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

load_dotenv()

TAGGER_PORT = int(os.getenv("TAGGER_PORT", 8081))
DEBUG = os.getenv("env", "production") == "development"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model")

class PredictionResult(BaseModel):
    tag: str
    prob: float


class Tagger:
    model: torch.nn.Module
    allowed_tags: List[str]
    transform: transforms.Compose


    def __init__(self):
        print("Loading model.")
        loadedModel: Any = torch.load(os.path.join(MODEL_PATH, "model.pth")).to("cuda") # type: ignore
        if not isinstance(loadedModel, torch.nn.Module):
            raise ValueError("Model failed to load.")
        self.model = loadedModel
        self.model.eval()

        with open(os.path.join(MODEL_PATH, "tags_8041.json"), "r") as file:
            tags = json.load(file)
        allowed_tags = sorted(tags)
        with open(os.path.join(MODEL_PATH, "tags_extra.json"), "r") as file:
            extra_tags = json.load(file)
            for position, tag in extra_tags:
                if position == -1:
                    allowed_tags.append(tag)
                else:
                    allowed_tags.insert(position, tag)

        self.allowed_tags = allowed_tags


        # Define transform
        self.transform = transforms.Compose(
            [
                transforms.Resize((448, 448)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.48145466, 0.4578275, 0.40821073], std=[0.26862954, 0.26130258, 0.27577711]),
            ]
        )



    def run_inference(self, img: Image.Image, cutoff: float = 0.3):
        start = time.time()

        tensor = self.transform(img).unsqueeze(0).to("cuda") # type: ignore
        with torch.no_grad():
            out = self.model(tensor)
        probabilities = torch.nn.functional.sigmoid(out[0])
        indices = torch.where(probabilities > cutoff)[0]
        results = [PredictionResult(tag=self.allowed_tags[idx], prob=probabilities[idx].item()) for idx in indices]
        results.sort(key=lambda x: x.prob, reverse=True)
        end = time.time()
        print(f"Executed in {end - start} seconds")

        return results



TAGGER = Tagger()


app = FastAPI()

@app.post("/predict/file", response_model=List[PredictionResult])
async def predict(file: UploadFile = File(...), cutoff: float = 0.3):
    # Process uploaded image
    try:
        contents = await file.read()
        img = Image.open(BytesIO(contents)).convert("RGB")
        results = TAGGER.run_inference(img, cutoff)
    except Exception as e:
        print("Error processing image")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

    return results


@app.post("/predict/url", response_model=List[PredictionResult])
async def predict_url(image_path: str, cutoff: float = 0.3):
    # Process image from URL
	# TODO: Make these paths independent of where the test is run
    print(f"Image path: {image_path}  -  cutoff: {cutoff}")
    print(f"Processing image from URL: {image_path}")
    try:
        img = Image.open(image_path).convert("RGB")
        results = TAGGER.run_inference(img, cutoff)
    except Exception as e:
        print("Error processing image")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=TAGGER_PORT)
