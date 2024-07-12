from typing import Annotated, Literal, Optional

import pytest

from arcade.sdk.annotations import Inferrable
from arcade.sdk.schemas import (
    InputParameter,
    OAuth2AuthorizationRequirement,
    ToolInputs,
    ToolOutput,
    ToolRequirements,
    ValueSchema,
)
from arcade.sdk.tool import tool
from arcade.tool.catalog import ToolCatalog


def test_create_tool_with_input_param():
    @tool
    def sample_function(param1: str):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.inputs == ToolInputs(
        parameters=[
            InputParameter(
                name="param1",
                description="No description provided.",
                inferrable=True,  # Defaults to true
                required=True,  # Defaults to required (no default value in the function signature)
                value_schema=ValueSchema(val_type="string", enum=None),
            )
        ]
    )


def test_create_tool_with_input_param_with_default():
    @tool
    def sample_function(param1: str = "default"):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.inputs == ToolInputs(
        parameters=[
            InputParameter(
                name="param1",
                description="No description provided.",
                inferrable=True,
                required=False,  # Because a default value is provided
                value_schema=ValueSchema(val_type="string", enum=None),
            )
        ]
    )


def test_create_tool_with_optional_input_param():
    @tool
    def sample_function(param1: Optional[str]):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.inputs == ToolInputs(
        parameters=[
            InputParameter(
                name="param1",
                description="No description provided.",
                inferrable=True,
                required=False,  # Because of Optional[str]
                value_schema=ValueSchema(val_type="string", enum=None),
            )
        ]
    )


def test_create_tool_with_inferrable_input_param():
    @tool
    def sample_function(param1: Annotated[str, "param description", Inferrable(False)]):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.inputs == ToolInputs(
        parameters=[
            InputParameter(
                name="param1",
                description="param description",
                inferrable=False,  # Not the default, thanks to Opaque
                required=True,
                value_schema=ValueSchema(val_type="string", enum=None),
            )
        ]
    )


def test_create_tool_with_multiple_input_params():
    @tool
    def sample_function(param1: str, param2: int, param3: float, param4: bool):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.inputs == ToolInputs(
        parameters=[
            InputParameter(
                name="param1",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(val_type="string", enum=None),
            ),
            InputParameter(
                name="param2",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(val_type="integer", enum=None),
            ),
            InputParameter(
                name="param3",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(val_type="decimal", enum=None),
            ),
            InputParameter(
                name="param4",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(val_type="boolean", enum=None),
            ),
        ]
    )


def test_create_tool_with_input_dict_param():
    @tool
    def sample_function(param1: dict):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.inputs == ToolInputs(
        parameters=[
            InputParameter(
                name="param1",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(val_type="json", enum=None),
            )
        ]
    )


def test_create_tool_with_input_string_enum_param():
    @tool
    def sample_function(param1: Literal["value1", "value2"]):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.inputs == ToolInputs(
        parameters=[
            InputParameter(
                name="param1",
                description="No description provided.",
                inferrable=True,
                required=True,
                value_schema=ValueSchema(val_type="string", enum=["value1", "value2"]),
            )
        ]
    )


def test_create_tool_with_unsupported_input_param():
    @tool
    def sample_function(param1: complex):
        pass

    try:
        ToolCatalog.create_tool_definition(sample_function, "1.0")
    except TypeError as e:
        assert str(e) == "Unsupported parameter type: <class 'complex'>"


def test_create_tool_with_annotated_param():
    @tool
    def sample_function(my_param: Annotated[str, "a description"]):
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.inputs.parameters[0] == InputParameter(
        name="my_param",
        description="a description",
        inferrable=True,
        required=True,
        value_schema=ValueSchema(val_type="string", enum=None),
    )


def test_create_tool_with_no_return():
    @tool
    def sample_function():
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.output.available_modes == ["null"]
    assert not tool_def.output.value_schema


def test_create_tool_with_output_value():
    @tool
    def sample_function() -> str:
        return "output"

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.output == ToolOutput(
        description="No description provided.",
        available_modes=["value", "error"],
        value_schema=ValueSchema(val_type="string", enum=None),
    )


def test_create_tool_with_optional_output_value():
    @tool
    def sample_function() -> Optional[str]:
        return "output"

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.output == ToolOutput(
        description="No description provided.",
        available_modes=["value", "error", "null"],
        value_schema=ValueSchema(val_type="string", enum=None),
    )


def test_create_tool_with_annotated_output_value():
    @tool
    def sample_function() -> Annotated[str, "output description"]:
        return "output"

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.output == ToolOutput(
        description="output description",
        available_modes=["value", "error"],
        value_schema=ValueSchema(val_type="string", enum=None),
    )


@pytest.mark.parametrize(
    "tool_decorator_args, expected_tool_def_fields",
    [
        pytest.param(
            {},
            {
                "version": "1.0",
                "name": "sample_function",
                "description": "No description provided.",
            },
            id="test_with_version",
        ),
        pytest.param({}, {"name": "sample_function"}, id="test_with_default_function_name"),
        pytest.param(
            {"name": "custom_name"},
            {"name": "custom_name"},
            id="test_with_specified_name",
        ),
        pytest.param(
            {},
            {"description": "No description provided."},
            id="test_with_no_description",
        ),
        pytest.param(
            {"description": "Custom description"},
            {"description": "Custom description"},
            id="test_with_specified_description",
        ),
        pytest.param(
            {
                "requires_auth": OAuth2AuthorizationRequirement(
                    url="https://example.com/oauth2/auth", scope=["scope1", "scope2"]
                )
            },
            {
                "requirements": ToolRequirements(
                    **{
                        "authorization": OAuth2AuthorizationRequirement(
                            url="https://example.com/oauth2/auth",
                            scope=["scope1", "scope2"],
                        )
                    }
                )
            },
            id="test_with_oauth2_auth_requirement",
        ),
    ],
)
def test_create_tool_def(tool_decorator_args, expected_tool_def_fields):
    @tool(**tool_decorator_args)
    def sample_function():
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    for field, expected_value in expected_tool_def_fields.items():
        assert getattr(tool_def, field) == expected_value


# Needs to be a separate test because of docstring
def test_create_tool_def_with_docstring_description():
    @tool
    def sample_function():
        """Docstring description"""
        pass

    tool_def = ToolCatalog.create_tool_definition(sample_function, "1.0")

    assert tool_def.description == "Docstring description"  # Uses docstring description
