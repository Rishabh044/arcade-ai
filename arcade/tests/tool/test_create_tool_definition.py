from arcade.sdk.models import InputParameter, OAuth2AuthorizationRequirement, ToolInput, ValueSchema
from arcade.sdk.tool import tool
from arcade.tool.catalog import ToolCatalog


def test_create_tool_def_with_version():
    @tool
    def sample_function():
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.version == "1.0"


def test_create_tool_def_with_default_function_name():
    @tool
    def sample_function():
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.name == "sample_function"  # Defaults to literal function name


def test_create_tool_def_with_specified_name():
    @tool(name="custom_name")
    def sample_function():
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.name == "custom_name"  # Uses specified name


def test_create_tool_def_with_no_description():
    @tool
    def sample_function():
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.description == "No description provided."  # Default


def test_create_tool_def_with_specified_description():
    @tool(description="Custom description")
    def sample_function():
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.description == "Custom description"  # Uses specified description


def test_create_tool_def_with_docstring_description():
    @tool
    def sample_function():
        """Docstring description"""
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.description == "Docstring description"  # Uses docstring description


def test_create_tool_def_with_oauth2_auth_requirement():
    @tool(
        requires_auth=OAuth2AuthorizationRequirement(
            url="https://example.com/oauth2/auth", scopes=["scope1", "scope2"]
        )
    )
    def sample_function():
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.requirements.authorization == OAuth2AuthorizationRequirement(
        url="https://example.com/oauth2/auth", scopes=["scope1", "scope2"]
    )


def test_create_tool_with_input_param():
    @tool
    def sample_function(param1: str):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.input == ToolInput(
        parameters=[
            InputParameter(
                name="param1",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(type="string", enum=None),
            )
        ]
    )


def test_create_tool_with_input_param_with_default():
    @tool
    def sample_function(param1: str = "default"):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.input == ToolInput(
        parameters=[
            InputParameter(
                name="param1",
                description="No description provided.",
                inferrable=True,
                required=False,  # Because default is provided
                value_schema=ValueSchema(type="string", enum=None),
            )
        ]
    )


def test_create_tool_with_optional_input_param():
    from typing import Optional

    @tool
    def sample_function(param1: Optional[str]):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.input == ToolInput(
        parameters=[
            InputParameter(
                name="param1",
                description="No description provided.",
                inferrable=True,
                required=False,  # Because of Optional[str]
                value_schema=ValueSchema(type="string", enum=None),
            )
        ]
    )


def test_create_tool_with_multiple_input_params():
    @tool
    def sample_function(param1: str, param2: int, param3: float, param4: bool):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.input == ToolInput(
        parameters=[
            InputParameter(
                name="param1",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(type="string", enum=None),
            ),
            InputParameter(
                name="param2",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(type="integer", enum=None),
            ),
            InputParameter(
                name="param3",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(type="decimal", enum=None),
            ),
            InputParameter(
                name="param4",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(type="boolean", enum=None),
            ),
        ]
    )


# TODO: Test with dict (json) parameter
# TODO: Test with string parameter with enum values
# TODO: Test with unsupported parameter (raises TypeError)
# TODO: Test with Annotated[str, ...] parameter

# TODO: Test with output (return) value -> TO.value.value_schema is set
# TODO: Test with Optional[] output value -> ToolOutput.available_modes includes `null`
# TODO: Test with Annotated[str, ...] output value -> TO.value.description is set
