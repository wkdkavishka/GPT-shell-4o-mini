"""
Initialization and setup functions for GPT-shell-4o-mini.

Handles first-run setup, validation, and configuration management.
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path

# Import required modules
try:
    import requests
except ImportError:
    print(
        "Error: 'requests' library not found. Please install it: pip install requests",
        file=sys.stderr,
    )
    sys.exit(1)

# Import project modules
from ..user.profile import collect_user_profile, save_user_profile, load_user_profile
from ..os_specific.environment import update_shell_profile


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


def validate_setup(api_key):
    """
    Comprehensive setup validation for every run.

    Returns a list of missing components (empty list means everything is valid).
    """
    issues = []

    # Check API key
    if not api_key or not verify_api_key(api_key):
        issues.append("api_key")

    # Check user profile
    profile = load_user_profile()
    if not profile or not all(k in profile for k in ["username", "os"]):
        issues.append("profile")

    # Check system info completeness
    if profile and profile.get("os") == "Linux" and not profile.get("distro"):
        issues.append("system_info")

    return issues


def first_run_setup(target_issues=None, console=None):
    """
    Interactive setup wizard for first-time users or for fixing missing components.

    Args:
        target_issues: List of specific issues to fix. If None, runs full setup.
        console: Rich console instance. If None, creates a new one.
    """
    # Import console only when needed to avoid circular imports
    if console is None:
        from rich.console import Console

        console = Console()

    full_setup = target_issues is None

    console.print("\n" + "=" * 60)
    if full_setup:
        console.print("[bold cyan]Welcome to GPT-shell-4o-mini![/bold cyan]")
    else:
        console.print("[bold cyan]GPT-shell-4o-mini Setup[/bold cyan]")
    console.print("=" * 60)

    # Determine what needs to be set up
    setup_api_key = full_setup or "api_key" in target_issues
    setup_profile = (
        full_setup or "profile" in target_issues or "system_info" in target_issues
    )

    # API Key Setup
    if setup_api_key:
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

            api_key = console.input(
                "\n[bold]Enter your OpenAI API key:[/bold] "
            ).strip()

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
            profile_saved = update_shell_profile(api_key, console=console)

            if profile_saved:
                console.print("\n[green]✓[/green] API key saved successfully!")
                console.print(
                    "\n[bold]Important:[/bold] For the key to be available, run:"
                )
                console.print(
                    "  [cyan]source ~/.bashrc[/cyan]  (or your shell's config file)"
                )
                console.print(
                    "\nOr restart your terminal, then run '[cyan]gpt[/cyan]' again.\n"
                )
            else:
                console.print(
                    "\n[yellow]API key setup complete, but you'll need to manually add it.[/yellow]\n"
                )

        except (EOFError, KeyboardInterrupt):
            console.print("\n\n[yellow]Setup cancelled.[/yellow]\n")
            sys.exit(0)

    # User Profile Setup
    if setup_profile:
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
            if "os_version" in profile:
                console.print(f"  Version: {profile['os_version']}")

    if full_setup:
        console.print("\n[green]✓[/green] Setup complete!")
        console.print("\nYou can now run '[cyan]gpt[/cyan]' to start using ChatGPT.\n")

    # Exit after setup to ensure environment variables are properly loaded
    if setup_api_key:
        sys.exit(0)
