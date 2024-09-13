from typing import TYPE_CHECKING, Any

import typer
from openai.resources.chat.completions import ChatCompletionChunk, Stream
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from typer.core import TyperGroup
from typer.models import Context

from arcade.core.catalog import ToolCatalog
from arcade.core.config_model import Config
from arcade.core.toolkit import Toolkit

if TYPE_CHECKING:
    from arcade.sdk.eval.eval import EvaluationResult

console = Console()


class OrderCommands(TyperGroup):
    def list_commands(self, ctx: Context) -> list[str]:  # type: ignore[override]
        """Return list of commands in the order appear."""
        return list(self.commands)  # get commands using self.commands


def create_cli_catalog(
    toolkit: str | None = None,
    show_toolkits: bool = False,
) -> ToolCatalog:
    """
    Load toolkits from the python environment.
    """
    if toolkit:
        try:
            prefixed_toolkit = "arcade_" + toolkit
            toolkits = [Toolkit.from_package(prefixed_toolkit)]
        except ValueError:
            try:  # try without prefix
                toolkits = [Toolkit.from_package(toolkit)]
            except ValueError as e:
                console.print(f"❌ {e}", style="bold red")
                typer.Exit(code=1)
    else:
        toolkits = Toolkit.find_all_arcade_toolkits()

    if not toolkits:
        console.print("❌ No toolkits found or specified", style="bold red")
        typer.Exit(code=1)

    catalog = ToolCatalog()
    for loaded_toolkit in toolkits:
        if show_toolkits:
            console.print(f"Loading toolkit: {loaded_toolkit.name}", style="bold blue")
        catalog.add_toolkit(loaded_toolkit)
    return catalog


def display_streamed_markdown(stream: Stream[ChatCompletionChunk], model: str) -> tuple[str, str]:
    """
    Display the streamed markdown chunks as a single line.
    """
    from rich.live import Live

    full_message = ""
    role = ""
    with Live(console=console, refresh_per_second=10) as live:
        for chunk in stream:
            choice = chunk.choices[0]
            chunk_message = choice.delta.content
            if role == "":
                role = choice.delta.role or ""
                if role == "assistant":
                    console.print(f"\n[bold blue]Assistant ({model}):[/bold blue] ")
            if chunk_message:
                full_message += chunk_message
                markdown_chunk = Markdown(full_message)
                live.update(markdown_chunk)

        # Markdownify URLs in the final message if applicable
        if role == "assistant":
            full_message = markdownify_urls(full_message)
            live.update(Markdown(full_message))

    return role, full_message


def markdownify_urls(message: str) -> str:
    """
    Convert URLs in the message to markdown links.
    """
    import re

    # This regex will match URLs that are not already formatted as markdown links:
    # [Link text](https://example.com)
    url_pattern = r"(?<!\]\()https?://\S+"

    # Wrap all URLs in the message with markdown links
    return re.sub(url_pattern, r"[Link](\g<0>)", message)


def validate_and_get_config(
    validate_engine: bool = True,
    validate_api: bool = True,
    validate_user: bool = True,
) -> Config:
    """
    Validates the configuration, user, and returns the Config object
    """
    from arcade.core.config import config

    if validate_engine and (not config.engine or not config.engine_url):
        console.print("❌ Engine configuration not found or URL is missing.", style="bold red")
        raise typer.Exit(code=1)

    if validate_api and (not config.api or not config.api.key):
        console.print(
            "❌ API configuration not found or key is missing. Please run `arcade login`.",
            style="bold red",
        )
        raise typer.Exit(code=1)

    if validate_user and (not config.user or not config.user.email):
        console.print(
            "❌ User email not found in configuration. Please run `arcade login`.", style="bold red"
        )
        raise typer.Exit(code=1)

    return config


def apply_config_overrides(
    config: Config, host_input: str | None, port_input: int | None, tls_input: bool | None
) -> None:
    """
    Apply optional config overrides (passed by the user) to the config object.
    """

    if not config.engine:
        # Should not happen, validate_and_get_config ensures that `engine` is set
        raise ValueError("Engine configuration not found in config.")

    # Special case for "localhost" and nothing else specified:
    # default to dev port and no TLS for convenience
    if host_input == "localhost":
        if port_input is None:
            port_input = 9099
        if tls_input is None:
            tls_input = False

    if host_input:
        config.engine.host = host_input

    if port_input is not None:
        config.engine.port = port_input

    if tls_input is not None:
        config.engine.tls = tls_input


