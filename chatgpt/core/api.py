"""
OpenAI API interaction functions for GPT-shell-4o-mini.
"""

import os
import sys
import json
import subprocess
import webbrowser
from datetime import datetime

# Import OpenAI library
try:
    from openai import OpenAI, APIError, RateLimitError, APIConnectionError
except ImportError:
    print(
        "Error: 'openai' library not found. Please install it: pip install openai",
        file=sys.stderr,
    )
    sys.exit(1)

# Import project modules
from .config import COMMAND_GENERATION_PROMPT
from ..user.profile import format_user_profile
from ..os_specific.terminal import format_terminal_session


def handle_api_error(e, console=None):
    """Handles common OpenAI API errors."""
    # Import console only when needed to avoid circular imports
    if console is None:
        from rich.console import Console

        console = Console()

    if isinstance(e, RateLimitError):
        console.print(
            f"[bold red]API Error:[/bold red] Rate limit exceeded. Please check your plan and usage limits."
        )
    elif isinstance(e, APIConnectionError):
        console.print(
            f"[bold red]API Error:[/bold red] Could not connect to OpenAI. Check your network connection."
        )
    elif isinstance(e, APIError):
        console.print(f"[bold red]API Error ({e.status_code}):[/bold red] {e.message}")
        if e.body and "message" in e.body:
            console.print(f"  Details: {e.body['message']}")
    else:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
    sys.exit(1)


def list_models(client=None, console=None):
    """Lists available OpenAI models."""
    # Import console only when needed to avoid circular imports
    if console is None:
        from rich.console import Console

        console = Console()

    try:
        console.print("[grey50]Fetching models...[/grey50]", end="\r")
        if client is None:
            from .. import client
        models = client.models.list()
        console.print(
            "Available OpenAI Models:" + " " * 20
        )  # Overwrite fetching message

        # Sort models by creation date or ID if needed
        for model in sorted(models.data, key=lambda x: x.id):
            created_date = (
                datetime.fromtimestamp(model.created).strftime("%Y-%m-%d")
                if model.created
                else "N/A"
            )
            console.print(
                f"- [bold cyan]{model.id}[/bold cyan] (Owned by: {model.owned_by}, Created: {created_date})"
            )
    except APIError as e:
        handle_api_error(e, console)


def get_model_details(model_id, client=None, console=None):
    """Gets details for a specific model."""
    # Import console only when needed to avoid circular imports
    if console is None:
        from rich.console import Console

        console = Console()

    try:
        console.print(f"[grey50]Fetching details for {model_id}...[/grey50]", end="\r")
        if client is None:
            from .. import client
        model = client.models.retrieve(model_id)
        console.print(
            f"Details for model [bold cyan]{model_id}[/bold cyan]:" + " " * 20
        )  # Overwrite

        # Print details using rich formatting or just json.dumps
        console.print(json.dumps(model.to_dict(), indent=2))
    except APIError as e:
        # Customize error for not found
        if hasattr(e, "status_code") and e.status_code == 404:
            console.print(f"[bold red]Error:[/bold red] Model '{model_id}' not found.")
            sys.exit(1)
        else:
            handle_api_error(e, console)


def generate_image(prompt, size, client=None, console=None):
    """Generates an image using DALL-E."""
    # Import console only when needed to avoid circular imports
    if console is None:
        from rich.console import Console

        console = Console()

    try:
        console.print("[grey50]Generating image...[/grey50]", end="\r")
        if client is None:
            from .. import client
        response = client.images.generate(
            model="dall-e-3",  # Or dall-e-2 if preferred/available
            prompt=prompt,
            size=size,
            quality="standard",  # or "hd"
            n=1,
        )
        image_url = response.data[0].url
        console.print("Image generated successfully!" + " " * 20)  # Overwrite
        console.print(f"Link: {image_url}")

        # Offer to open in browser
        try:
            if console.input("Open image in browser? (y/N) ").lower() == "y":
                webbrowser.open(image_url)
        except Exception as e:
            console.print(f"[yellow]Could not open browser:[/yellow] {e}")

    except APIError as e:
        handle_api_error(e, console)
    except (
        Exception
    ) as e:  # Catch other potential errors like network issues during download etc.
        console.print(
            f"[red]An error occurred during image generation or display:[/red] {e}"
        )


def get_chat_completion(messages, model, temperature, max_tokens, client=None):
    """Gets a completion from a chat model."""
    try:
        # Build complete context
        context_parts = []

        # Add static profile
        profile = format_user_profile()
        if profile:
            context_parts.append(profile)

        # Add terminal session
        terminal = format_terminal_session()
        if terminal:
            context_parts.append(terminal)

        # Combine contexts
        full_context = "\n".join(context_parts)

        # Prepend to first user message
        if full_context and len(messages) > 1:
            for i, msg in enumerate(messages):
                if msg["role"] == "user":
                    messages[i]["content"] = f"{full_context}\n\n{msg['content']}"
                    break

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
    except APIError as e:
        handle_api_error(e)
        return None  # Indicate failure
