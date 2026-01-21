"""
Terminal context capture functions for GPT-shell-4o-mini.

This module handles capturing terminal session data from various sources
like tmux, screen, and shell history.
"""

import os
import subprocess
import platform
import tempfile
import re
from pathlib import Path


def capture_tmux_session(lines=30):
    """Capture recent lines from current tmux pane."""
    try:
        if os.environ.get("TMUX"):
            result = subprocess.run(
                ["tmux", "capture-pane", "-p", "-S", f"-{lines}"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return result.stdout
    except Exception:
        pass
    return None


def capture_screen_session():
    """Capture from GNU screen."""
    try:
        if os.environ.get("STY"):
            with tempfile.NamedTemporaryFile(
                mode="w+", delete=False, suffix=".txt"
            ) as f:
                temp_file = f.name

            subprocess.run(["screen", "-X", "hardcopy", temp_file], timeout=2)

            if os.path.exists(temp_file):
                with open(temp_file, "r") as f:
                    content = f.read()
                os.unlink(temp_file)
                return content
    except Exception:
        pass
    return None


def get_shell_history(max_commands=5):
    """Get recent shell commands from history."""
    history = []

    try:
        if platform.system() == "Windows":
            # PowerShell history
            ps_history = (
                Path.home()
                / "AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt"
            )
            if ps_history.exists():
                with open(ps_history, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    history = [
                        line.strip() for line in lines[-max_commands:] if line.strip()
                    ]
        else:
            # Try bash history
            bash_history = Path.home() / ".bash_history"
            if bash_history.exists():
                with open(bash_history, "r") as f:
                    lines = f.readlines()
                    history = [
                        line.strip() for line in lines[-max_commands:] if line.strip()
                    ]

            # Try zsh history if bash not found
            elif (Path.home() / ".zsh_history").exists():
                zsh_history = Path.home() / ".zsh_history"
                with open(zsh_history, "rb") as f:
                    content = f.read().decode("utf-8", errors="ignore")
                    lines = content.split("\n")
                    # zsh history format: : timestamp:0;command
                    history = []
                    for line in lines[-max_commands:]:
                        if ";" in line:
                            cmd = line.split(";", 1)[1].strip()
                            if cmd:
                                history.append(cmd)
                        elif line.strip() and not line.startswith(":"):
                            history.append(line.strip())
    except Exception:
        pass

    return history


def get_current_shell():
    """Detect current shell."""
    if platform.system() == "Windows":
        if os.environ.get("PSModulePath"):
            return "PowerShell"
        return "cmd"

    shell_path = os.environ.get("SHELL", "")
    return shell_path.split("/")[-1] if shell_path else "unknown"


def clean_terminal_output(text):
    """Remove ANSI color codes and clean up terminal output."""
    import re

    # More comprehensive ANSI escape sequence pattern
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    text = ansi_escape.sub("", text)

    # Remove carriage returns that mess up display
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Limit to avoid token limits (last 2000 chars)
    if len(text) > 2000:
        text = "...(truncated)\n" + text[-2000:]

    return text


def get_terminal_session(max_lines=300):
    """
    Capture recent terminal session (commands + outputs).
    Tries multiple methods in order.
    Returns: (method_name, session_text)
    """

    # Try tmux first (most common for developers)
    session = capture_tmux_session(lines=max_lines)
    if session:
        return ("tmux", session)

    # Try screen
    session = capture_screen_session()
    if session:
        return ("screen", session)

    # Fallback: command history only (no outputs)
    history = get_shell_history(max_commands=5)
    if history:
        return ("history", "\n".join([f"$ {cmd}" for cmd in history]))

    return (None, None)


def format_terminal_session():
    """Format terminal session as context string."""
    try:
        method, session = get_terminal_session(max_lines=300)

        if not session:
            return ""

        # Clean the output
        session = clean_terminal_output(session)

        # Build terminal session info
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

        # Format as separate components
        terminal_session = f"[Terminal Session: ({terminal_info})]"
        terminal_history = f"[Terminal History: ({session})]"

        return f"{terminal_session}\n{terminal_history}"
    except Exception:
        # Silently fail if context collection fails
        return ""
