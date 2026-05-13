import os
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
from config import MODEL
from core.logging_config import logger

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate(messages, tools=None):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        temperature=0.7
    )
    return response.choices[0].message

def generate_with_tools(messages, tools=None):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        temperature=0.3
    )
    return response.choices[0].message

async def agenerate(messages, tools=None):
    response = await async_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        temperature=0.7
    )
    logger.debug(f"LLM call completed, tokens used: {response.usage}")
    return response.choices[0].message

async def agenerate_with_tools(messages, tools=None):
    response = await async_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        temperature=0.3
    )
    logger.debug(f"LLM tool call completed, tokens used: {response.usage}")
    return response.choices[0].message