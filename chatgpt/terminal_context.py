"""
Terminal context capture functions for GPT-shell-4o-mini.

This module handles capturing terminal session data from various sources
like tmux, screen, and shell history.
"""

import os
import platform
from pathlib import Path


def get_current_shell():
    """Detect current shell."""
    if platform.system() == "Windows":
        if os.environ.get("PSModulePath"):
            return "PowerShell"
        return "cmd"

    shell_path = os.environ.get("SHELL", "")
    return shell_path.split("/")[-1] if shell_path else "unknown"


def format_terminal_session():
    """Format terminal session as context string."""
    try:
        # Build terminal session info only (no history)
        parts = [
            f"Shell: {get_current_shell()}",
            f"CWD: {os.getcwd()}",
            f"User: {os.getenv('USER', os.getenv('USERNAME', 'unknown'))}",
            f"Home: {Path.home()}",
        ]

        # Add environment info
        if os.getenv("VIRTUAL_ENV"):
            parts.append(f"VEnv: {os.path.basename(os.getenv('VIRTUAL_ENV'))}")

        if os.getenv("CONDA_DEFAULT_ENV"):
            parts.append(f"Conda: {os.getenv('CONDA_DEFAULT_ENV')}")

        terminal_info = " | ".join(parts)

        # Format as terminal session info only
        return f"[Terminal Session: ({terminal_info})]"
    except Exception:
        # Silently fail if context collection fails
        return ""
