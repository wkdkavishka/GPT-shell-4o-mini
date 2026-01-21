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


# def get_terminal_session(max_lines=300):
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

    # Try to capture from current terminal using script command
    try:
        # This captures recent terminal output by running script briefly
        import tempfile
        import subprocess
        import time

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp_path = tmp.name

        # Run script command briefly to capture terminal buffer
        try:
            # Use script to capture terminal output with better options
            result = subprocess.run(
                ["script", "-q", "-c", "exit", tmp_path],
                capture_output=True,
                text=True,
                timeout=3,
            )
            time.sleep(0.2)  # Brief pause

            # Read the captured content
            with open(tmp_path, "r") as f:
                content = f.read()

            if content.strip():
                lines = content.strip().split("\n")
                # Get last max_lines, excluding the exit command and script artifacts
                relevant_lines = []
                for line in lines[-max_lines - 5 :]:
                    # Skip script-related lines and empty lines
                    if (
                        line.strip()
                        and "Script started" not in line
                        and "Script done" not in line
                        and "exit" not in line.lower()
                        and not line.startswith("[")
                        and len(line.strip()) > 0
                    ):
                        relevant_lines.append(line)

                if relevant_lines:
                    return ("script", "\n".join(relevant_lines[-max_lines:]))
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ):
            pass
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
    except Exception:
        pass

    # Fallback: command history only (no outputs) - get more commands
    history = get_shell_history(max_commands=50)  # Increased from 5 to 50
    if history:
        return ("history", "\n".join([f"$ {cmd}" for cmd in history]))

    return (None, None)


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
