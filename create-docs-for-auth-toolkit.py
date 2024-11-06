import os

from arcadepy import Arcade

from arcade.core.toolkit import Toolkit


def snake_to_camel(snake_str):
    return "".join(word.capitalize() for word in snake_str.split("_"))


toolkits = Toolkit.find_all_arcade_toolkits()
toolkits_to_files = {}
for toolkit in toolkits:
    files_to_tools = {}
    for filepath, tools in toolkit.tools.items():
        if not len(tools):
            continue
        files_to_tools[filepath.split(".")[-1]] = []
        for tool in tools:
            tool_id = toolkit.name.capitalize() + "." + snake_to_camel(tool)
            files_to_tools[filepath.split(".")[-1]].append(tool_id)
    toolkits_to_files[toolkit.name] = files_to_tools

file_path_to_tools = {}
for tk, file_to_tools in toolkits_to_files.items():
    if not len(file_to_tools):
        continue
    if len(file_to_tools) == 1:
        path = "integrations/toolkits/" + tk + ".mdx"
        file_path_to_tools[path] = next(iter(file_to_tools.values()))
    else:
        for file, tools in file_to_tools.items():
            path = "integrations/toolkits/" + tk.capitalize() + "/" + file + ".mdx"
            file_path_to_tools[path] = tools

for path, tools in file_path_to_tools.items():
    print(path)
    for tool in tools:
        print(f"    {tool}")

client = Arcade(base_url="https://api.arcade-ai.com")

# Retrieve the tools for the specified toolkit
toolkit_name = "slack"
tools = client.tools.list(toolkit=toolkit_name)

# Start building the content for the .mdx file
mdx_content = f"""# {toolkit_name.capitalize()}

import ToolInfo from "@/components/ToolInfo";
import Badges from "@/components/Badges";
import TabbedCodeBlock from "@/components/TabbedCodeBlock";
import TableOfContents from "@/components/TableOfContents";

<ToolInfo
  description="Enable agents to interact with {toolkit_name.capitalize()}."
  author="Arcade AI"
  codeLink="https://github.com/ArcadeAI/arcade-ai/tree/main/toolkits/{toolkit_name}"
  authType="OAuth2"
  versions={{["0.1.0"]}}
/>

<Badges repo="arcadeai/arcade_{toolkit_name}" />

The Arcade AI {toolkit_name.capitalize()} toolkit provides a pre-built set of tools for interacting with {toolkit_name.capitalize()}. These tools make it easy to build agents and AI apps that can:
"""

# Add a brief description of each tool
for tool in tools.items:
    mdx_content += f"\n- {tool.description}"

mdx_content += f"\n\n## Install\n\n```bash\npip install arcade_{toolkit_name}\n```\n\n"

# Add the available tools section
mdx_content += (
    '## Available Tools\n\n<TableOfContents\n  headers={["Tool Name", "Description"]}\n  data={[\n'
)

for tool in tools.items:
    mdx_content += f'    ["{tool.name}", "{tool.description}"],\n'

mdx_content += "  ]}\n/>\n\n"

mdx_content += f"<Tip>\n  If you need to perform an action that's not listed here, you can [get in touch\n  with us](mailto:contact@arcade-ai.com) to request a new tool, or [create your\n  own tools](/home/build-tools/create-a-toolkit) with the [{toolkit_name.capitalize()} auth provider](/integrations/auth/{toolkit_name}#using-{toolkit_name}-auth-in-custom-tools).\n</Tip>\n"

# Add detailed sections for each tool
for tool in tools.items:
    camel_case_tool_name = tool.fully_qualified_name.split(".")[1].split("@")[0]
    snake_case_tool_name = ""
    for i, char in enumerate(camel_case_tool_name):
        if char.isupper() and i != 0:
            snake_case_tool_name += "_" + char.lower()
        else:
            snake_case_tool_name += char.lower()
    mdx_content += f'\n## {tool.name}\n\n<br />\n<TabbedCodeBlock\n  tabs={{[\n    {{\n      label: "Call the Tool with User Authorization",\n      content: {{\n        Python: [\n          "/examples/integrations/toolkits/{toolkit_name}/{snake_case_tool_name}_example_call_tool.py",\n        ],\n        JavaScript: ["Coming Soon"],\n      }},\n    }},\n    {{\n      label: "Execute the Tool with OpenAI",\n      content: {{\n        Python: [\n          "/examples/integrations/toolkits/{toolkit_name}/{snake_case_tool_name}_example_llm_oai.py",\n        ],\n        JavaScript: ["Coming Soon"],\n      }},\n    }},\n  ]}}\n/>\n\n{tool.description}\n\n'

    # Add parameters if available
    if tool.inputs.parameters:
        mdx_content += "\n**Parameters**\n\n"
        for param in tool.inputs.parameters:
            mdx_content += f"- **`{param.name}`** _({param.value_schema.val_type}, {'required' if param.required else 'optional'})_ {param.description}\n"
        mdx_content += "\n\n"
    mdx_content += "---\n"

# Add the Auth section for the toolkit
mdx_content += f"""
## Auth

The Arcade AI {toolkit_name.capitalize()} toolkit uses the [Slack auth provider](/integrations/auth/slack) to connect to users' Slack accounts.

With the hosted Arcade AI Engine, there's nothing to configure. Your users will see `Arcade AI (demo)` as the name of the application that's requesting permission.

<Warning type="warning" emoji="⚠️">
  The hosted Arcade Engine is intended for demo and testing purposes only, not
  for production use. To use Arcade AI and Slack in production, you must use a
  self-hosted instance of the Arcade Engine.
</Warning>

With a self-hosted installation of Arcade AI, you need to [configure the Slack auth provider](/integrations/auth/slack#configuring-slack-auth) with your own Slack app credentials.
"""

# Write the content to the .mdx file
file_name = f"integrations/toolkits/{toolkit_name}.mdx"
os.makedirs(os.path.dirname(file_name), exist_ok=True)
with open(file_name, "w") as file:
    file.write(mdx_content)

print(f"{file_name} file has been created.")
