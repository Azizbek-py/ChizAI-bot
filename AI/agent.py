import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.agents import create_agent, AgentState
from langchain.messages import HumanMessage, ToolMessage
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command

from AI.ai import generate_photo, describe_photo

load_dotenv()


class State(AgentState):
    filename: str
    image_url: str
    image_to_text: str
    image_url_message: str


@tool
def photo_generation(prompt: str) -> Command:
    """generate image from prompt"""
    url = generate_photo(prompt)
    return Command(
        update={
            "image_url": url,
            "image_url_message": "Rasm yaratildi"
        }
    )


@tool
def describe_image(runtime: ToolRuntime, filename: str, prompt: str) -> Command:
    """describe image"""
    try:
        text = describe_photo(filename, prompt)

        return Command(
            update={
                "filename": filename,
                "image_to_text": text,
                "messages": [
                    ToolMessage(
                        content=text,
                        tool_call_id=runtime.tool_call_id
                    )
                ],
            }
        )
    except Exception as e:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"Xatolik: {str(e)}",
                        tool_call_id=runtime.tool_call_id
                    )
                ]
            }
        )


def run_agent(prompt: str, filename: str = "") -> dict:
    model = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.environ.get("GROQ_API_KEY"),
    )

    agent = create_agent(
        model=model,
        tools=[photo_generation, describe_image],
        state_schema=State,
        system_prompt="Siz AI agent siz va faqat rasm yaratish yoki rasmni tavsiflash bilan shug‘ullanasiz. Har doim o‘zbek tilida javob bering."
    )

    response = agent.invoke({
        "messages": [HumanMessage(content=prompt)],
        "filename": filename
    })

    return {
        "url": response.get("image_url"),
        "message": response["messages"][-1].content if response.get("messages") else ""
    }