"""
Security utilities for GPT-shell-4o-mini.
"""

import re


def is_dangerous(command):
    """Checks if a command contains potentially dangerous patterns."""
    # Basic checks, similar to the bash script but can be expanded
    dangerous_patterns = [
        "rm ",
        ">",
        "mv ",
        "mkfs",
        ":(){:|:&};",
        "dd ",
        "chmod ",
        "wget ",
        "curl ",
    ]

    # Check common redirection/overwriting patterns more carefully
    if ">" in command and not command.strip().endswith(" > /dev/null"):
        if not command.strip().endswith((">>", "2>", "1>", "&>")):
            # Check if '>' is followed by a space and a potential filename
            if " > " in command or ">" == command.strip()[-1]:
                return True

    # Check for patterns explicitly
    for pattern in dangerous_patterns:
        if pattern in command:
            # Avoid false positives like 'curl --help' vs 'curl http...'
            if pattern in ["wget ", "curl "]:
                # Simple check: is there likely a URL or option after it?
                parts = command.split(pattern, 1)
                if (
                    len(parts) > 1
                    and parts[1].strip()
                    and not parts[1].strip().startswith("-")
                ):
                    return True
            else:
                return True
    return False


def validate_command(command):
    """
    Validate a command for safety.
    Returns a tuple of (is_safe, reason)
    """
    if not command or not command.strip():
        return False, "Empty command"

    command = command.strip()

    # Check for extremely dangerous patterns
    extremely_dangerous = [
        r"rm\s+-rf\s+/",
        r":\(\)\{\s*\|\s*:\s*&\s*\}\s*;",
        r"dd\s+if=/dev/zero",
        r"mkfs\.",
        r"format\s+",
        r"fdisk\s+",
    ]

    for pattern in extremely_dangerous:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Extremely dangerous command pattern detected: {pattern}"

    # Check for potentially dangerous patterns
    if is_dangerous(command):
        return False, "Potentially dangerous command detected"

    return True, "Command appears safe"


def sanitize_input(text):
    """
    Sanitize user input to prevent injection attacks.
    This is a basic implementation - you may want to enhance it based on your needs.
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace("\x00", "")

    # Limit length to prevent DoS
    if len(text) > 10000:
        text = text[:10000] + "...(truncated)"

    return text


def is_safe_filename(filename):
    """Check if a filename is safe for filesystem operations."""
    if not filename:
        return False

    # Check for dangerous characters
    dangerous_chars = ["..", "/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in dangerous_chars:
        if char in filename:
            return False

    # Check for reserved names (Windows)
    reserved_names = [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    ]

    if filename.upper() in reserved_names:
        return False

    return True
