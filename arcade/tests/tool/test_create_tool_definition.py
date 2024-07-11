from arcade.sdk.models import OAuth2AuthorizationRequirement
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
