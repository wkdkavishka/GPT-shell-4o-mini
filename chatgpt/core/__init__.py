"""
Core module for GPT-shell-4o-mini.

Contains initialization, API interactions, and configuration.
"""

from .config import *
from .initialization import validate_setup, first_run_setup
from .api import *

__all__ = [
    # Configuration
    "HISTORY_FILE",
    "USER_PROFILE_FILE",
    "DEFAULT_MODEL",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_IMAGE_SIZE",
    "MAX_CONTEXT_MESSAGES",
    "COMMAND_GENERATION_PROMPT",
    "get_chat_init_prompt",
    "get_system_prompt",
    # Initialization
    "validate_setup",
    "first_run_setup",
    "verify_api_key",
    # API
    "list_models",
    "get_model_details",
    "generate_image",
    "get_chat_completion",
    "handle_api_error",
]
