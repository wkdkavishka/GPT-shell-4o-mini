"""
Initial checks and setup functions for GPT-shell-4o-mini.

This module handles API key verification, first-time setup wizard,
and environment variable configuration.
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path
from rich.console import Console

# Configuration
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
USER_PROFILE_FILE = Path.home() / ".chatgpt_py_info"

console = Console()


def verify_api_key(api_key):
    """Verify that an OpenAI API key is valid by making a test request."""
    try:
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )

        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                return True
        return False
    except Exception:
        return False


def update_shell_profile(api_key):
    """Add or update the OPENAI_KEY in the user's shell profile or system."""
    import platform

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


def first_run_setup():
    """Interactive setup wizard for first-time users."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Welcome to GPT-shell-4o-mini![/bold cyan]")
    console.print("=" * 60)
    console.print("\nIt looks like you haven't set up your OpenAI API key yet.")
    console.print("\n[bold]Where to get an API key:[/bold]")
    console.print("  https://platform.openai.com/account/api-keys")
    console.print("\n" + "=" * 60 + "\n")

    try:
        user_input = (
            console.input("[bold]Do you have an OpenAI API key? (yes/no):[/bold] ")
            .strip()
            .lower()
        )

        if user_input not in ["yes", "y"]:
            console.print("\n[yellow]Please get an API key from:[/yellow]")
            console.print("  https://platform.openai.com/account/api-keys")
            console.print(
                "\n[cyan]After getting your key, run 'gpt' again to set it up.[/cyan]\n"
            )
            sys.exit(0)

        api_key = console.input("\n[bold]Enter your OpenAI API key:[/bold] ").strip()

        if not api_key:
            console.print("[red]Error:[/red] No API key provided.")
            sys.exit(1)

        console.print("\n[cyan]Verifying API key...[/cyan]")

        if not verify_api_key(api_key):
            console.print("[red]Error:[/red] Invalid API key or unable to verify.")
            console.print("Please check your key and try again.\n")
            sys.exit(1)

        console.print("[green]✓[/green] API key verified successfully!")

        # Update shell profile
        console.print("\n[cyan]Saving API key to your shell profile...[/cyan]")
        profile_saved = update_shell_profile(api_key)

        # Import here to avoid circular imports
        from .user_profile import collect_user_profile, save_user_profile

        # Collect and save user profile
        console.print("\n[cyan]Setting up your profile...[/cyan]")
        profile = collect_user_profile()

        # Allow username customization
        console.print(f"\n[bold]Detected username:[/bold] {profile['username']}")
        custom_name = console.input(
            "[bold]Press Enter to use this, or type a different name:[/bold] "
        ).strip()

        if custom_name:
            profile["username"] = custom_name

        # Save profile
        if save_user_profile(profile):
            console.print(f"\n[green]✓[/green] Profile saved:")
            console.print(f"  Username: {profile['username']}")
            console.print(f"  OS: {profile['os']}")
            if "distro" in profile:
                console.print(f"  Distribution: {profile['distro']}")

        if profile_saved:
            console.print("\n[green]✓[/green] Setup complete!")
            console.print("\n[bold]Important:[/bold] For the key to be available, run:")
            console.print(
                "  [cyan]source ~/.bashrc[/cyan]  (or your shell's config file)"
            )
            console.print(
                "\nOr restart your terminal, then run '[cyan]gpt[/cyan]' again.\n"
            )
        else:
            console.print(
                "\n[yellow]Setup complete, but you'll need to manually add the key.[/yellow]\n"
            )

        sys.exit(0)

    except (EOFError, KeyboardInterrupt):
        console.print("\n\n[yellow]Setup cancelled.[/yellow]\n")
        sys.exit(0)


def check_api_key():
    """Check if API key is available, run setup if not."""
    global API_KEY
    if not API_KEY:
        # Run first-time setup wizard
        first_run_setup()
        # If we get here, setup was cancelled or failed
        sys.exit(1)
    return API_KEY
