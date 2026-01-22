"""
Automatic cleanup module for GPT-shell-4o-mini.

This module registers an atexit handler that detects when the package
is being uninstalled and automatically cleans up all files and environment variables.
"""

import os
import sys
import subprocess
import platform
import atexit
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
            return True
        except Exception:
            return False
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
            return result.returncode == 0
        except Exception:
            return False
    else:
        # Unix-like systems - remove from shell profiles
        key_removed = False
        for profile_file in SHELL_PROFILES:
            profile_path = Path(profile_file).expanduser()
            if profile_path.exists():
                try:
                    with profile_path.open("r") as f:
                        lines = f.readlines()

                    # Filter out lines containing OPENAI_KEY for our package
                    filtered_lines = []
                    local_key_removed = False
                    in_our_section = False

                    for line in lines:
                        if "# OpenAI API Key for GPT-shell-4o-mini" in line:
                            in_our_section = True
                            local_key_removed = True
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

                    if local_key_removed:
                        with profile_path.open("w") as f:
                            f.writelines(filtered_lines)
                        key_removed = True

                except Exception:
                    continue

        return key_removed


def cleanup_on_uninstall():
    """Cleanup function called during package uninstall."""
    # Only run if we're being uninstalled (not on normal exit)
    if not hasattr(sys, "real_prefix") and not (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        # Check if the package directory still exists
        package_dir = Path(__file__).parent.parent
        if not package_dir.exists():
            # Package is being uninstalled, run cleanup
            try:
                # Remove configuration files
                files_removed = 0
                for file_path in FILES_TO_REMOVE:
                    if remove_file(file_path):
                        files_removed += 1

                # Remove environment variables
                remove_openai_key_from_profiles()

                # Print cleanup message (only if we can)
                try:
                    console.print(
                        f"\n[cyan]GPT-shell-4o-mini cleanup: Removed {files_removed} config files[/cyan]"
                    )
                except:
                    pass  # Silent fail if console not available

            except Exception:
                pass  # Silent fail on any errors


def register_cleanup():
    """Register the cleanup function to run on package uninstall."""
    atexit.register(cleanup_on_uninstall)


# Register cleanup when module is imported
register_cleanup()
