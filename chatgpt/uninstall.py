"""
Uninstall command for GPT-shell-4o-mini.

This module provides a command-line uninstaller that can be called via:
gpt-remove or python -m chatgpt.uninstall
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from rich.console import Console

console = Console()

# Files created by the package
FILES_TO_REMOVE = [
    "~/.chatgpt_py_info",  # User profile
    "~/.chatgpt_py_history",  # Chat history
    "~/.chatgpt_py_sys_prompt",  # Custom system prompt
]

# Shell profiles that might contain OPENAI_KEY
SHELL_PROFILES = [
    "~/.bashrc",
    "~/.zprofile",
    "~/.zshrc",
    "~/.bash_profile",
    "~/.profile",
]


def remove_file(file_path):
    """Remove a single file if it exists."""
    path = Path(file_path).expanduser()
    if path.exists():
        try:
            path.unlink()
            console.print(f"[green]✓[/green] Removed {file_path}")
            return True
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to remove {file_path}: {e}")
            return False
    else:
        console.print(f"[yellow]-[/yellow] {file_path} not found")
        return False


def remove_openai_key_from_profiles():
    """Remove OPENAI_KEY from shell profile files."""
    system = platform.system()

    if system == "Windows":
        # Remove Windows environment variable
        try:
            result = subprocess.run(
                ["reg", "delete", "HKCU\\Environment", "/v", "OPENAI_KEY", "/f"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                console.print(
                    "[green]✓[/green] Removed OPENAI_KEY from Windows environment"
                )
            else:
                console.print(
                    "[yellow]-[/yellow] OPENAI_KEY not found in Windows environment"
                )
        except Exception as e:
            console.print(
                f"[red]✗[/red] Failed to remove Windows environment variable: {e}"
            )
    else:
        # Unix-like systems - remove from shell profiles
        for profile_file in SHELL_PROFILES:
            profile_path = Path(profile_file).expanduser()
            if profile_path.exists():
                try:
                    with profile_path.open("r") as f:
                        lines = f.readlines()

                    # Filter out lines containing OPENAI_KEY for our package
                    filtered_lines = []
                    key_removed = False
                    in_our_section = False

                    for line in lines:
                        if "# OpenAI API Key for GPT-shell-4o-mini" in line:
                            in_our_section = True
                            key_removed = True
                            continue
                        elif in_our_section and line.strip().startswith(
                            "export OPENAI_KEY="
                        ):
                            continue  # Skip the export line
                        elif in_our_section and line.strip() == "":
                            in_our_section = False  # End of our section
                            continue
                        elif in_our_section:
                            continue  # Skip any other lines in our section

                        filtered_lines.append(line)

                    if key_removed:
                        with profile_path.open("w") as f:
                            f.writelines(filtered_lines)
                        console.print(
                            f"[green]✓[/green] Removed OPENAI_KEY from {profile_file}"
                        )
                    else:
                        console.print(
                            f"[yellow]-[/yellow] OPENAI_KEY not found in {profile_file}"
                        )

                except Exception as e:
                    console.print(f"[red]✗[/red] Failed to update {profile_file}: {e}")


def uninstall_package():
    """Uninstall the Python package via pip."""
    try:
        console.print(
            "[cyan]Attempting to uninstall gpt-shell-4o-mini package...[/cyan]"
        )
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "gpt-shell-4o-mini", "-y"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✓[/green] Package uninstalled successfully")
            return True
        else:
            console.print("[yellow]-[/yellow] Package not found or already uninstalled")
            return False
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to uninstall package: {e}")
        return False


def main():
    """Main uninstall function."""
    console.print("\n" + "=" * 60)
    console.print("[bold red]GPT-shell-4o-mini Uninstaller[/bold red]")
    console.print("=" * 60)
    console.print("\nThis will remove:")
    console.print("• The gpt-shell-4o-mini Python package")
    console.print("• All configuration files in your home directory")
    console.print("• OPENAI_KEY from your shell profiles")
    console.print("• Chat history and custom prompts\n")

    # Confirmation
    try:
        confirm = (
            console.input(
                "[bold red]Are you sure you want to continue? (yes/no):[/bold red] "
            )
            .strip()
            .lower()
        )
        if confirm not in ["yes", "y"]:
            console.print("[yellow]Uninstall cancelled.[/yellow]")
            sys.exit(0)
    except (EOFError, KeyboardInterrupt):
        console.print("\n[yellow]Uninstall cancelled.[/yellow]")
        sys.exit(0)

    console.print("\n[cyan]Starting uninstall process...[/cyan]\n")

    # 1. Remove configuration files first (while package is still installed)
    console.print("[cyan]Removing configuration files...[/cyan]")
    files_removed = 0
    for file_path in FILES_TO_REMOVE:
        if remove_file(file_path):
            files_removed += 1

    # 2. Remove environment variables
    console.print("\n[cyan]Removing environment variables...[/cyan]")
    remove_openai_key_from_profiles()

    # 3. Uninstall package last
    console.print("\n[cyan]Uninstalling Python package...[/cyan]")
    package_removed = uninstall_package()

    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold green]Uninstall Complete![/bold green]")
    console.print("=" * 60)

    if files_removed > 0:
        console.print(f"✓ {files_removed} configuration files removed")
    console.print("✓ Environment variables cleaned")
    if package_removed:
        console.print("✓ Python package removed")

    console.print("\n[yellow]Note:[/yellow] You may need to:")
    console.print("• Restart your terminal to clear environment variables")
    console.print("• Run 'source ~/.bashrc' (or your shell config) to reload")

    console.print("\n[green]Thank you for using GPT-shell-4o-mini![/green]\n")

    # Self-delete the uninstall script
    try:
        import __main__

        script_path = Path(__main__.__file__)
        if script_path.exists():
            script_path.unlink()
            console.print(f"[green]✓[/green] Removed uninstall script: {script_path}")
    except:
        pass  # Silent fail if can't delete self


if __name__ == "__main__":
    main()
