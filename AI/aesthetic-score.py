import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from transformers import CLIPProcessor, CLIPModel, BatchEncoding, pipeline, Pipeline
import gradio as gr
from typing import Dict, Any

from aesthetic_predictor_v2_5 import convert_v2_5_from_siglip, AestheticPredictorV2_5Model

import json
import time
from io import BytesIO
from typing import List
import os
import traceback

import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
from pydantic import BaseModel
from torchvision.transforms import transforms # type: ignore
from dotenv import load_dotenv
from typing import Any


# MLP class remains mostly the same, but inherits from nn.Module instead of pl.LightningModule
class MLP(nn.Module):
    def __init__(self, input_size: int, xcol: str='emb', ycol: str='avg_rating'):
        super().__init__()
        self.input_size = input_size
        self.xcol = xcol
        self.ycol = ycol
        self.layers = nn.Sequential(
            nn.Linear(self.input_size, 1024),
            #nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(1024, 128),
            #nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            #nn.ReLU(),
            nn.Dropout(0.1),

            nn.Linear(64, 16),
            #nn.ReLU(),

            nn.Linear(16, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)

    def training_step(self, batch: torch.Tensor, batch_idx: int):
        x = batch[self.xcol]
        y = batch[self.ycol].reshape(-1, 1)
        x_hat = self.layers(x)
        loss = F.mse_loss(x_hat, y)
        return loss

    def validation_step(self, batch: torch.Tensor, batch_idx: int):
        x = batch[self.xcol]
        y = batch[self.ycol].reshape(-1, 1)
        x_hat = self.layers(x)
        loss = F.mse_loss(x_hat, y)
        return loss

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer

def normalized(a: np.ndarray[Any, Any], axis: int=-1, order: int=2) -> np.ndarray[Any, Any]:

    l2 = np.atleast_1d(np.linalg.norm(a, order, axis))
    l2[l2 == 0] = 1
    return a / np.expand_dims(l2, axis)


class AestheticProcessor():
    def __init__(self, device: int | str):

        model = MLP(768)

        device = "cuda" if torch.cuda.is_available() else "cpu"

        s: Dict[str, Any] = torch.load("sac+logos+ava1-l14-linearMSE.pth", map_location=device)

        model.load_state_dict(s)
        model.to(device)
        model.eval()

        # Load CLIP model and processor from Hugging Face
        clip_model: CLIPModel = CLIPModel.from_pretrained("openai/clip-vit-large-patch14").to(device)
        clip_processor: CLIPProcessor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
        self.classifier = model
        self.clip_model = clip_model
        self.clip_processor = clip_processor
        self.device = device

    def predict(self, image: Image.Image):
        # Process image using CLIP processor
        image_input: BatchEncoding = self.clip_processor(images=image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            # Get image features from CLIP model
            image_features = self.clip_model.get_image_features(**image_input)

            if self.device == 'cuda':
                im_emb_arr = normalized(image_features.detach().cpu().numpy())
                im_emb: torch.Tensor = torch.from_numpy(im_emb_arr).to(self.device).type(torch.cuda.FloatTensor)
            else:
                im_emb_arr = normalized(image_features.detach().numpy())
                im_emb: torch.Tensor = torch.from_numpy(im_emb_arr).to(self.device).type(torch.FloatTensor)
            prediction = self.classifier(im_emb)
        score = prediction.item()

        return {'score': score}


class AestheticShadowProcessor():
    def __init__(self, device: int | str):
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        self.pipe = pipeline("image-classification", model="./aesthetic-shadow-v2/", device=device)

    def predict(self, image: Image.Image):
        result = self.pipe(images=[image])
        print("Result is: ", result[0])

        prediction_single = result[0]
        ''' Format:
        [{'label': 'hq', 'score': 0.7508018612861633},
         {'label': 'lq', 'score': 0.2491981089115148}]
        '''

        hq: float = prediction_single[0]['score']
        lq: float = prediction_single[1]['score']
        predict_str = f"Prediction: {hq:0.2f}% High Quality; {lq:0.2f} Low Quality"
        print(predict_str)
        return {'High quality: ': format(hq, '.2f'), 'Low quality: ': format(lq, '.2f')}


class AP25Processor():
    def __init__(self, device: int | str):
        # load model and preprocessor
        print("Loading model")
        model, preprocessor = convert_v2_5_from_siglip(
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        )
        model: AestheticPredictorV2_5Model = model.to(torch.bfloat16).cuda()

        self.model = model
        self.preprocessor = preprocessor

    def predict(self, image: Image.Image):
        # load image to evaluate
        print("Loading image")
        image = image.convert("RGB")

        # preprocess image
        pixel_values = (
            self.preprocessor(images=image, return_tensors="pt")
            .pixel_values.to(torch.bfloat16)
            .cuda()
        )
        print("Predicting")

        # predict aesthetic score
        with torch.inference_mode():
            score: np.ndarray = self.model(pixel_values).logits.squeeze().float().cpu().numpy()

        # print result
        return {'score': f"{score:.2f}"}


def demo_server():
    # predictor = AestheticScorePredictor(device)
    # predictor = AestheticShadowProcessor(device)
    predictor = AP25Processor(device)
    with gr.Blocks() as demo:
        with gr.Row():
            with gr.Column():
                image_input = gr.Image(type='pil', label='Input image')
                submit_button = gr.Button('Submit')
            json_output = gr.JSON(label='Output')
        submit_button.click(predictor.predict, inputs=image_input, outputs=json_output)
        gr.Examples(examples=examples, inputs=image_input)
        gr.HTML(article)
    demo.launch()


class ScoreResult(BaseModel):
    score: float


app = FastAPI()
# Todo: create model loader dependency
print('\tinit models')
predictor = AP25Processor("cuda")

@app.post("/score/url", response_model=ScoreResult)
async def predict_url(image_path: str):
    print(f"Processing image from URL: {image_path}")
    try:
        img = Image.open(image_path)
        results = predictor.predict(img)
    except Exception as e:
        print("Error processing image")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

    return results

SCORE_PORT = int(os.getenv("SCORE_PORT", 8081))

if __name__ == '__main__':

    device = "cuda" if torch.cuda.is_available() else "cpu"

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SCORE_PORT)