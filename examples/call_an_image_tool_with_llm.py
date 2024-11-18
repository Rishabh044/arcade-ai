"""
This example shows how to call a tool that requires authorization with an LLM using the OpenAI Python client.
"""

import json
import os

from openai import OpenAI


def call_tool_with_openai(client: OpenAI) -> dict:
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Take a screenshot of https://www.cnn.com/  wait a couple seconds before screenshotting so that it has time to load",
            },
        ],
        model="gpt-4o-mini",
        user="eric@arcade-ai.com",
        tools=["Web.ScrapeUrl"],
        tool_choice="execute",
    )
    a = json.loads(response.choices[0].message.content)
    screenshot_url = a[next(iter(a.keys()))]["value"]["screenshot"]
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What are the biggest stories today? Also, describe any images in the screenshot.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": screenshot_url},
                    },
                ],
            },
        ],
        model="gpt-4o-mini",
        user="eric@arcade-ai.com",
        tool_choice="generate",
    )

    return response


if __name__ == "__main__":
    arcade_api_key = os.environ.get(
        "ARCADE_API_KEY"
    )  # If you forget your Arcade API key, it is stored at ~/.arcade/credentials.yaml on `arcade login`
    cloud_host = "https://api.arcade-ai.com" + "/v1"
    local_host = "http://localhost:9099" + "/v1"

    openai_client = OpenAI(
        api_key=arcade_api_key,
        base_url=local_host,  # Alternatively, use http://localhost:9099/v1 if you are running Arcade Engine locally
    )

    chat_result = call_tool_with_openai(openai_client)
    # If the tool call requires authorization, then wait for the user to authorize and then call the tool again
    if (
        chat_result.choices[0].tool_authorizations
        and chat_result.choices[0].tool_authorizations[0].get("status") == "pending"
    ):
        print(chat_result.choices[0].message.content)
        input("After you have authorized, press Enter to continue...")
        chat_result = call_tool_with_openai(openai_client)

    print(chat_result.choices[0].message.content)


# Choice(
#     finish_reason="tool_calls",
#     index=0,
#     logprobs=None,
#     message=ChatCompletionMessage(
#         content='{"call_RxEFKidLoIkw7i19l6VCFBns":{"value":{"metadata":{"HandheldFriendly":"True","description":"Arcade helps AI connect on the user\'s behalf to APIs, data, and systems like Gmail and Slack. Start building in minutes with our pre-built connectors.","generator":"Ghost 5.100","language":"en","og:description":"Arcade helps AI connect on the user\'s behalf to APIs, data, and systems like Gmail and Slack. Start building in minutes with our pre-built connectors.","og:image":"https://static.ghost.org/v5.0.0/images/publication-cover.jpg","og:image:height":"840","og:image:width":"1200","og:site_name":"Arcade Blog - Agent Auth and AI Tool-Calling","og:title":"Arcade Blog - Agent Auth and AI Tool-Calling","og:type":"website","og:url":"https://blog.arcade-ai.com/","ogDescription":"Arcade helps AI connect on the user\'s behalf to APIs, data, and systems like Gmail and Slack. Start building in minutes with our pre-built connectors.","ogImage":"https://static.ghost.org/v5.0.0/images/publication-cover.jpg","ogLocaleAlternate":[],"ogSiteName":"Arcade Blog - Agent Auth and AI Tool-Calling","ogTitle":"Arcade Blog - Agent Auth and AI Tool-Calling","ogUrl":"https://blog.arcade-ai.com/","referrer":"no-referrer-when-downgrade","sourceURL":"https://blog.arcade-ai.com/","statusCode":200,"title":"Arcade Blog - Agent Auth and AI Tool-Calling","twitter:card":"summary_large_image","twitter:description":"Arcade helps AI connect on the user\'s behalf to APIs, data, and systems like Gmail and Slack. Start building in minutes with our pre-built connectors.","twitter:image":"https://static.ghost.org/v5.0.0/images/publication-cover.jpg","twitter:site":"@TryArcade","twitter:title":"Arcade Blog - Agent Auth and AI Tool-Calling","twitter:url":"https://blog.arcade-ai.com/","url":"https://blog.arcade-ai.com/","viewport":"width=device-width, initial-scale=1"},"screenshot":"https://service.firecrawl.dev/storage/v1/object/public/media/screenshot-0a9829c3-7dcd-4f87-9229-5020079ecbba.png"}}}',
#         refusal=None,
#         role="assistant",
#         function_call=None,
#         tool_calls=[
#             ChatCompletionMessageToolCall(
#                 id="call_RxEFKidLoIkw7i19l6VCFBns",
#                 function=Function(
#                     arguments='{"formats":["screenshot"],"url":"https://blog.arcade-ai.com/"}',
#                     name="Web_ScrapeUrl",
#                 ),
#                 type="function",
#             )
#         ],
#     ),
#     tool_messages=None,
#     tool_authorizations=None,
# )
# {
#     "call_RxEFKidLoIkw7i19l6VCFBns": {
#         "value": {
#             "metadata": {
#                 "HandheldFriendly": "True",
#                 "description": "Arcade helps AI connect on the user's behalf to APIs, data, and systems like Gmail and Slack. Start building in minutes with our pre-built connectors.",
#                 "generator": "Ghost 5.100",
#                 "language": "en",
#                 "og:description": "Arcade helps AI connect on the user's behalf to APIs, data, and systems like Gmail and Slack. Start building in minutes with our pre-built connectors.",
#                 "og:image": "https://static.ghost.org/v5.0.0/images/publication-cover.jpg",
#                 "og:image:height": "840",
#                 "og:image:width": "1200",
#                 "og:site_name": "Arcade Blog - Agent Auth and AI Tool-Calling",
#                 "og:title": "Arcade Blog - Agent Auth and AI Tool-Calling",
#                 "og:type": "website",
#                 "og:url": "https://blog.arcade-ai.com/",
#                 "ogDescription": "Arcade helps AI connect on the user's behalf to APIs, data, and systems like Gmail and Slack. Start building in minutes with our pre-built connectors.",
#                 "ogImage": "https://static.ghost.org/v5.0.0/images/publication-cover.jpg",
#                 "ogLocaleAlternate": [],
#                 "ogSiteName": "Arcade Blog - Agent Auth and AI Tool-Calling",
#                 "ogTitle": "Arcade Blog - Agent Auth and AI Tool-Calling",
#                 "ogUrl": "https://blog.arcade-ai.com/",
#                 "referrer": "no-referrer-when-downgrade",
#                 "sourceURL": "https://blog.arcade-ai.com/",
#                 "statusCode": 200,
#                 "title": "Arcade Blog - Agent Auth and AI Tool-Calling",
#                 "twitter:card": "summary_large_image",
#                 "twitter:description": "Arcade helps AI connect on the user's behalf to APIs, data, and systems like Gmail and Slack. Start building in minutes with our pre-built connectors.",
#                 "twitter:image": "https://static.ghost.org/v5.0.0/images/publication-cover.jpg",
#                 "twitter:site": "@TryArcade",
#                 "twitter:title": "Arcade Blog - Agent Auth and AI Tool-Calling",
#                 "twitter:url": "https://blog.arcade-ai.com/",
#                 "url": "https://blog.arcade-ai.com/",
#                 "viewport": "width=device-width, initial-scale=1",
#             },
#             "screenshot": "https://service.firecrawl.dev/storage/v1/object/public/media/screenshot-0a9829c3-7dcd-4f87-9229-5020079ecbba.png",
#         }
#     }
# }
