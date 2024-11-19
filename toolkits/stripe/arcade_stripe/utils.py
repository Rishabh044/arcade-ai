import os
from typing import Optional, get_args

from stripe_agent_toolkit.api import StripeAPI
from stripe_agent_toolkit.functions import *  # noqa: F403
from stripe_agent_toolkit.prompts import *  # noqa: F403
from stripe_agent_toolkit.schema import *  # noqa: F403
from stripe_agent_toolkit.tools import tools


def get_secret(name: str, default: Optional[str] = None) -> str:
    secret = os.getenv(name)
    if secret is None and default is not None:
        return default
    return secret


def get_stripe_api() -> StripeAPI:
    api_key = get_secret("STRIPE_SECRET_KEY")
    return StripeAPI(secret_key=api_key)


def __generate_stripe_tools_file():
    """
    FOR DEVELOPMENT PURPOSES ONLY.

    Generate the stripe tools file.
    Execute this function to generate the 'Arcade AI Stripe Toolkit' based on the 'Stripe Agent Toolkit'.
    """
    output_file = "tools/stripe.py"
    with open(output_file, "w") as f:
        # Write header imports and utility functions
        f.write("""import os
from typing import Annotated, Optional

from stripe_agent_toolkit.api import StripeAPI

from arcade.sdk import tool


def get_secret(name: str, default: Optional[str] = None) -> str:
    secret = os.getenv(name)
    if secret is None and default is not None:
        return default
    return secret

def get_stripe_api() -> StripeAPI:
    api_key = get_secret("STRIPE_SECRET_KEY")
    return StripeAPI(secret_key=api_key)

""")

        # Generate and write each tool function
        for tool_info in tools:
            method_name = tool_info["method"]
            method = globals().get(method_name)
            if not method:
                print(f"Method {method_name} not found.")
                continue

            args_schema = tool_info["args_schema"]
            description = tool_info["description"].strip()

            # Extract argument names and types from the schema
            arg_names = list(args_schema.__annotations__.keys())
            arg_types = [args_schema.__annotations__[field] for field in arg_names]

            # Generate the tool function code
            arcade_tool_code = f"""
@tool
def {method_name}(
    {
                ", ".join([
                    f'{name}: Annotated[Optional[{get_args(arg_type)[0].__name__}], "{args_schema.__fields__[name].description}"] = None'
                    if args_schema.__fields__[name].default is None
                    else f'{name}: Annotated[{arg_type.__name__}, "{args_schema.__fields__[name].description}"]'
                    for name, arg_type in zip(arg_names, arg_types)
                ])
            }
) -> Annotated[str, "{description.splitlines()[0]}"]:
    \"\"\"{description.splitlines()[0]}
    \"\"\"
    stripe_api = get_stripe_api()
    return stripe_api.run({method_name}.__name__, {
                ", ".join([f"{name}={name}" for name in arg_names])
            })
"""
            f.write(arcade_tool_code)
            f.write("\n")
