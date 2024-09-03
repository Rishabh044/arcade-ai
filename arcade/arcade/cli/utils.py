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
from arcade.core.toolkit import Toolkit

if TYPE_CHECKING:
    from arcade.core.config import Config

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
) -> "Config":
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
        table.add_column("Case", style="cyan", no_wrap=True)
        table.add_column("Expected Tool", style="green")
        table.add_column("Predicted Tool", style="yellow")
        table.add_column("Score", justify="right")
        table.add_column("Status", justify="center")

        for case in cases:
            status = "✅" if case["evaluation"]["pass"] else "❌"
            if case["evaluation"].get("warning"):
                status = "⚠️"

            table.add_row(
                case["name"][:30] + "..." if len(case["name"]) > 30 else case["name"],
                case["expected_tool"],
                case["predicted_tool"],
                f"{case['evaluation']['score']:.2f}",
                status,
            )

        console.print(table)

        # Display detailed results in a panel
        for case in cases:
            if not show_details:
                eval_results = (
                    f"[bold]Case:[/bold] {case['name']}\n"
                    f"[bold]Evaluation:[/bold]\t{_format_evaluation(case['evaluation'])}"
                )
                console.print(eval_results)
            else:
                detailed_results = (
                    f"[bold]Case:[/bold] {case['name']}\n\n"
                    f"[bold]User Input:[/bold] {case['input']}\n"
                    f"[bold]Expected Tool:[/bold] {case['expected_tool']}\n"
                    f"[bold]Predicted Tool:[/bold] {case['predicted_tool']}\n\n"
                    f"[bold]Expected Args:[/bold]\n{_format_args(case['expected_args'])}\n"
                    f"[bold]Predicted Args:[/bold]\n{_format_args(case['predicted_args'])}\n\n"
                    f"[bold]Evaluation:[/bold]\n{_format_evaluation(case['evaluation'])}\n"
                )
                console.print(Panel(detailed_results, title="Case Results", expand=False))
            console.print("-" * 80)


def _format_args(args: dict[str, Any]) -> str:
    """Format argument dictionary for display."""
    return "\n".join(f"  {k}: {v}" for k, v in args.items())


def _format_evaluation(evaluation: dict[str, Any]) -> str:
    """
    Format evaluation results with color-coded matches and accurate score ranges.

    Args:
        evaluation: A dictionary containing evaluation results.

    Returns:
        A formatted string representation of the evaluation results.
    """
    result = []
    result.append(f"  Overall Score: {evaluation['score']:.2f}")

    # Determine and add the overall result status
    if evaluation["pass"]:
        result.append("  [green]Result: Pass[/green]")
        # Early return if passed, skipping detailed results
        # TODO: Make this optional
        return "\t".join(result)
    elif evaluation.get("warning"):
        result.append("  [yellow]Result: Warning[/yellow]")
    elif evaluation.get("fail"):
        result.append("  [red]Result: Fail[/red]")
    else:
        result.append("  [bold red]Result: Unknown[/bold red]")

    # make consistent with shorter return
    result = ["\t".join(result)]

    # Add critic results header if we didn't pass
    result.append("\n[bold]Critic Results:[/bold]")

    # Process each critic result
    for critic in evaluation.get("critic_results", []):
        match_color = "green" if critic.get("match") else "red"
        weight = critic.get("weight", 1.0)
        max_score = critic.get("max_score", 1.0)
        field = critic.get("field", "Unknown")

        critic_result = (
            f"  [bold]{field}:[/bold] "
            f"[{match_color}]"
            f"Match: {critic.get('match', False)}, "
            f"Score: {critic.get('score', 0):.2f}/{max_score:.2f} "
            f"(Weight: {weight:.2f})"
            f"[/{match_color}]"
        )
        result.append(critic_result)

    return "\n".join(result)
