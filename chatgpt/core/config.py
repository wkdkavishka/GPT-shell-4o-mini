"""
Configuration constants and functions for GPT-shell-4o-mini.
"""

import os
from pathlib import Path
from datetime import datetime

# --- File Paths ---
HISTORY_FILE = Path.home() / ".chatgpt_py_history"
USER_PROFILE_FILE = Path.home() / ".chatgpt_py_info"

# --- Default Settings ---
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1024
DEFAULT_IMAGE_SIZE = "512x512"

# --- Context Management ---
MAX_CONTEXT_MESSAGES = (
    10  # Max number of user/assistant message pairs to keep in context
)

# --- Prompts ---
COMMAND_GENERATION_PROMPT = "You are a Command Line Interface expert and your task is to provide functioning shell commands. Return a CLI command and nothing else - do not send it in a code block, quotes, or anything else, just the pure text CONTAINING ONLY THE COMMAND. If possible, return a one-line bash command or chain many commands together. Return ONLY the command ready to run in the terminal. The command should do the following:"


def get_chat_init_prompt():
    """Get the initial chat prompt with dynamic date."""
    return f"You are ChatGPT, a Large Language Model trained by OpenAI. You answer as concisely as possible for each response (e.g. don't be verbose). If you are generating a list, do not have too many items. Keep the number of items short. Before each user prompt you will be given the chat history in Q&A form. Output your answer directly, with no labels in front. Do not start your answers with A or Anwser. Today's date is {datetime.now().strftime('%m/%d/%Y')}"


def get_system_prompt():
    """Get the system prompt with dynamic date."""
    return f"You are ChatGPT, a large language model trained by OpenAI. Answer as concisely as possible. Current date: {datetime.now().strftime('%m/%d/%Y')}."
