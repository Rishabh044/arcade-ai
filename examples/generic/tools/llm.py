

from typing import (
    IO,
    Union,
    List,
    Dict,
    Optional,
    Any,
    Type,
)
import io
import requests
from os import PathLike
import base64

from arcade.sdk import Param, tool, get_secret
from typing import List
import pandas as pd
import openai



@tool
async def summarize(
    text: Param(str, "Text to summarize"),
    system_prompt: Param(str, "System prompt to use") = "Summarize the following text",
    max_tokens: Param(int, "Maximum number of tokens to generate") = 1000,
    ) -> Param(str, "Summarized text"):
    """Summarize a piece of text using OpenAI Language models."""

    api_key = get_secret("openai_api_key", None)
    model = get_secret("openai_model_summarize", "gpt-4-turbo")
    # Call the OpenAI model with the tools and messages

    if isinstance(text, list):
        text = "\n".join(text)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]

    client = openai.AsyncClient(api_key=api_key)
    completion = await openai.chat.completions.create(
        model=model,
        messages=messages,
    )
    summary = completion.choices[0].message.content
    return summary



@tool
async def respond(
    context: Param(str, "context of the conversation"),
    system_prompt: Param(str, "System prompt to use") = "Given the following context, respond with a message in a friendly and helpful manner. Be informal and use a casual tone.",
    max_tokens: Param(int, "Maximum number of tokens to generate") = 1000,
    ) -> Param(str, "The response to the context provided"):
    """Respond to a user given context using OpenAI Language models"""

    api_key = get_secret("openai_api_key", None)
    model = get_secret("openai_model_summarize", "gpt-4-turbo")
    # Call the OpenAI model with the tools and messages

    if isinstance(context, list):
        context = "\n".join(context)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context},
    ]

    client = openai.AsyncClient(api_key=api_key)
    completion = await openai.chat.completions.create(
        model=model,
        messages=messages,
    )
    response = completion.choices[0].message.content
    return response



