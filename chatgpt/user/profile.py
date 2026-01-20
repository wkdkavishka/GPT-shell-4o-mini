"""
User profile management functions for GPT-shell-4o-mini.
"""

import os
import json
import platform
import getpass
from pathlib import Path

# Import project modules
from ..core.config import USER_PROFILE_FILE


def collect_user_profile():
    """Collect static user profile information (done once during setup)."""
    profile = {
        "username": getpass.getuser(),
        "os": platform.system(),
        "os_version": platform.version(),
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
    """Load user profile from file."""
    if not USER_PROFILE_FILE.exists():
        return None

    try:
        with open(USER_PROFILE_FILE, "r") as f:
            return json.load(f)
    except:
        return None


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

    if profile.get("os_version"):
        parts.append(f"Version: {profile['os_version']}")

    return "[Static Profile: " + " | ".join(parts) + "]"
