"""Rich-based terminal output helpers. All pipeline feedback goes through here."""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich import box

_console = Console()


def get_console() -> Console:
    return _console


def print_agent_start(agent_name: str) -> None:
    _console.print(f"\n[bold cyan]▶ {agent_name}[/bold cyan]")


def print_agent_complete(agent_name: str, token_usage: dict) -> None:
    input_t = token_usage.get("input_tokens", "?")
    output_t = token_usage.get("output_tokens", "?")
    _console.print(
        f"[green]✓ {agent_name}[/green]  "
        f"[dim]in={input_t} out={output_t} tokens[/dim]"
    )


def print_warning(message: str) -> None:
    _console.print(Panel(f"[yellow]{message}[/yellow]", title="⚠ Warning", border_style="yellow"))


def print_error(message: str) -> None:
    _console.print(Panel(f"[red]{message}[/red]", title="✗ Error", border_style="red"))


def print_section(title: str) -> None:
    _console.rule(f"[bold]{title}[/bold]")


def print_briefs_table(briefs: list) -> None:
    """Print ContentBrief objects as a readable Rich table for interactive review."""
    table = Table(title="Content Briefs — Review & Select", box=box.ROUNDED, show_lines=True)
    table.add_column("#", style="bold", width=3)
    table.add_column("ID", style="cyan", width=28)
    table.add_column("Format", width=6)
    table.add_column("Title", width=40)
    table.add_column("Angle", width=50)
    table.add_column("Score", width=6)

    for i, brief in enumerate(briefs, 1):
        table.add_row(
            str(i),
            brief.brief_id,
            brief.format,
            brief.title,
            brief.angle[:80],
            f"{brief.priority_score:.2f}",
        )

    _console.print(table)


def print_final_summary(batch_id: str, output_paths: dict[str, str]) -> None:
    table = Table(title=f"Pipeline Complete — {batch_id}", box=box.SIMPLE_HEAVY)
    table.add_column("Output", style="bold")
    table.add_column("Path", style="dim")

    for name, path in output_paths.items():
        table.add_row(name, path)

    _console.print(table)


def make_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=_console,
    )
