from typing import Annotated, Optional

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


def test_create_tool_with_input_dict_param():
    @tool
    def sample_function(param1: dict):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.input == ToolInput(
        parameters=[
            InputParameter(
                name="param1",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(type="json", enum=None),
            )
        ]
    )


# def test_create_tool_with_input_string_enum_param():
#     @tool
#     def sample_function(param1: str):
#         pass

#     tool_def = ToolCatalog.create_tool_definition(
#         sample_function, "1.0", input_parameters=[
#             InputParameter(
#                 name="param1",
#                 description="No description provided.",
#                 inferrable=True,
#                 required=True,
#                 value_schema=ValueSchema(type="string", enum=["value1", "value2"]),
#             )
#         ]
#     )

#     assert tool_def.input.parameters[0].value_schema.enum == ["value1", "value2"]


def test_create_tool_with_unsupported_input_param():
    @tool
    def sample_function(param1: complex):
        pass

    try:
        ToolCatalog.create_tool_definition(sample_function, "1.0")
    except TypeError as e:
        assert str(e) == "Unsupported parameter type: <class 'complex'>"


def test_create_tool_with_annotated_param():
    from typing import Annotated

    @tool
    def sample_function(param1: Annotated[str, "description"]):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.input.parameters[0].description == "description"


def test_create_tool_with_no_return():
    @tool
    def sample_function():
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.output.available_modes == ["null"]
    assert not tool_def.output.value


def test_create_tool_with_output_value():
    @tool
    def sample_function() -> str:
        return "output"

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.output.value.value_schema == ValueSchema(type="string", enum=None)
    assert "value" in tool_def.output.available_modes


def test_create_tool_with_optional_output_value():
    @tool
    def sample_function() -> Optional[str]:
        return "output"

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.output.value.value_schema == ValueSchema(type="string", enum=None)
    assert "null" in tool_def.output.available_modes


def test_create_tool_with_annotated_output_value():
    @tool
    def sample_function() -> Annotated[str, "output description"]:
        return "output"

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.output.value.value_schema == ValueSchema(type="string", enum=None)
    assert tool_def.output.value.description == "output description"
    assert "value" in tool_def.output.available_modes
