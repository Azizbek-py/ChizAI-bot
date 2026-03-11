import io
import os
import requests
from huggingface_hub import InferenceClient
from settings import *

hf = InferenceClient(
    provider="fal-ai",
    api_key=HF_TOKEN
)

HF_MODEL = "ZB-Tech/Text-to-Image"

# async def photo_generation(prompt: str) -> str:
#     img = hf.text_to_image(prompt, model=HF_MODEL)

#     bio = io.BytesIO()
#     bio.name = "gen.png"
#     img.save(bio, format="PNG")
#     bio.seek(0)

#     r = requests.post(
#         "https://uguu.se/upload",
#         files={"files[]": ("gen.png", bio, "image/png")},
#         timeout=60,
#     )
#     r.raise_for_status()
#     return r.json()["files"][0]["url"]


async def photo_generation(prompt):
    return "AgACAgQAAxkBAAFESZJpru_CbJc1LPz0gKDhOQ3w6SkJdQACPA1rGwg2fVH73btp5iDaFwEAAwIAA3kAAzoE"