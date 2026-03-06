import os
import io
import base64
import requests
from huggingface_hub import InferenceClient
from settings import *
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent, AgentState
from langchain.messages import HumanMessage, ToolMessage
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command

from groq import Groq

load_dotenv()

HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

class State(AgentState):
    filename: str
    image_url: str
    image_to_text: str
    image_url_message: str


@tool
def describe_image(runtime: ToolRuntime, filename: str, prompt: str) -> str | Command:
    try:
        # Faylni base64 formatiga o'girish
        with open(filename, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Groq API mijozini yaratish
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

        # API orqali tasvirni tahlil qilish
        completion = client.chat.completions.create(
            messages=[
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

        # Javobni qaytarish
        message = completion.choices[0].message
        return Command(
            update={
                "filename": filename,
                "image_to_text": message,
                "messages": [ToolMessage(content=message, tool_call_id=runtime.tool_call_id)],
            }
        )
    except Exception as e:

        # Xatolik yuz berganda xabarni qaytarish
        return f"Xatolik: {e}"

@tool
def photo_generation(prompt: str) -> str:
    
    client = InferenceClient(
        provider="nscale",
        api_key=os.environ["HF_TOKEN"],
    )

    # output is a PIL.Image object
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
    return Command(
            update={
                "image_url": data["files"][0]["url"],
                "image_url_message": f"Siz tasvirlab bergan rasm yaratildi"
            }
        )

async def user_input(filename: str = "", prompt: str = "") -> str:

    user_messages = """User messages were taken from DB and converted to list"""
    agent_messages = """Agent messages were taken from DB converted to list"""

    model = init_chat_model(model="gemini-2.5-flash", model_provider="google_genai")
    agent = create_agent(
        model=model,
        tools=[describe_image, photo_generation],
        state_schema=State,
        system_prompt="""You are helpfull AI Agent and you must generate and describe image. 
                        I must not answer ohter question. Give an answer in Uzbek Language."""
    )
    
    response = agent.invoke({
        "messages": [HumanMessage(content=prompt)],
        "filename": filename
    })

    data_to_return = {
        "url": response.get("image_url"),
        "message": response["messages"].content
    }
    return data_to_return

