import pytest
from arcade.sdk.errors import ToolExecutionError

from arcade_math.tools.miscellaneous import (
    abs_val,
    factorial,
    sqrt,
)


def test_abs_val():
    assert abs_val("2") == "2"
    assert abs_val("-1") == "1"
    assert abs_val("-1.12341234") == "1.12341234"


def test_factorial():
    assert factorial("1") == "1"
    assert factorial("0") == "1"
    assert factorial("-0") == "1"
    assert factorial("23") == "25852016738884976640000"
    assert factorial("24") == "620448401733239439360000"
    assert factorial("10") == "3628800"
    with pytest.raises(ToolExecutionError):
        factorial("-1")
    with pytest.raises(ToolExecutionError):
        factorial("-10")
    with pytest.raises(ToolExecutionError):
        factorial("0.0000")
    with pytest.raises(ToolExecutionError):
        factorial("-0.0")
    with pytest.raises(ToolExecutionError):
        factorial("1.0")
    with pytest.raises(ToolExecutionError):
        factorial("-1.0")
    with pytest.raises(ToolExecutionError):
        factorial("23.0")


def test_sqrt():
    assert sqrt("1") == "1"
    assert sqrt("0") == "0"
    assert sqrt("-0") == "-0"
    assert sqrt("23") == "4.795831523312719541597438064"
    assert sqrt("24") == "4.898979485566356196394568149"
    assert sqrt("10") == "3.162277660168379331998893544"
    assert sqrt("0.0") == "0.0"
    assert sqrt("0.0000") == "0.00"
    assert sqrt("-0.0") == "-0.0"
    assert sqrt("1.0") == "1.0"
    assert sqrt("3.14") == "1.772004514666935040199112510"
    assert sqrt("0.4") == "0.6324555320336758663997787089"
    assert sqrt("10.0") == "3.162277660168379331998893544"
    with pytest.raises(ToolExecutionError):
        sqrt("-1")
    with pytest.raises(ToolExecutionError):
        sqrt("-10")
    with pytest.raises(ToolExecutionError):
        sqrt("-1.0")
    with pytest.raises(ToolExecutionError):
        sqrt("-1.3")
    with pytest.raises(ToolExecutionError):
        sqrt("-10.0")
