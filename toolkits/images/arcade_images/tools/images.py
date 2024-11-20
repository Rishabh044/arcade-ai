from typing import Annotated

from openai import OpenAI

from arcade.sdk import tool
from toolkits.images.arcade_images.utils import get_secret


@tool
def generate_image(
    prompt: Annotated[str, "The prompt for the image to generate"],
    model: Annotated[str, "The model to use to generate the image"] = "dall-e-2",
) -> Annotated[list[str], "The URL(s) of the generated image(s)"]:
    """Generate an image based on a prompt"""
    api_key = get_secret("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    response = client.images.generate(
        prompt=prompt,
        n=1,
        size="256x256",
    )

    images = [image.url for image in response.data]
    return images
