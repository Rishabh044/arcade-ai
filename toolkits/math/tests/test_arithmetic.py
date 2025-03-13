import pytest
from arcade.sdk.errors import ToolExecutionError

from arcade_math.tools.arithmetic import (
    add,
    subtract,
    multiply,
    divide,
    sqrt,
    sum_list,
    sum_range,
    mod,
    power,
    abs_val,
    log,
    avg,
    median,
    factorial,
    deg_to_rad,
    rad_to_deg,
    ceil,
    floor,
    round_num,
    gcd,
    lcm,
)


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1", "2", "3"),
        ("-1", "1", "0"),
        ("0.5", "10.9", "11.4"),
        # Big ints
        ("12345678901234567890", "9876543210987654321", "22222222112222222211"),
        # Big floats
        (
            "12345678901234567890.120",
            "9876543210987654321.987",
            "22222222112222222212.107",
        ),
    ],
)
def test_add(a, b, expected):
    assert add(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("1", "2", "-1"),
        ("-1", "1", "-2"),
        ("0.5", "10.9", "-10.4"),
        # Big ints
        ("12345678901234567890", "12323456679012345668", "22222222222222222"),
        # Big floats
        (
            "12345678901234567890.120",
            "12343557689113355768.9079",
            "2121212121212121.2121",
        ),
    ],
)
def test_subtract(a, b, expected):
    assert subtract(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("-1", "2", "-2"),
        # TODO(mateo): ok to return negative 0?
        ("-10", "0", "-0"),
        ("0.5", "10.9", "5.45"),
        # TODO(mateo): is scientific notation is acceptable as output?
        # Big ints
        (
            "12345678901234567890",
            "18000000162000001474380013420000",
            "2.222222222222222222222222223E+50"
        ),
        # Big floats
        (
            "12345678901234567890.120",
            "12345678901234567890.120",
            "1.524157875323883675048681628E+38",
        ),
    ],
)
def test_multiply(a, b, expected):
    assert multiply(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("-1", "2", "-0.5"),
        ("-10", "1", "-10"),
        ("0.5", "10.9", "0.04587155963302752293577981651"),
        # Big ints
        (
            "152407406035740740602050",
            "12345678901234567890",
            "12345"
        ),
        # Big floats
        (
            "152407406035740740603531.400",
            "12345678901234567890.120",
            "12345",
        ),
    ],
)
def test_divide(a, b, expected):
    assert divide(a, b) == expected


def text_zero_division():
    with pytest.raises(ToolExecutionError):
        divide("1", "0")
    with pytest.raises(ToolExecutionError):
        divide("1", "0.0")
    with pytest.raises(ToolExecutionError):
        divide("1", "0.000000")


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


def test_sum_list():
    assert sum_list(["1", "2", "3", "4", "5", "6"]) == "21"
    assert sum_list([]) == "0"
    assert sum_list(["-1", "-2", "-3", "-4", "-5", "-6"]) == "-21"
    assert sum_list(["0.1", "0.2", "0.3", "0.3", "0.5", "0.7"]) == "2.1"


def test_sum_range():
    assert sum_range("8", "2") == "0"
    assert sum_range("-8", "2") == "-33"
    assert sum_range("8", "-2") == "0"
    assert sum_range("2", "3") == "5"
    assert sum_range("0", "10") == "55"
    with pytest.raises(ToolExecutionError):
        sum_range("2", "0.5")
    with pytest.raises(ToolExecutionError):
        sum_range("-1", "0.5")
    with pytest.raises(ToolExecutionError):
        sum_range("2.", "0.5")
    with pytest.raises(ToolExecutionError):
        sum_range("-1", "0.5")


def test_mod():
    # TODO(mateo): ok to return negative 0?
    assert mod("-1", "0.5") == "-0.0"
    assert mod("-8", "2") == "-0"
    assert mod("0", "10") == "0"
    assert mod("2", "0.5") == "0.0"
    assert mod("2", "3") == "2"
    assert mod("2.", "-0.5") == "0.0"
    assert mod("2.1234", "0.6") == "0.3234"
    assert mod("2.1234", "1") == "0.1234"
    assert mod("2.1234", "3") == "2.1234"
    assert mod("8", "-2") == "0"
    assert mod("8", "2") == "0"


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


def test_abs_val():
    assert abs_val("2") == "2"
    assert abs_val("-1") == "1"
    assert abs_val("-1.12341234") == "1.12341234"


def test_log():
    assert log("8", "2") == "3.0"
    assert log("2", "3") == "0.6309297535714574"
    assert log("2", "0.5") == "-1.0"
    with pytest.raises(ToolExecutionError):
        log("-1", "0.5")
    with pytest.raises(ToolExecutionError):
        log("0", "10")


def test_avg():
    assert avg(["1", "2", "3", "4", "5", "6"]) == "3.5"
    assert avg([]) == "0.0"
    assert avg(["-1", "-2", "-3", "-4", "-5", "-6"]) == "-3.5"
    assert avg(["0.1", "0.2", "0.3", "0.3", "0.5", "0.7"]) == "0.35"


