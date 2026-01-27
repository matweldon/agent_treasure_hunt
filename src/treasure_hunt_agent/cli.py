"""
Interactive CLI for the treasure hunt game.

Provides a rich, interactive command-line interface for running
treasure hunts with real-time turn display.

Usage:
    treasure-hunt run path/to/hunt --interactive
    treasure-hunt run path/to/hunt --model gemini-2.5-flash
    treasure-hunt generate path/to/hunt --difficulty medium
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich import box

from treasure_hunt_agent.game_tools import TOOL_DEFINITIONS
from treasure_hunt_agent.treasure_hunt_game import (
    GameResult,
    TreasureHuntGame,
    TurnResult,
)
from treasure_hunt_agent.treasure_hunt_generator import generate_treasure_hunt

app = typer.Typer(
    name="treasure-hunt",
    help="Run AI agents through treasure hunt challenges.",
    add_completion=False,
)
console = Console()


def create_agent(model_name: str, api_key: str):
    """Create a Gemini agent with the specified model."""
    from treasure_hunt_agent.gemini_agent import GeminiAgent

    system_instructions = """You are an expert at navigating filesystems and solving puzzles.
You are in a treasure hunt where you need to find a hidden treasure key by exploring a directory structure.

Your goal:
1. Start by reading the start file to get your first clue
2. Follow clues by navigating directories and reading files
3. Each clue will point you to the next file with a relative path
4. When you find what you think is the treasure key, use check_treasure to verify it

Available tools:
- ls(path): List files and directories
- cd(path): Change to a directory
- cat(file_path): Read a file's contents
- pwd(): Show current directory
- check_treasure(key): Check if a key is correct (ends game if correct)
- give_up(): Give up (ends game as failure)
- ask_human(question): Ask for help

Tips:
- Read clues carefully - they contain relative paths
- You can use ../ to go up directories
- All paths must stay within the treasure hunt boundaries
- When you see a file that just contains text (not a path), it might be the treasure key!

Be methodical and follow the clues step by step. Good luck!
"""

    return GeminiAgent(
        model_name=model_name,
        system_instructions=system_instructions,
        tools=TOOL_DEFINITIONS,
        api_key=api_key,
    )


def display_turn(turn: TurnResult, show_agent_text: bool = True) -> Panel:
    """Create a rich panel displaying a turn result."""
    content = Text()

    # Agent text if present
    if show_agent_text and turn.agent_text:
        content.append("Agent: ", style="bold cyan")
        content.append(f"{turn.agent_text}\n\n", style="dim")

    # Tool calls
    if turn.tool_calls:
        for tc in turn.tool_calls:
            # Tool name and arguments
            args_str = ", ".join(f"{k}={v!r}" for k, v in tc["arguments"].items())
            content.append(f"  {tc['name']}", style="bold green")
            content.append(f"({args_str})\n", style="green")

            # Result (truncated if too long)
            result_str = str(tc["result"])
            if len(result_str) > 200:
                result_str = result_str[:197] + "..."
            # Indent result lines
            for line in result_str.split("\n"):
                content.append(f"    {line}\n", style="dim")
            content.append("\n")
    else:
        content.append("  (no tool calls)\n", style="dim italic")

    # Token usage
    content.append(f"  Tokens: {turn.tokens_used:,}", style="dim")

    return Panel(
        content,
        title=f"[bold]Turn {turn.turn_number}[/bold]",
        border_style="blue",
        box=box.ROUNDED,
    )


def display_game_result(result: GameResult, treasure_key: str | None = None) -> Panel:
    """Create a rich panel displaying the final game result."""
    if result.success:
        title = "[bold green]SUCCESS[/bold green]"
        border_style = "green"
    else:
        title = "[bold red]FAILURE[/bold red]"
        border_style = "red"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="bold")
    table.add_column("Value")

    table.add_row("End Reason", result.end_reason)
    table.add_row("Turns Taken", str(result.turns_taken))
    table.add_row("Total Time", f"{result.total_time:.2f}s")
    table.add_row("", "")
    table.add_row("Prompt Tokens", f"{result.prompt_tokens:,}")
    table.add_row("Completion Tokens", f"{result.completion_tokens:,}")
    table.add_row("Total Tokens", f"{result.total_tokens:,}")

    if result.treasure_key_found:
        table.add_row("", "")
        table.add_row("Key Attempted", result.treasure_key_found)
        if treasure_key:
            table.add_row("Actual Key", treasure_key)
            if result.treasure_key_found == treasure_key:
                table.add_row("Match", "[green]Yes[/green]")
            else:
                table.add_row("Match", "[red]No[/red]")

    if result.error:
        table.add_row("", "")
        table.add_row("Error", f"[red]{result.error}[/red]")

    return Panel(
        table,
        title=title,
        border_style=border_style,
        box=box.DOUBLE,
    )


def display_hunt_info(hunt_result: dict, hunt_path: Path) -> Panel:
    """Display information about a generated hunt."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="bold")
    table.add_column("Value")

    table.add_row("Path", str(hunt_path))
    table.add_row("Start File", hunt_result["start_file"])
    table.add_row("Treasure File", hunt_result["treasure_file"])
    table.add_row("Path Length", f"{hunt_result['path_length']} steps")
    table.add_row("Directories", str(hunt_result["num_directories"]))
    table.add_row("Files", str(hunt_result["num_files"]))
    table.add_row("Treasure Key", f"[dim]{hunt_result['treasure_key']}[/dim]")

    return Panel(
        table,
        title="[bold]Hunt Generated[/bold]",
        border_style="cyan",
        box=box.ROUNDED,
    )


