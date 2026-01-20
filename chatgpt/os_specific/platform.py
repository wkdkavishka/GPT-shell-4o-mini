"""
Platform-specific utilities for GPT-shell-4o-mini.
"""

import platform
import os


def get_platform_info():
    """Get comprehensive platform information."""
    info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }

    # Add Linux distribution if applicable
    if info["system"] == "Linux":
        try:
            import distro

            info["distro"] = distro.name(pretty=True)
            info["distro_id"] = distro.id()
            info["distro_version"] = distro.version()
        except ImportError:
            try:
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            info["distro"] = line.split("=")[1].strip().strip('"')
                        elif line.startswith("ID="):
                            info["distro_id"] = line.split("=")[1].strip().strip('"')
                        elif line.startswith("VERSION_ID="):
                            info["distro_version"] = (
                                line.split("=")[1].strip().strip('"')
                            )
            except:
                info["distro"] = "Unknown Linux"

    return info


def is_windows():
    """Check if running on Windows."""
    return platform.system().lower() == "windows"


def is_macos():
    """Check if running on macOS."""
    return platform.system().lower() == "darwin"


def is_linux():
    """Check if running on Linux."""
    return platform.system().lower() == "linux"


def get_shell_type():
    """Get the current shell type."""
    if is_windows():
        if os.environ.get("PSModulePath"):
            return "PowerShell"
        return "cmd"

    shell_path = os.environ.get("SHELL", "")
    return shell_path.split("/")[-1] if shell_path else "unknown"
