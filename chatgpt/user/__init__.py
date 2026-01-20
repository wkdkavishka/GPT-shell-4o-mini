"""
User module for GPT-shell-4o-mini.

Contains user profile and history management functions.
"""

from .profile import *
from .history import *

__all__ = [
    # Profile management
    "collect_user_profile",
    "save_user_profile",
    "load_user_profile",
    "format_user_profile",
    # History management
    "append_history",
    "display_history",
]
