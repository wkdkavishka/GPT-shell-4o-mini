"""
User profile management functions for GPT-shell-4o-mini.

This module handles static user profile collection, storage, and formatting.
"""

import json
import platform
import getpass
from pathlib import Path

# Configuration
USER_PROFILE_FILE = Path.home() / ".chatgpt_py_info"


def collect_user_profile():
    """Collect static user profile information."""
    profile = {
        "username": getpass.getuser(),
        "os": platform.system(),
    }

    # Add Linux distribution if applicable
    if profile["os"] == "Linux":
        try:
            import distro

            profile["distro"] = distro.name(pretty=True)
        except ImportError:
            try:
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            profile["distro"] = line.split("=")[1].strip().strip('"')
                            break
            except:
                profile["distro"] = "Unknown Linux"

    return profile


def save_user_profile(profile):
    """Save user profile to file."""
    try:
        with open(USER_PROFILE_FILE, "w") as f:
            json.dump(profile, f, indent=2)
        return True
    except Exception:
        return False


def load_user_profile():
    """Load user profile from file, create if doesn't exist."""
    if not USER_PROFILE_FILE.exists():
        # Create profile if it doesn't exist
        profile = collect_user_profile()
        save_user_profile(profile)
        return profile

    try:
        with open(USER_PROFILE_FILE, "r") as f:
            return json.load(f)
    except:
        # If file is corrupted, recreate it
        profile = collect_user_profile()
        save_user_profile(profile)
        return profile


def format_user_profile():
    """Format static profile as string."""
    profile = load_user_profile()
    if not profile:
        return ""

    parts = [
        f"User: {profile.get('username', 'unknown')}",
        f"OS: {profile.get('os', 'unknown')}",
    ]

    if profile.get("distro"):
        parts.append(f"Distro: {profile['distro']}")

    return "[Static Profile: " + " | ".join(parts) + "]"
