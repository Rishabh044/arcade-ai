class ToolError(Exception):
    """
    Base class for all errors related to tools.
    """

    pass


class ToolDefinitionError(ToolError):
    """
    Raised when there is an error in the definition of a tool.
    """

    pass


# ------  runtime errors ------


class ToolRuntimeError(RuntimeError):
    pass


class ToolExecutionError(ToolRuntimeError):
    """
    Raised when there is an error executing a tool.
    """

    pass


class ToolSerializationError(ToolRuntimeError):
    """
    Raised when there is an error executing a tool.
    """

    pass


class ToolInputError(ToolSerializationError):
    """
    Raised when there is an error in the input to a tool.
    """

    pass


class ToolOutputError(ToolSerializationError):
    """
    Raised when there is an error in the output of a tool.
    """

    pass
