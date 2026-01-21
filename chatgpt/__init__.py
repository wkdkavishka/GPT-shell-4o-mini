"""
GPT-shell-4o-mini - A simple, lightweight CLI to use OpenAI's ChatGPT and DALL-E from the terminal.

This package provides a command-line interface for interacting with OpenAI's API,
including chat completion, image generation, and command generation features.
"""

from .main import main

# Import version from pyproject.toml to avoid duplication
try:
    import importlib.metadata as metadata

    __version__ = metadata.version("gpt-shell-4o-mini")
except ImportError:
    # Fallback for older Python versions
    import pkg_resources

    __version__ = pkg_resources.get_distribution("gpt-shell-4o-mini").version

__all__ = ["main"]