def test_median():
    assert median(["1", "2", "3", "4", "5", "6"]) == "3.5"
    assert median([]) == "0.0"
    assert median(["-1", "-2", "-3", "-4", "-5", "-6"]) == "-3.5"
    assert median(["0.1", "0.2", "0.3", "0.3", "0.5", "0.7"]) == "0.3"


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


def test_deg_to_rad():
    assert deg_to_rad("1") == "0.017453292519943295"
    assert deg_to_rad("-1") == "-0.017453292519943295"
    assert deg_to_rad("0") == "0.0"
    assert deg_to_rad("-0") == "-0.0"
    assert deg_to_rad("23") == "0.4014257279586958"
    assert deg_to_rad("24") == "0.4188790204786391"
    assert deg_to_rad("-10") == "-0.17453292519943295"
    assert deg_to_rad("10") == "0.17453292519943295"
    assert deg_to_rad("180") == "3.141592653589793"
    assert deg_to_rad("0.0") == "0.0"
    assert deg_to_rad("0.0000") == "0.0"
    assert deg_to_rad("-0.0") == "-0.0"
    assert deg_to_rad("1.0") == "0.017453292519943295"
    assert deg_to_rad("-1.0") == "-0.017453292519943295"
    assert deg_to_rad("23.0") == "0.4014257279586958"
    assert deg_to_rad("0.4") == "0.006981317007977318"
    assert deg_to_rad("-10.0") == "-0.17453292519943295"
    assert deg_to_rad("10.0") == "0.17453292519943295"


def test_rad_to_deg():
    assert rad_to_deg("1") == "57.29577951308232"
    assert rad_to_deg("-1") == "-57.29577951308232"
    assert rad_to_deg("0") == "0.0"
    assert rad_to_deg("-0") == "-0.0"
    assert rad_to_deg("23") == "1317.8029288008934"
    assert rad_to_deg("24") == "1375.0987083139757"
    assert rad_to_deg("-10") == "-572.9577951308232"
    assert rad_to_deg("10") == "572.9577951308232"
    assert rad_to_deg("0.0") == "0.0"
    assert rad_to_deg("0.0000") == "0.0"
    assert rad_to_deg("-0.0") == "-0.0"
    assert rad_to_deg("1.0") == "57.29577951308232"
    assert rad_to_deg("-1.0") == "-57.29577951308232"
    assert rad_to_deg("3.14") == "179.9087476710785"
    assert rad_to_deg("0.4") == "22.918311805232932"
    assert rad_to_deg("-10.0") == "-572.9577951308232"
    assert rad_to_deg("10.0") == "572.9577951308232"


def test_ceil():
    assert ceil("1") == "1"
    assert ceil("-1") == "-1"
    assert ceil("0") == "0"
    assert ceil("-0") == "0"
    assert ceil("0.0") == "0"
    assert ceil("0.0000") == "0"
    assert ceil("-0.0") == "0"
    assert ceil("1.0") == "1"
    assert ceil("-1.0") == "-1"
    assert ceil("3.14") == "4"
    assert ceil("0.4") == "1"
    assert ceil("-1.3") == "-1"


def test_floor():
    assert floor("1") == "1"
    assert floor("-1") == "-1"
    assert floor("0") == "0"
    assert floor("-0") == "0"
    assert floor("10") == "10"
    assert floor("0.0") == "0"
    assert floor("0.0000") == "0"
    assert floor("-0.0") == "0"
    assert floor("1.0") == "1"
    assert floor("-1.0") == "-1"
    assert floor("3.14") == "3"
    assert floor("0.4") == "0"
    assert floor("-1.3") == "-2"


def test_round_num():
    # TODO(mateo): ok with scientific notatin? ok with negative round digits?
    assert round_num("1.2345", "-2") == "0E+2"
    assert round_num("1.2345", "-1") == "0E+1"
    assert round_num("1.2345", "0") == "1"
    assert round_num("1.2345", "1") == "1.2"
    assert round_num("1.2345", "2") == "1.23"
    assert round_num("1.2345", "3") == "1.234"
    assert round_num("1.2345", "8") == "1.23450000"
    assert round_num("1.654321", "-2") == "0E+2"
    assert round_num("1.654321", "-1") == "0E+1"
    assert round_num("1.654321", "0") == "2"
    assert round_num("1.654321", "1") == "1.7"
    assert round_num("1.654321", "2") == "1.65"
    assert round_num("1.654321", "3") == "1.654"
    assert round_num("1.654321", "8") == "1.65432100"


def test_gcd():
    assert gcd("-15", "-5") == "5"
    assert gcd("15", "0") == "15"
    assert gcd("15", "-2") == "1"
    assert gcd("15", "-0") == "15"
    assert gcd("15", "5") == "5"
    assert gcd("7", "13") == "1"
    assert gcd("-13", "13") == "13"
    with pytest.raises(ToolExecutionError):
        gcd("15.0", "5.0")


def test_lcm():
    assert lcm("-15", "-5") == "15"
    assert lcm("15", "0") == "0"
    assert lcm("15", "-2") == "30"
    assert lcm("15", "-0") == "0"
    assert lcm("15", "5") == "15"
    assert lcm("7", "13") == "91"
    assert lcm("-13", "13") == "13"
    with pytest.raises(ToolExecutionError):
        lcm("15.0", "5.0")
