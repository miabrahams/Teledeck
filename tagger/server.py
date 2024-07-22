import json
import time
from io import BytesIO
from typing import List
import os

import torch
from fastapi import FastAPI, File, UploadFile
from PIL import Image
from pydantic import BaseModel, model_serializer, Field
from typing import Dict
from decimal import Decimal
from torchvision.transforms import transforms

TAGGER_PORT = 8081
DEBUG = os.getenv("env", "production") == "development"


class PredictionResult(BaseModel):
    tag: str
    probability: Decimal = Field(max_digits=3, decimal_places=2)

    @model_serializer
    def ser_model(self) -> Dict[str, Decimal]:
        return {self.tag: self.probability}


class Tagger:
    model: torch.nn.Module = None
    allowed_tags: List[str] = None
    transform: transforms.Compose = None


    def __init__(self):
        print("Loading model.")
        self.model = torch.load("model/model.pth").to("cuda")
        self.model.eval()

        with open("model/tags_8041.json", "r") as file:
            tags = json.load(file)
        allowed_tags = sorted(tags)
        allowed_tags.insert(0, "placeholder0")
        allowed_tags.append("placeholder1")
        allowed_tags.append("explicit")
        allowed_tags.append("questionable")
        allowed_tags.append("safe")
        print(f"Allowed tags: {len(allowed_tags)}")
        self.allowed_tags = allowed_tags

        """
        with open("model/tags_extra.json", "r") as file:
            extra_tags = json.load(file)
            for position, tag in extra_tags:
                if position == -1:
                    allowed_tags.append(tag)
                else:
                    allowed_tags.insert(position, tag)
        """

        # Define transform
        self.transform = transforms.Compose(
            [
                transforms.Resize((448, 448)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.48145466, 0.4578275, 0.40821073], std=[0.26862954, 0.26130258, 0.27577711]),
            ]
        )

    async def load_model():
        pass


    def run_inference(self, img: Image):
        start = time.time()

        tensor = self.transform(img).unsqueeze(0).to("cuda")
        with torch.no_grad():
            out = self.model(tensor)
        probabilities = torch.nn.functional.sigmoid(out[0])
        indices = torch.where(probabilities > 0.3)[0]
        results = [PredictionResult(tag=self.allowed_tags[idx], probability=f"{probabilities[idx].item():0.2f}") for idx in indices]
        end = time.time()
        print(f"Executed in {end - start} seconds")

        return results



TAGGER = Tagger()

if DEBUG:
    image_path = "../static/media/photo_2024-07-20_15-31-52.jpg"
    img = Image.open(image_path).convert('RGB')
    results = TAGGER.run_inference(img)
    for (tag, prob) in results:
        print(f"{tag}: {prob}")


app = FastAPI()

@app.post("/predict/file", response_model=List[PredictionResult])
async def predict(file: UploadFile = File(...), cutoff: float = 0.3):
    # Process uploaded image
    contents = await file.read()
    img = Image.open(BytesIO(contents)).convert("RGB")

    results = TAGGER.run_inference(img)
    results = results.where(lambda x: x.probability > cutoff)

    return results


@app.post("/predict/url", response_model=List[PredictionResult])
async def predict_url(image_path: str, cutoff: float = 0.3):
    # Process image from URL
    print(f"Processing image from URL: {image_path}")
    img = Image.open(image_path).convert("RGB")

    results = TAGGER.run_inference(img)

    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=TAGGER_PORT)
