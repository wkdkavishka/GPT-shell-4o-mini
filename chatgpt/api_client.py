"""
API client functions for GPT-shell-4o-mini.

This module handles all interactions with the OpenAI API,
including chat completions, image generation, and model management.
"""

import sys
import json
import webbrowser
from datetime import datetime
from rich.console import Console

# Try importing necessary libraries and provide helpful error messages
try:
    from openai import OpenAI, APIError, RateLimitError, APIConnectionError
except ImportError:
    print(
        "Error: 'openai' library not found. Please install it: pip install openai",
        file=sys.stderr,
    )
    sys.exit(1)

# Configuration
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1024
DEFAULT_IMAGE_SIZE = "512x512"
MAX_CONTEXT_MESSAGES = 10

console = Console()
client = None  # Initialize client later after checking API key


def handle_api_error(e):
    """Handles common OpenAI API errors."""
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


def initialize_client(api_key):
    """Initialize the OpenAI client with the provided API key."""
    global client
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        console.print(f"[bold red]Error initializing OpenAI client:[/bold red] {e}")
        sys.exit(1)


def list_models():
    """Lists available OpenAI models."""
    try:
        console.print("[grey50]Fetching models...[/grey50]", end="\r")
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
        handle_api_error(e)


def get_model_details(model_id):
    """Gets details for a specific model."""
    try:
        console.print(f"[grey50]Fetching details for {model_id}...[/grey50]", end="\r")
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
            handle_api_error(e)


def generate_image(prompt, size):
    """Generates an image using DALL-E."""
    try:
        console.print("[grey50]Generating image...[/grey50]", end="\r")
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
        handle_api_error(e)
    except (
        Exception
    ) as e:  # Catch other potential errors like network issues during download etc.
        console.print(
            f"[red]An error occurred during image generation or display:[/red] {e}"
        )


def get_chat_completion(messages, model, temperature, max_tokens):
    """Gets a completion from a chat model."""
    try:
        # Import here to avoid circular imports
        from .user_profile import format_user_profile
        from .terminal_context import format_terminal_session

        # Build complete context for EVERY prompt
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

        # Prepend context to EVERY user message, not just the first one
        for i, msg in enumerate(messages):
            if msg["role"] == "user":
                messages[i]["content"] = f"{full_context}\n\n{msg['content']}"

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


def get_system_prompt():
    """Get the system prompt from custom file or default."""
    from pathlib import Path

    custom_prompt_file = Path.home() / ".chatgpt_py_sys_prompt"

    if custom_prompt_file.exists():
        try:
            with open(custom_prompt_file, "r", encoding="utf-8") as f:
                custom_prompt = f.read().strip()
                if custom_prompt:
                    return custom_prompt
        except (IOError, OSError):
            # If file exists but can't be read, fall back to default
            pass

    # Default system prompt
    return f"""
CRITICAL THINKING REQUIREMENTS:
- Analyze the user's intent and underlying goals from their questions
- Consider the provided context (user profile, terminal session, previous conversation)
- Think deeply about what the user is trying to accomplish
- Research and provide comprehensive, well-thought-out solutions
- Anticipate follow-up needs and address potential edge cases
- Consider system implications, security aspects, and best practices
- Provide context-aware answers that build on previous interactions

RESPONSE GUIDELINES:
- Provide thorough, well-researched answers that demonstrate deep understanding
- Include relevant examples, alternatives, and considerations
- Explain the "why" behind recommendations, not just the "how"
- Consider the user's specific environment and use case from context
- Offer multiple approaches when applicable with pros/cons
- Include security and performance considerations
- Reference relevant system documentation or best practices when helpful
"""

    # def get_chat_init_prompt():
    """Get the chat initialization prompt."""
    return f"You are ChatGPT, a Large Language Model trained by OpenAI. You answer as concisely as possible for each response (e.g. don't be verbose). If you are generating a list, do not have too many items. Keep the number of items short. Before each user prompt you will be given the chat history in Q&A form. Output your answer directly, with no labels in front. Do not start your answers with A or Anwser. Today's date is {datetime.now().strftime('%m/%d/%Y')}"


# Command generation prompt
COMMAND_GENERATION_PROMPT = "You are a Command Line Interface expert and your task is to provide functioning shell commands. Return a CLI command and nothing else - do not send it in a code block, quotes, or anything else, just the pure text CONTAINING ONLY THE COMMAND. If possible, return a one-line bash command or chain many commands together. Return ONLY the command ready to run in the terminal. The command should do the following:"


def set_custom_system_prompt(prompt_text):
    """Save a custom system prompt to the file."""
    from pathlib import Path

    custom_prompt_file = Path.home() / ".chatgpt_py_sys_prompt"

    try:
        with open(custom_prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt_text.strip())
        return True
    except (IOError, OSError):
        return False


def get_custom_system_prompt():
    """Get the current custom system prompt from file."""
    from pathlib import Path

    custom_prompt_file = Path.home() / ".chatgpt_py_sys_prompt"

    if custom_prompt_file.exists():
        try:
            with open(custom_prompt_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except (IOError, OSError):
            pass

    return None


def reset_system_prompt():
    """Remove the custom system prompt file to use default."""
    from pathlib import Path

    custom_prompt_file = Path.home() / ".chatgpt_py_sys_prompt"

    try:
        if custom_prompt_file.exists():
            custom_prompt_file.unlink()
        return True
    except (IOError, OSError):
        return False
