import warnings

import pytest

from arcade.sdk.warns import deprecated


@deprecated("please use new_function", stacklevel=3)
async def add(a, b):
    """A simple async function that adds two numbers."""
    return a + b


@pytest.mark.asyncio
async def test_deprecated_warning_is_emitted():
    # The context manager pytest.warns() will catch a warning matching the given criteria.
    with pytest.warns(DeprecationWarning, match="add is deprecated: please use new_function"):
        result = await add(2, 3)
        assert result == 5


@pytest.mark.asyncio
async def test_deprecated_warning_multiple_calls():
    # Make sure all DeprecationWarnings are caught, even if they are normally suppressed.
    warnings.simplefilter("always", DeprecationWarning)
    with pytest.warns(DeprecationWarning) as record:
        results = []
        for i in range(3):
            results.append(await add(i, i))
        # Check that the function returns the expected values.
        assert results == [0, 2, 4]
    # Ensure that a warning was raised for each call.
    assert len(record) == 3
