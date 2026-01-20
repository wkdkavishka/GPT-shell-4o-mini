"""
Environment variable setup functions for GPT-shell-4o-mini.
"""

import os
import subprocess
import platform
from pathlib import Path


def update_shell_profile(api_key, console=None):
    """Add or update the OPENAI_KEY in the user's shell profile or system."""
    # Import console only when needed to avoid circular imports
    if console is None:
        from rich.console import Console

        console = Console()

    system = platform.system()

    if system == "Windows":
        # Windows: Use setx to set user environment variable
        try:
            subprocess.run(
                ["setx", "OPENAI_KEY", api_key], check=True, capture_output=True
            )
            # Also set for current session
            os.environ["OPENAI_KEY"] = api_key
            console.print(
                f"[green]✓[/green] Added OPENAI_KEY to Windows environment variables"
            )
            console.print(
                f"[yellow]Note:[/yellow] Restart your terminal for the change to take effect"
            )
            return True
        except Exception as e:
            console.print(
                f"[yellow]Warning:[/yellow] Could not set environment variable: {e}"
            )
            console.print(
                f"[yellow]Please manually set OPENAI_KEY in System Settings[/yellow]"
            )
            return False

    else:  # macOS or Linux
        # Existing Unix shell profile logic
        profile_paths = [
            Path.home() / ".bashrc",
            Path.home() / ".zprofile",
            Path.home() / ".zshrc",
            Path.home() / ".bash_profile",
            Path.home() / ".profile",
        ]

        for profile_path in profile_paths:
            if profile_path.exists():
                try:
                    with profile_path.open("r") as f:
                        content = f.read()

                    if "export OPENAI_KEY" not in content:
                        with profile_path.open("a") as f:
                            f.write(f"\n# OpenAI API Key for GPT-shell-4o-mini\n")
                            f.write(f"export OPENAI_KEY={api_key}\n")
                        console.print(
                            f"[green]✓[/green] Added OPENAI_KEY to {profile_path}"
                        )
                        return True
                    else:
                        console.print(
                            f"[yellow]![/yellow] OPENAI_KEY already exists in {profile_path}"
                        )
                        return True
                except Exception as e:
                    console.print(
                        f"[yellow]Warning:[/yellow] Could not update {profile_path}: {e}"
                    )
                    continue

        # If no profile found
        console.print("[yellow]Warning:[/yellow] No shell profile found.")
        console.print(f"[yellow]Please manually add to your shell config:[/yellow]")
        console.print(f"  export OPENAI_KEY={api_key}")
        return False
