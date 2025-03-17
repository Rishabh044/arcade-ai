import pytest
from arcade.sdk.errors import ToolExecutionError

from arcade_math.tools.exponents import (
    log,
    power,
)


def test_log():
    assert log("8", "2") == "3.0"
    assert log("2", "3") == "0.6309297535714574"
    assert log("2", "0.5") == "-1.0"
    with pytest.raises(ToolExecutionError):
        log("-1", "0.5")
    with pytest.raises(ToolExecutionError):
        log("0", "10")


def test_power():
    assert power("-8", "2") == "64"
    assert power("0", "10") == "0"
    assert power("2", "0.5") == "1.414213562373095048801688724"
    assert power("2", "3") == "8"
    assert power("2.", "-0.5") == "0.7071067811865475244008443621"
    assert power("2.1234", "0.6") == "1.571155202490495156807227175"
    assert power("2.1234", "1") == "2.1234"
    assert power("2.1234", "3") == "9.574044440904"
    assert power("8", "-2") == "0.015625"
    assert power("8", "2") == "64"
    with pytest.raises(ToolExecutionError):
        power("-1", "0.5")
