import pytest
from pydantic import BaseModel
from arcade.tool.catalog import create_func_models

# Sample function to test
def sample_function(param1: int, param2: str) -> str:
    """
    A sample function to test create_func_models.
    """
    return f"{param1} {param2}"

def test_create_func_models():
    input_model, output_model = create_func_models(sample_function)

    # Check if input_model is a subclass of BaseModel
    assert issubclass(input_model, BaseModel)

    # Check if output_model is a subclass of BaseModel
    assert issubclass(output_model, BaseModel)

    # Check if input_model has the correct fields
    assert 'param1' in input_model.model_fields
    assert 'param2' in input_model.model_fields

    # Check if output_model has the correct fields
    assert 'result' in output_model.model_fields

    # Check if the types of the fields are correct
    assert input_model.__annotations__['param1'] == int
    assert input_model.__annotations__['param2'] == str
    assert output_model.__annotations__['result'] == str
