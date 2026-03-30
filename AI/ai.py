import os
import io
import base64
import requests

from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from groq import Groq
from settings import GROQ_TOKEN, HF_TOKEN

load_dotenv()

HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"


def generate_photo(prompt: str) -> str:
    client = InferenceClient(
        provider="nscale",
        api_key=HF_TOKEN,
    )

    img = client.text_to_image(
        prompt=prompt,
        model=HF_MODEL,
    )

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


def describe_photo(filename: str, prompt: str) -> dict:
    with open(filename, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "Sen rasmni boshqa Rasm generatsiya qiladigan API uchun tahlil qilib beradigan agentsan. Rasm xar bitta pikseligacha tahlil qilinishi kerak va mukammal prompt ko'rinishida bo'lishi kerak. Qo'shimcha prompt va rasmni to'g'ri bir-birga qo'shib prompt hozili qilib qaytar chunki rasmlarda insonlarning yuzi ham qatnashadi hattoki. SHuning uchun batafsil va tushunarli yoz"
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                },
            ],
        }
    ],
    model="meta-llama/llama-4-scout-17b-16e-instruct",
)

    message = completion.choices[0].message

    return {
        "text": message.content,
        "model": completion.model,
        "usage": completion.usage,
        "raw": completion
    }