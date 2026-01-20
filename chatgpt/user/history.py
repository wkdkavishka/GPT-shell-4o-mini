"""
Chat history management functions for GPT-shell-4o-mini.
"""

import os
from datetime import datetime
from pathlib import Path

# Import project modules
from ..core.config import HISTORY_FILE


def append_history(prompt, response):
    """Appends interaction to the history file."""
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            f.write(f"{timestamp} User: {prompt}\n")
            f.write(f"{timestamp} Assistant: {response}\n\n")
    except IOError as e:
        # Import console only when needed to avoid circular imports
        from rich.console import Console

        console = Console()
        console.print(
            f"[yellow]Warning:[/yellow] Could not write to history file {HISTORY_FILE}: {e}"
        )


def display_history():
    """Displays the chat history."""
    # Import console only when needed to avoid circular imports
    from rich.console import Console

    console = Console()

    if not HISTORY_FILE.exists():
        console.print("[yellow]History file not found.[/yellow]")
        return
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            console.print(f.read())
    except IOError as e:
        console.print(f"[red]Error reading history file {HISTORY_FILE}: {e}[/red]")
