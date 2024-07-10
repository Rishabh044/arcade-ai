from typing import Annotated, Optional

from pydantic import BaseModel

from arcade.sdk.tool import Param
from arcade.tool.catalog import create_func_models


def test_models_subclass_BaseModel():
    def sample_function():
        pass

    input_model, output_model = create_func_models(sample_function)

    # Both should subclass BaseModel
    assert issubclass(input_model, BaseModel)
    assert issubclass(output_model, BaseModel)


def test_function_with_no_params_has_no_input_fields():
    def sample_function():
        pass

    input_model, _ = create_func_models(sample_function)

    # No input fields
    assert not input_model.model_fields


def test_function_with_null_return_has_no_output_fields():
    def sample_function():
        pass

    _, output_model = create_func_models(sample_function)

    # No output fields
    assert not output_model.model_fields


def test_create_func_model_with_simple_types_has_correct_fields():
    def sample_function(
        param1: int,
        param2: str,
    ) -> str:
        return f"{param1} {param2}"

    input_model, output_model = create_func_models(sample_function)

    check_model_fields(
        input_model,
        {"param1": (int, "No description provided."), "param2": (str, "No description provided.")},
    )

    check_model_fields(
        output_model,
        {
            "result": (
                str,
                "No description provided.",
            )  # Not Optional[str] TODO this is inconsistent
        },
    )

    # Check if input_model has the correct fields
    assert "param1" in input_model.model_fields
    assert input_model.__annotations__["param1"] is int
    assert input_model.model_fields["param1"].description == "No description provided."

    assert "param2" in input_model.model_fields
    assert input_model.__annotations__["param2"] is str
    assert input_model.model_fields["param2"].description == "No description provided."

    # Check if output_model has the correct fields
    assert "result" in output_model.model_fields
    assert output_model.__annotations__["result"] is str  # Not Optional[str]
    assert output_model.model_fields["result"].description == "No description provided."


def test_create_func_model_with_Annotated_has_correct_fields():
    def sample_function(
        param1: Annotated[int, "The first operand"], param2: Annotated[str, "The second operand"]
    ) -> Annotated[str, "Returns magical things"]:
        return f"{param1} {param2}"

    input_model, output_model = create_func_models(sample_function)

    check_model_fields(
        input_model, {"param1": (int, "The first operand"), "param2": (str, "The second operand")}
    )

    check_model_fields(output_model, {"result": (Optional[str], "Returns magical things")})


def test_create_func_model_with_Param_has_correct_fields():
    def sample_function(
        param1: Param(int, "The first operand"),
        param2: Param(str, "The second operand"),
    ) -> Param(str, "Returns magical things"):
        return f"{param1} {param2}"

    input_model, output_model = create_func_models(sample_function)

    check_model_fields(
        input_model, {"param1": (int, "The first operand"), "param2": (str, "The second operand")}
    )

    check_model_fields(output_model, {"result": (Optional[str], "Returns magical things")})


def check_model_fields(model: BaseModel, expected_fields: dict[type, str]):
    for field_name, (field_type, field_description) in expected_fields.items():
        assert field_name in model.model_fields
        assert model.__annotations__[field_name] == field_type
        assert model.model_fields[field_name].description == field_description