def display_eval_results(results: list[dict[str, Any]], show_details: bool = False) -> None:
    """
    Display evaluation results in a more readable format with color-coded matches.

    Args:
        results: List of dictionaries containing evaluation results for each model.
        show_details: Whether to show detailed results for each case.
    """
    for model_results in results:
        model = model_results.get("model", "Unknown Model")
        cases = model_results.get("cases", [])

        table = Table(
            title=f"Evaluation Results for {model}", show_header=True, header_style="bold magenta"
        )
        table.add_column("Case")
        table.add_column("Expected Tools")
        table.add_column("Predicted Tools")
        table.add_column("Score")
        table.add_column("Status")

        for case in cases:
            expected_tools = ", ".join(tc["name"] for tc in case["expected_tool_calls"])
            predicted_tools = ", ".join(tc["name"] for tc in case["predicted_tool_calls"])
            evaluation = case["evaluation"]
            status = (
                "[green]Pass[/green]"
                if evaluation.passed
                else "[yellow]Warning[/yellow]"
                if evaluation.warning
                else "[red]Fail[/red]"
            )

            table.add_row(
                case["name"][:30] + "..." if len(case["name"]) > 30 else case["name"],
                expected_tools,
                predicted_tools,
                f"{evaluation.score:.2f}",
                status,
            )

        console.print(table)

        # Display detailed results in a panel
        for case in cases:
            if not show_details:
                eval_results = f"[bold]Evaluation:[/bold]\n{_format_evaluation(case['evaluation'])}"
                console.print(Panel(eval_results, title=f"Case: {case['name']}", expand=False))
            else:
                detailed_results = (
                    f"[bold]User Input:[/bold] {case['input']}\n\n"
                    f"[bold]Expected Tool Calls:[/bold]\n{_format_tool_calls(case['expected_tool_calls'])}\n\n"
                    f"[bold]Predicted Tool Calls:[/bold]\n{_format_tool_calls(case['predicted_tool_calls'])}\n\n"
                    f"[bold]Evaluation:[/bold]\n{_format_evaluation(case['evaluation'])}\n"
                )
                console.print(Panel(detailed_results, title=f"Case: {case['name']}", expand=False))
            console.print("-" * 80)


def _format_args(args: dict[str, Any]) -> str:
    """Format argument dictionary for display."""
    return "\n".join(f"    {k}: {v}" for k, v in args.items())


def _format_evaluation(evaluation: "EvaluationResult") -> str:
    """
    Format evaluation results with color-coded matches and accurate score ranges.

    Args:
        evaluation: An EvaluationResult object containing the evaluation results.

    Returns:
        A formatted string representation of the evaluation results.
    """
    result = []
    result.append(f"  Score: {evaluation.score:.2f}")

    # Determine and add the overall result status
    if evaluation.passed:
        result.append("  [green]Result: Pass[/green]")
        # Early return if passed, skipping detailed results
        # TODO: Make this optional
        return "\t".join(result)
    elif evaluation.warning:
        result.append("  [yellow]Result: Warning[/yellow]")
    elif evaluation.fail:
        result.append("  [red]Result: Fail[/red]")
    else:
        result.append("  [bold red]Result: Unknown[/bold red]")

    # make consistent with shorter return
    result = ["\t".join(result)]

    # Add critic results header if we didn't pass
    result.append("\n[bold]Critic Results:[/bold]")

    # Process each critic result
    for critic_result in evaluation.results:
        if critic_result["weight"] <= 0.0:
            continue
        match_color = "green" if critic_result["match"] else "red"
        weight = critic_result["weight"]
        field = critic_result["field"]

        critic_result_str = (
            f"  [bold]{field}:[/bold] "
            f"[{match_color}]"
            f"Match: {critic_result['match']}, "
            f"Score: {critic_result['score']:.2f}/{weight:.2f}"
            f"[/{match_color}]"
        )
        result.append(critic_result_str)

    return "\n".join(result)


def _format_tool_calls(tool_calls: list[dict[str, Any]]) -> str:
    """Format tool calls for display."""
    formatted_calls = []
    for tc in tool_calls:
        formatted_call = f"  Tool: {tc['name']}\n  Args:\n{_format_args(tc['args'])}"
        formatted_calls.append(formatted_call)
    return "\n\n".join(formatted_calls)
