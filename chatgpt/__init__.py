#!/usr/bin/env python3
"""
GPT-shell-4o-mini Package

A Python package for interacting with OpenAI's ChatGPT and DALL-E from the terminal.
"""

import os
import sys
from pathlib import Path

# Try importing necessary libraries and provide helpful error messages
try:
    from openai import OpenAI
except ImportError:
    print(
        "Error: 'openai' library not found. Please install it: pip install openai",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from rich.console import Console
    from rich.markdown import Markdown
except ImportError:
    print(
        "Error: 'rich' library not found. Please install it: pip install rich",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import requests
except ImportError:
    print(
        "Error: 'requests' library not found. Please install it: pip install requests",
        file=sys.stderr,
    )
    sys.exit(1)

# Import core modules
from .core.config import *
from .core.initialization import validate_setup, first_run_setup
from .core.api import *
from .user.profile import *
from .user.history import *
from .os_specific.terminal import *
from .os_specific.environment import *
from .os_specific.platform import *
from .utils.helpers import *
from .utils.security import *

# Initialize global console
console = Console()

# Initialize global client (will be set after API key validation)
client = None


def main():
    """Main entry point for GPT-shell-4o-mini."""
    global client

    # Import here to avoid circular imports
    from .core.initialization import validate_setup, first_run_setup
    from .core.api import list_models
    from .user.history import display_history
    from .utils.security import is_dangerous
    import argparse
    import subprocess

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="A Python script to interact with OpenAI's API from the terminal.",
        epilog="Example: gpt -p 'Translate to French: Hello World!'",
    )
    parser.add_argument(
        "-p", "--prompt", help="Provide prompt directly instead of starting chat."
    )
    parser.add_argument(
        "--prompt-from-file",
        type=argparse.FileType("r", encoding="utf-8"),
        help="Provide prompt from a file.",
    )
    parser.add_argument(
        "-i", "--init-prompt", help="Provide initial system prompt (overrides default)."
    )
    parser.add_argument(
        "--init-prompt-from-file",
        type=argparse.FileType("r", encoding="utf-8"),
        help="Provide initial system prompt from file.",
    )
    parser.add_argument(
        "-l", "--list", action="store_true", help="List available OpenAI models."
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model to use (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help=f"Sampling temperature (default: {DEFAULT_TEMPERATURE}).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Max tokens for completion (default: {DEFAULT_MAX_TOKENS}).",
    )
    parser.add_argument(
        "-s",
        "--size",
        default=DEFAULT_IMAGE_SIZE,
        choices=[
            "256x256",
            "512x512",
            "1024x1024",
            "1792x1024",
            "1024x1792",
        ],
        help=f"Image size for DALL-E (default: {DEFAULT_IMAGE_SIZE}).",
    )

    args = parser.parse_args()

    # --- Setup Validation ---
    global API_KEY
    API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")

    # Validate setup on every run
    issues = validate_setup(API_KEY)
    if issues:
        # Run targeted setup for missing components
        first_run_setup(target_issues=issues)
        # Re-check after setup
        API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        issues = validate_setup(API_KEY)
        if issues:
            console.print(
                f"[red]Setup failed. Missing components: {', '.join(issues)}[/red]"
            )
            sys.exit(1)

    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=API_KEY)
    except Exception as e:
        console.print(f"[bold red]Error initializing OpenAI client:[/bold red] {e}")
        sys.exit(1)

    # --- Handle Standalone Actions ---
    if args.list:
        list_models(client=client, console=console)
        sys.exit(0)

    # --- Determine Initial Prompt and Mode ---
    initial_prompt_text = None
    pipe_mode = False

    if args.prompt:
        initial_prompt_text = args.prompt
        pipe_mode = True
    elif args.prompt_from_file:
        initial_prompt_text = args.prompt_from_file.read()
        args.prompt_from_file.close()
        pipe_mode = True
    elif not sys.stdin.isatty():  # Check if input is being piped
        initial_prompt_text = sys.stdin.read()
        pipe_mode = True

    # --- Setup System Prompt ---
    system_prompt = get_system_prompt()
    if args.init_prompt:
        system_prompt = args.init_prompt
    elif args.init_prompt_from_file:
        system_prompt = args.init_prompt_from_file.read()
        args.init_prompt_from_file.close()

    # --- Chat History Initialization ---
    messages = [{"role": "system", "content": system_prompt}]

    # --- Execute ---
    if pipe_mode:
        # Import pipe mode handling functions
        from .core.api import generate_image, get_model_details, get_chat_completion

        # --- Pipe/Single Prompt Mode ---
        prompt = initial_prompt_text.strip()
        if not prompt:
            console.print("[red]Error:[/red] Received empty prompt from pipe/argument.")
            sys.exit(1)

        if prompt.lower().startswith("image:"):
            image_prompt = prompt[len("image:") :].strip()
            generate_image(image_prompt, args.size, client=client, console=console)
        elif prompt.lower().startswith("model:"):
            model_id = prompt[len("model:") :].strip()
            get_model_details(model_id, client=client, console=console)
        elif prompt.lower() == "history":
            display_history()
        elif prompt.lower() == "models":
            list_models(client=client, console=console)
        elif prompt.lower().startswith("command:"):
            command_desc = prompt[len("command:") :].strip()
            request_prompt = f"{COMMAND_GENERATION_PROMPT} {command_desc}"
            messages.append({"role": "user", "content": request_prompt})
            console.print("[grey50]Generating command...[/grey50]", end="\r")
            command_output = get_chat_completion(
                messages, args.model, args.temperature, args.max_tokens, client=client
            )
            console.print(" " * 30, end="\r")  # Clear

            if command_output:
                console.print(
                    f"[bold cyan]Suggested Command:[/bold cyan]\n{command_output}"
                )
                append_history(prompt, command_output)

                if is_dangerous(command_output):
                    console.print(
                        "[bold yellow]Warning![/bold yellow] This command might modify your file system, download files, or execute complex operations. Review it carefully."
                    )

                try:
                    if console.input("Execute this command? (y/N) ").lower() == "y":
                        console.print(f"\n[grey50]Executing: {command_output}[/grey50]")
                        result = subprocess.run(
                            command_output,
                            shell=True,
                            check=False,
                            capture_output=True,
                            text=True,
                        )
                        if result.stdout:
                            console.print("[bold green]Output:[/bold green]")
                            console.print(result.stdout)
                        if result.stderr:
                            console.print("[bold red]Error Output:[/bold red]")
                            console.print(result.stderr)
                        if result.returncode != 0:
                            console.print(
                                f"[yellow]Command exited with status code:[/yellow] {result.returncode}"
                            )

                except Exception as e:
                    console.print(
                        f"[bold red]Failed to execute command:[/bold red] {e}"
                    )
            else:
                console.print("[red]Failed to generate command.[/red]")
        else:
            # Default to chat completion
            messages.append({"role": "user", "content": prompt})
            console.print("[grey50]Processing...[/grey50]", end="\r")
            response_data = get_chat_completion(
                messages, args.model, args.temperature, args.max_tokens, client=client
            )
            console.print(" " * 30, end="\r")  # Clear processing message
            if response_data:
                console.print(Markdown(response_data))
                append_history(prompt, response_data)
            else:
                console.print("[red]Failed to get response.[/red]")

    else:
        # --- Interactive Chat Mode ---
        console.print(
            f"Welcome to ChatGPT in Python! Model: [cyan]{args.model}[/cyan]. Type 'exit' or 'quit' to end."
        )
        while True:
            try:
                prompt = console.input("[bold green]You: [/bold green]")
            except (EOFError, KeyboardInterrupt):
                console.print("\nExiting.")
                break

            prompt_lower = prompt.lower().strip()

            if prompt_lower in ["exit", "quit", "q"]:
                break
            if not prompt.strip():
                continue

            if prompt_lower == "history":
                display_history()
                continue
            elif prompt_lower == "models":
                list_models(client=client, console=console)
                continue
            elif prompt_lower.startswith("model:"):
                model_id = prompt[len("model:") :].strip()
                if model_id:
                    get_model_details(model_id, client=client, console=console)
                else:
                    console.print(
                        "[yellow]Please specify a model ID after 'model:'.[/yellow]"
                    )
                continue
            elif prompt_lower.startswith("image:"):
                image_prompt = prompt[len("image:") :].strip()
                if image_prompt:
                    generate_image(
                        image_prompt, args.size, client=client, console=console
                    )
                else:
                    console.print(
                        "[yellow]Please provide a description after 'image:'.[/yellow]"
                    )
                continue
            elif prompt_lower.startswith("command:"):
                command_desc = prompt[len("command:") :].strip()
                if not command_desc:
                    console.print(
                        "[yellow]Please describe the command you want after 'command:'.[/yellow]"
                    )
                    continue

                command_messages = [
                    {
                        "role": "system",
                        "content": get_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": f"{COMMAND_GENERATION_PROMPT} {command_desc}",
                    },
                ]

                console.print("[grey50]Generating command...[/grey50]", end="\r")
                command_output = get_chat_completion(
                    command_messages,
                    args.model,
                    args.temperature,
                    args.max_tokens,
                    client=client,
                )
                console.print(" " * 30, end="\r")  # Clear

                if command_output:
                    console.print(
                        f"[bold cyan]Suggested Command:[/bold cyan]\n{command_output}"
                    )
                    append_history(prompt, command_output)

                    if is_dangerous(command_output):
                        console.print(
                            "[bold yellow]Warning![/bold yellow] This command might modify your file system, download files, or execute complex operations. Review it carefully."
                        )

                    try:
                        if console.input("Execute this command? (y/N) ").lower() == "y":
                            console.print(
                                f"\n[grey50]Executing: {command_output}[/grey50]"
                            )
                            result = subprocess.run(
                                command_output,
                                shell=True,
                                check=False,
                                capture_output=True,
                                text=True,
                            )
                            if result.stdout:
                                console.print("[bold green]Output:[/bold green]")
                                console.print(result.stdout.strip())
                            if result.stderr:
                                console.print("[bold red]Error Output:[/bold red]")
                                console.print(result.stderr.strip())
                            if result.returncode != 0:
                                console.print(
                                    f"[yellow]Command exited with status code:[/yellow] {result.returncode}"
                                )
                    except Exception as e:
                        console.print(
                            f"[bold red]Failed to execute command:[/bold red] {e}"
                        )
                else:
                    console.print("[red]Failed to generate command.[/red]")
                continue

            # --- Regular Chat ---
            messages.append({"role": "user", "content": prompt})

            console.print("[grey50]ChatGPT is thinking...[/grey50]", end="\r")
            response_data = get_chat_completion(
                messages, args.model, args.temperature, args.max_tokens, client=client
            )
            console.print(" " * 30, end="\r")  # Clear thinking message

            if response_data:
                console.print("[bold cyan]ChatGPT:[/bold cyan]")
                console.print(Markdown(response_data))
                messages.append({"role": "assistant", "content": response_data})
                append_history(prompt, response_data)

                # Simple context management: Keep only the last N pairs + system prompt
                if len(messages) > (1 + MAX_CONTEXT_MESSAGES * 2):
                    messages = [messages[0]] + messages[-(MAX_CONTEXT_MESSAGES * 2) :]
            else:
                console.print("[red]Failed to get response.[/red]")
                messages.pop()


if __name__ == "__main__":
    main()
