import math
from decimal import Decimal
from statistics import median as stats_median
from typing import Annotated

from arcade.sdk import tool


@tool
def add(
    a: Annotated[str, "The first number as a string"],
    b: Annotated[str, "The second number as a string"],
) -> Annotated[str, "The sum of the two numbers as a string"]:
    """
    Add two numbers together
    """
    # Use Decimal for arbitrary precision
    a_decimal = Decimal(a)
    b_decimal = Decimal(b)
    return str(a_decimal + b_decimal)


@tool
def subtract(
    a: Annotated[str, "The first number as a string"],
    b: Annotated[str, "The second number as a string"],
) -> Annotated[str, "The difference of the two numbers as a string"]:
    """
    Subtract two numbers
    """
    # Use Decimal for arbitrary precision
    a_decimal = Decimal(a)
    b_decimal = Decimal(b)
    return str(a_decimal - b_decimal)


@tool
def multiply(
    a: Annotated[str, "The first number as a string"],
    b: Annotated[str, "The second number as a string"],
) -> Annotated[str, "The product of the two numbers as a string"]:
    """
    Multiply two numbers together
    """
    # Use Decimal for arbitrary precision
    a_decimal = Decimal(a)
    b_decimal = Decimal(b)
    return str(a_decimal * b_decimal)


@tool
def divide(
    a: Annotated[str, "The first number as a string"],
    b: Annotated[str, "The second number as a string"],
) -> Annotated[str, "The quotient of the two numbers as a string"]:
    """
    Divide two numbers.
    """
    # Use Decimal for arbitrary precision
    a_decimal = Decimal(a)
    b_decimal = Decimal(b)
    return str(a_decimal / b_decimal)


@tool
def sqrt(
    a: Annotated[str, "The number to square root as a string"],
) -> Annotated[str, "The square root of the number as a string"]:
    """
    Get the square root of a number
    If 
    """
    # Use Decimal for arbitrary precision
    a_decimal = Decimal(a)
    return str(a_decimal.sqrt())


@tool
def sum_list(
    numbers: Annotated[list[str], "The list of numbers as strings"],
) -> Annotated[str, "The sum of the numbers in the list as a string"]:
    """
    Sum all numbers in a list
    """
    # Use Decimal for arbitrary precision
    return str(sum([Decimal(n) for n in numbers]))


@tool
def sum_range(
    start: Annotated[str, "The start of the range to sum as a string"],
    end: Annotated[str, "The end of the range to sum as a string"],
) -> Annotated[str, "The sum of the numbers in the list as a string"]:
    """
    Sum all numbers from start through end
    """
    return str(sum(list(range(int(start), int(end) + 1))))


# -----------------------
# Additional useful tools
# -----------------------


@tool
def mod(
    a: Annotated[str, "The dividend as a string"],
    b: Annotated[str, "The divisor as a string"],
) -> Annotated[str, "The remainder after dividing a by b as a string"]:
    """
    Calculate the remainder (modulus) of one number divided by another.
    """
    # Use Decimal for arbitrary precision
    return str(Decimal(a) % Decimal(b))


@tool
def power(
    a: Annotated[str, "The base number as a string"],
    b: Annotated[str, "The exponent as a string"],
) -> Annotated[str, "The result of raising a to the power of b as a string"]:
    """
    Calculate one number raised to the power of another.
    """
    # Use Decimal for arbitrary precision
    return str(Decimal(a)**Decimal(b))


@tool
def abs_val(
    a: Annotated[int, "The number as a string"],
) -> Annotated[int, "The absolute value of the number as a string"]:
    """
    Calculate the absolute value of a number.
    """
    # Use Decimal for arbitrary precision
    return str(abs(Decimal(a)))


@tool
def log(
    a: Annotated[str, "The number to take the logarithm of as a string"],
    base: Annotated[str, "The logarithmic base as a string"],
) -> Annotated[str, "The logarithm of the number with the specified base as a string"]:
    """
    Calculate the logarithm of a number with a given base.
    """
    # Use Decimal for arbitrary precision
    return str(math.log(Decimal(a), Decimal(base)))


@tool
def avg(
    numbers: Annotated[list[str], "The list of numbers as strings"],
) -> Annotated[str, "The average (mean) of the numbers in the list as a string"]:
    """
    Calculate the average (mean) of a list of numbers.
    Returns "0.0" if the list is empty.
    """
    # Use Decimal for arbitrary precision
    numbers = [Decimal(n) for n in numbers]
    return str(sum(numbers) / len(numbers)) if numbers else "0.0"


@tool
def median(
    numbers: Annotated[list[str], "A list of numbers as strings"],
) -> Annotated[str, "The median value of the numbers in the list as a string"]:
    """
    Calculate the median of a list of numbers.
    Returns "0.0" if the list is empty.
    """
    # Use Decimal for arbitrary precision
    numbers = [Decimal(n) for n in numbers]
    return str(stats_median(numbers)) if numbers else "0.0"


@tool
def factorial(
    a: Annotated[str, "The non-negative integer to compute the factorial for as a string"],
) -> Annotated[str, "The factorial of the number as a string"]:
    """
    Compute the factorial of a non-negative integer.
    Returns 1 for 0.
    """
    return str(math.factorial(int(a)))


@tool
def deg_to_rad(
    degrees: Annotated[str, "Angle in degrees as a string"],
) -> Annotated[str, "Angle in radians as a string"]:
    """
    Convert an angle from degrees to radians.
    """
    # Use Decimal for arbitrary precision
    return str(math.radians(Decimal(degrees)))


@tool
def rad_to_deg(
    radians: Annotated[str, "Angle in radians as a string"],
) -> Annotated[str, "Angle in degrees as a string"]:
    """
    Convert an angle from radians to degrees.
    """
    # Use Decimal for arbitrary precision
    return str(math.degrees(Decimal(radians)))


@tool
def ceil(
    a: Annotated[str, "The number to round up as a string"],
) -> Annotated[str, "The smallest integer greater than or equal to the number as a string"]:
    """
    Return the ceiling of a number.
    """
    # Use Decimal for arbitrary precision
    return str(math.ceil(Decimal(a)))


@tool
def floor(
    a: Annotated[str, "The number to round down as a string"],
) -> Annotated[str, "The largest integer less than or equal to the number as a string"]:
    """
    Return the floor of a number.
    """
    # Use Decimal for arbitrary precision
    return str(math.floor(Decimal(a)))


@tool
def round_num(
    value: Annotated[str, "The number to round as a string"],
    ndigits: Annotated[str, "The number of digits after the decimal point as a string"],
) -> Annotated[str, "The number rounded to the specified number of digits as a string"]:
    """
    Round a number to a specified number of digits.
    """
    # Use Decimal for arbitrary precision
    return str(round(Decimal(value), int(ndigits)))


@tool
def gcd(
    a: Annotated[str, "First integer as a string"],
    b: Annotated[str, "Second integer as a string"],
) -> Annotated[str, "The greatest common divisor of a and b as a string"]:
    """
    Calculate the greatest common divisor (GCD) of two integers.
    """
    return str(math.gcd(int(a), int(b)))


@tool
def lcm(
    a: Annotated[str, "First integer as a string"],
    b: Annotated[str, "Second integer as a string"],
) -> Annotated[str, "The least common multiple of a and b as a string"]:
    """
    Calculate the least common multiple (LCM) of two integers.
    Returns "0" if either integer is 0.
    """
    a, b = int(a), int(b)
    if a == 0 or b == 0:
        return "0"
    return str(abs(a * b) // math.gcd(a, b))
