
from openai import AsyncOpenAI

api_key = "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"

client = AsyncOpenAI(api_key=api_key, base_url="http://localhost:8000/v1")

# Using 'async' with 'await' for proper asynchronous call
async def get_chat_response():
    response = await client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a friendly assistant named Jarvis. Help with whatever you can."},
            {"role": "user", "content": "Hey there! What's your name?"},
        ],
        model="gpt-4-turbo",
        tools=["ReadEmail"],
        tool_choice="execute",
        stream=False
    )
    return response

async def print_chat_responses():
    response = await get_chat_response()
    print(response.choices[0].message)


import asyncio
asyncio.run(print_chat_responses())