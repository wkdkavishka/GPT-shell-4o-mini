"""
OS-specific module for GPT-shell-4o-mini.

Contains terminal context, environment setup, and platform utilities.
"""

from .terminal import *
from .environment import *
from .platform import *

__all__ = [
    # Terminal context
    "capture_tmux_session",
    "capture_screen_session",
    "get_shell_history",
    "get_current_shell",
    "clean_terminal_output",
    "get_terminal_session",
    "format_terminal_session",
    # Environment setup
    "update_shell_profile",
    # Platform utilities
    "get_platform_info",
]