@app.command()
def run(
    hunt_path: Path = typer.Argument(
        ...,
        help="Path to treasure hunt directory",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    model: str = typer.Option(
        "gemini-2.5-flash",
        "--model",
        "-m",
        help="Gemini model to use",
    ),
    max_turns: int = typer.Option(
        50,
        "--max-turns",
        "-t",
        help="Maximum number of turns",
    ),
    max_tokens: int = typer.Option(
        100000,
        "--max-tokens",
        help="Maximum tokens to use",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--batch",
        "-i/-b",
        help="Run interactively (show each turn) or in batch mode",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="GOOGLE_API_KEY",
        help="Google API key (or set GOOGLE_API_KEY env var)",
    ),
):
    """
    Run a treasure hunt with an AI agent.

    The agent will navigate the filesystem structure, following clues
    until it finds the treasure key or fails.
    """
    if not api_key:
        console.print(
            "[red]Error:[/red] No API key provided. "
            "Set GOOGLE_API_KEY or use --api-key",
            style="bold",
        )
        raise typer.Exit(1)

    # Check for config file
    config_path = hunt_path / ".treasure_hunt_config.json"
    if not config_path.exists():
        console.print(
            f"[red]Error:[/red] Not a valid treasure hunt: {hunt_path}",
            style="bold",
        )
        console.print("Missing .treasure_hunt_config.json file")
        raise typer.Exit(1)

    console.print()
    console.print(
        Panel(
            f"[bold]Treasure Hunt[/bold]\n\n"
            f"Path: {hunt_path}\n"
            f"Model: {model}\n"
            f"Max Turns: {max_turns}\n"
            f"Mode: {'Interactive' if interactive else 'Batch'}",
            border_style="cyan",
        )
    )
    console.print()

    # Create agent
    with console.status("[bold cyan]Creating agent...", spinner="dots"):
        try:
            agent = create_agent(model, api_key)
        except Exception as e:
            console.print(f"[red]Error creating agent:[/red] {e}")
            raise typer.Exit(1)

    # Create game
    game = TreasureHuntGame(
        hunt_path=str(hunt_path),
        agent=agent,
        max_turns=max_turns,
        max_tokens=max_tokens,
    )

    # Load treasure key for comparison
    import json

    with open(config_path) as f:
        config = json.load(f)
    treasure_key = config.get("treasure_key")

    if interactive:
        # Interactive mode - show each turn
        console.print("[bold cyan]Starting hunt...[/bold cyan]\n")

        while True:
            # Show spinner while agent thinks
            with console.status(
                f"[bold cyan]Turn {game.state.turn_number + 1}...",
                spinner="dots",
            ):
                turn_result = game.take_turn()

            # Display the turn
            console.print(display_turn(turn_result))

            # Handle human input if needed
            if turn_result.needs_human_input:
                console.print()
                console.print(
                    f"[bold yellow]Agent asks:[/bold yellow] {turn_result.pending_question}"
                )
                response = console.input("[bold]Your response:[/bold] ")
                console.print()

                # Continue with human input
                with console.status("[bold cyan]Processing response...", spinner="dots"):
                    turn_result = game.take_turn(human_input=response)
                console.print(display_turn(turn_result))

            if turn_result.game_over:
                break

        # Show final result
        console.print()
        console.print(display_game_result(turn_result.game_result, treasure_key))

    else:
        # Batch mode - run to completion with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Running treasure hunt...", total=None)

            result = game.run()

            progress.update(task, completed=True)

        # Show summary
        console.print()
        console.print(display_game_result(result, treasure_key))

        # Show tool call summary
        console.print()
        console.print("[bold]Tool Call History:[/bold]")
        for i, call in enumerate(result.tool_calls, 1):
            args_str = ", ".join(f"{k}={v!r}" for k, v in call["arguments"].items())
            result_str = str(call["result"])
            if len(result_str) > 60:
                result_str = result_str[:57] + "..."
            console.print(
                f"  {i:2}. Turn {call['turn']:2}: "
                f"[green]{call['name']}[/green]({args_str}) -> [dim]{result_str}[/dim]"
            )


@app.command()
def generate(
    output_path: Path = typer.Argument(
        ...,
        help="Path where treasure hunt will be created",
    ),
    difficulty: str = typer.Option(
        "easy",
        "--difficulty",
        "-d",
        help="Difficulty level: easy, medium, or hard",
    ),
    seed: Optional[int] = typer.Option(
        None,
        "--seed",
        "-s",
        help="Random seed for reproducibility",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing directory",
    ),
):
    """
    Generate a new treasure hunt.

    Creates a directory structure with clues leading to a treasure key.
    """
    if difficulty not in ("easy", "medium", "hard"):
        console.print(
            f"[red]Error:[/red] Invalid difficulty '{difficulty}'. "
            "Use: easy, medium, or hard"
        )
        raise typer.Exit(1)

    if output_path.exists():
        if force:
            shutil.rmtree(output_path)
        else:
            console.print(
                f"[red]Error:[/red] Directory already exists: {output_path}\n"
                "Use --force to overwrite"
            )
            raise typer.Exit(1)

    with console.status("[bold cyan]Generating treasure hunt...", spinner="dots"):
        result = generate_treasure_hunt(
            base_path=str(output_path),
            difficulty=difficulty,
            seed=seed,
        )

    console.print()
    console.print(display_hunt_info(result, output_path))
    console.print()
    console.print(
        f"[green]Run with:[/green] treasure-hunt run {output_path}"
    )


@app.command()
def quick(
    difficulty: str = typer.Option(
        "easy",
        "--difficulty",
        "-d",
        help="Difficulty level: easy, medium, or hard",
    ),
    model: str = typer.Option(
        "gemini-2.5-flash",
        "--model",
        "-m",
        help="Gemini model to use",
    ),
    max_turns: int = typer.Option(
        50,
        "--max-turns",
        "-t",
        help="Maximum number of turns",
    ),
    seed: Optional[int] = typer.Option(
        None,
        "--seed",
        "-s",
        help="Random seed for reproducibility",
    ),
    keep: bool = typer.Option(
        False,
        "--keep",
        "-k",
        help="Keep the treasure hunt directory after completion",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--batch",
        "-i/-b",
        help="Run interactively or in batch mode",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="GOOGLE_API_KEY",
        help="Google API key (or set GOOGLE_API_KEY env var)",
    ),
):
    """
    Generate and immediately run a treasure hunt.

    Combines 'generate' and 'run' into a single command for quick testing.
    """
    if not api_key:
        console.print(
            "[red]Error:[/red] No API key provided. "
            "Set GOOGLE_API_KEY or use --api-key",
            style="bold",
        )
        raise typer.Exit(1)

    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())
    hunt_path = temp_dir / "treasure_hunt"

    try:
        # Generate
        with console.status("[bold cyan]Generating treasure hunt...", spinner="dots"):
            hunt_result = generate_treasure_hunt(
                base_path=str(hunt_path),
                difficulty=difficulty,
                seed=seed,
            )

        console.print()
        console.print(display_hunt_info(hunt_result, hunt_path))
        console.print()

        # Create agent
        with console.status("[bold cyan]Creating agent...", spinner="dots"):
            agent = create_agent(model, api_key)

        # Create game
        game = TreasureHuntGame(
            hunt_path=str(hunt_path),
            agent=agent,
            max_turns=max_turns,
        )

        treasure_key = hunt_result["treasure_key"]

        if interactive:
            console.print("[bold cyan]Starting hunt...[/bold cyan]\n")

            while True:
                with console.status(
                    f"[bold cyan]Turn {game.state.turn_number + 1}...",
                    spinner="dots",
                ):
                    turn_result = game.take_turn()

                console.print(display_turn(turn_result))

                if turn_result.needs_human_input:
                    console.print()
                    console.print(
                        f"[bold yellow]Agent asks:[/bold yellow] "
                        f"{turn_result.pending_question}"
                    )
                    response = console.input("[bold]Your response:[/bold] ")
                    console.print()

                    with console.status(
                        "[bold cyan]Processing response...", spinner="dots"
                    ):
                        turn_result = game.take_turn(human_input=response)
                    console.print(display_turn(turn_result))

                if turn_result.game_over:
                    break

            console.print()
            console.print(display_game_result(turn_result.game_result, treasure_key))

        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Running treasure hunt...", total=None)
                result = game.run()
                progress.update(task, completed=True)

            console.print()
            console.print(display_game_result(result, treasure_key))

        if keep:
            console.print(f"\n[dim]Hunt kept at: {hunt_path}[/dim]")

    finally:
        if not keep:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    app()
