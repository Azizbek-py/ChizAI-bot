import os
import io
import requests
from huggingface_hub import InferenceClient
from settings import *

hf = InferenceClient(api_key=HF_TOKEN)
HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"


async def photo_generation(prompt: str) -> str:
    img = hf.text_to_image(prompt, model=HF_MODEL)

    bio = io.BytesIO()
    bio.name = "gen.png"
    img.save(bio, format="PNG")
    bio.seek(0)

    r = requests.post(
        "https://uguu.se/upload",
        files={"files[]": ("gen.png", bio, "image/png")},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    return data["files"][0]["url"]