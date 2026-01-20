"""
General helper functions for GPT-shell-4o-mini.
"""

import os
from pathlib import Path


def safe_file_read(file_path, encoding="utf-8"):
    """Safely read a file with error handling."""
    try:
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()
    except (IOError, OSError, UnicodeDecodeError) as e:
        return None


def safe_file_write(file_path, content, encoding="utf-8"):
    """Safely write content to a file with error handling."""
    try:
        # Create parent directories if they don't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except (IOError, OSError) as e:
        return False


def format_error_message(error_type, details):
    """Format a standardized error message."""
    return f"[{error_type}] {details}"


def truncate_text(text, max_length=2000, suffix="...(truncated)"):
    """Truncate text to a maximum length with a suffix."""
    if len(text) <= max_length:
        return text
    return suffix + "\n" + text[-(max_length - len(suffix)) :]


def ensure_directory_exists(directory_path):
    """Ensure a directory exists, creating it if necessary."""
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except (IOError, OSError):
        return False


def get_file_size(file_path):
    """Get the size of a file in bytes."""
    try:
        return os.path.getsize(file_path)
    except (IOError, OSError):
        return 0


def is_executable(command):
    """Check if a command is executable in the system PATH."""
    import shutil

    return shutil.which(command) is not None
