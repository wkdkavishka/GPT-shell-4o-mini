"""
Main CLI interface for GPT-shell-4o-mini.

This module contains the main function and command-line interface logic,
integrating all the other modules.
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown

# Import modules from the package
from .checks import check_api_key
from .api_client import (
    initialize_client,
    list_models,
    get_model_details,
    generate_image,
    get_chat_completion,
    get_system_prompt,
    set_custom_system_prompt,
    get_custom_system_prompt,
    reset_system_prompt,
    COMMAND_GENERATION_PROMPT,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_IMAGE_SIZE,
    MAX_CONTEXT_MESSAGES,
)

# Configuration
HISTORY_FILE = Path.home() / ".chatgpt_py_history"

console = Console()


def append_history(prompt, response):
    """Appends interaction to the history file."""
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            f.write(f"{timestamp} User: {prompt}\n")
            f.write(f"{timestamp} Assistant: {response}\n\n")
    except IOError as e:
        console.print(
            f"[yellow]Warning:[/yellow] Could not write to history file {HISTORY_FILE}: {e}"
        )


def display_history():
    """Displays the chat history."""
    if not HISTORY_FILE.exists():
        console.print("[yellow]History file not found.[/yellow]")
        return
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            console.print(f.read())
    except IOError as e:
        console.print(f"[red]Error reading history file {HISTORY_FILE}: {e}[/red]")


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
    if ">" in command and not command.strip().endswith(
        " > /dev/null"
    ):  # Allow piping output to null
        if not command.strip().endswith(
            (">>", "2>", "1>", "&>")
        ):  # Basic check, might need refinement
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


def print_debug_info(messages, model, temperature, max_tokens, debug_flag):
    """Print debug information about the context being sent to AI."""
    if debug_flag:
        console.print("\n[bold yellow]=== DEBUG: Context Sent to AI ===[/bold yellow]")

        # Import here to avoid circular imports
        from .user_profile import format_user_profile
        from .terminal_context import format_terminal_session

        # Build and display full context only
        context_parts = []
        profile = format_user_profile()
        if profile:
            context_parts.append(profile)
        terminal = format_terminal_session()
        if terminal:
            context_parts.append(terminal)
        full_context = "\n".join(context_parts)

        console.print(f"[cyan]Full Context:[/cyan]\n{full_context}")

        console.print(f"[cyan]Messages being sent:[/cyan]")
        for i, msg in enumerate(messages):
            role_color = "green" if msg["role"] == "system" else "blue"
            content_preview = msg["content"][:100] + (
                "..." if len(msg["content"]) > 100 else ""
            )
            console.print(f"  [{role_color}] {msg['role']}", end=" ")
            console.print(content_preview, markup=False)

        console.print(
            f"[cyan]Model: {model}, Temperature: {temperature}, Max Tokens: {max_tokens}[/cyan]"
        )
        console.print("[bold yellow]=== END DEBUG ===[/bold yellow]\n")


def main():
    """Main CLI interface function."""

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="A Python script to interact with OpenAI's API from the terminal.",
        epilog="Example: python -m chatgpt -p 'Translate to French: Hello World!'",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print debug information including context sent to AI.",
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
            "2048x2048",
            "4096x4096",
        ],  # Added DALL-E 3 sizes
        help=f"Image size for DALL-E (default: {DEFAULT_IMAGE_SIZE}).",
    )

    # System prompt management arguments
    parser.add_argument(
        "--sys-prompt",
        help="Set or update custom system prompt (saved to ~/.chatgpt_py_sys_prompt).",
    )
    parser.add_argument(
        "--get-sys-prompt",
        action="store_true",
        help="Show current custom system prompt.",
    )
    parser.add_argument(
        "--reset-sys-prompt",
        action="store_true",
        help="Remove custom system prompt and use default.",
    )

    args = parser.parse_args()

    # --- Initial Checks ---
    api_key = check_api_key()

    # Initialize OpenAI client now that we know the key exists
    initialize_client(api_key)

    # --- Handle Standalone Actions ---
    if args.list:
        list_models()
        sys.exit(0)

    # Handle system prompt management
    if args.sys_prompt is not None:
        if args.sys_prompt:
            # Set custom system prompt from argument
            if set_custom_system_prompt(args.sys_prompt):
                console.print(
                    "[green]✓[/green] Custom system prompt saved to ~/.chatgpt_py_sys_prompt"
                )
            else:
                console.print("[red]✗[/red] Failed to save custom system prompt")
        else:
            console.print("[yellow]Warning:[/yellow] System prompt cannot be empty")
        sys.exit(0)

    if args.get_sys_prompt:
        current_prompt = get_custom_system_prompt()
        if current_prompt:
            console.print(
                f"[cyan]Current custom system prompt:[/cyan]\n{current_prompt}"
            )
        else:
            console.print(
                "[yellow]No custom system prompt found. Using default prompt.[/yellow]"
            )
            console.print(f"[cyan]Default prompt:[/cyan]\n{get_system_prompt()}")
        sys.exit(0)

    if args.reset_sys_prompt:
        if reset_system_prompt():
            console.print(
                "[green]✓[/green] Custom system prompt removed. Using default prompt."
            )
        else:
            console.print("[yellow]No custom system prompt to remove.[/yellow]")
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
    system_prompt = get_system_prompt()  # Default
    if args.init_prompt:
        system_prompt = args.init_prompt
    elif args.init_prompt_from_file:
        system_prompt = args.init_prompt_from_file.read()
        args.init_prompt_from_file.close()

    # --- Chat History Initialization ---
    messages = [{"role": "system", "content": system_prompt}]

    # --- Execute ---

    if pipe_mode:
        # --- Pipe/Single Prompt Mode ---
        prompt = initial_prompt_text.strip()
        if not prompt:
            console.print("[red]Error:[/red] Received empty prompt from pipe/argument.")
            sys.exit(1)

        if prompt.lower().startswith("image:"):
            image_prompt = prompt[len("image:") :].strip()
            generate_image(image_prompt, args.size)
        elif prompt.lower().startswith("model:"):
            model_id = prompt[len("model:") :].strip()
            get_model_details(model_id)
        elif prompt.lower() == "history":
            display_history()
        elif prompt.lower() == "models":
            list_models()
        elif prompt.lower().startswith("command:"):
            command_desc = prompt[len("command:") :].strip()
            request_prompt = f"{COMMAND_GENERATION_PROMPT} {command_desc}"
            messages.append({"role": "user", "content": request_prompt})
            print_debug_info(
                messages, args.model, args.temperature, args.max_tokens, args.debug
            )
            console.print("[grey50]Generating command...[/grey50]", end="\r")
            command_output = get_chat_completion(
                messages, args.model, args.temperature, args.max_tokens
            )
            console.print(" " * 30, end="\r")  # Clear

            if command_output:
                console.print(
                    f"[bold cyan]Suggested Command:[/bold cyan]\n{command_output}"
                )
                append_history(prompt, command_output)  # Log before asking to run

                if is_dangerous(command_output):
                    console.print(
                        "[bold yellow]Warning![/bold yellow] This command might modify your file system, download files, or execute complex operations. Review it carefully."
                    )

                try:
                    if console.input("Execute this command? (y/N) ").lower() == "y":
                        console.print(f"\n[grey50]Executing: {command_output}[/grey50]")
                        # Use shell=True cautiously, as the model might generate complex pipes/chains
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
            print_debug_info(
                messages, args.model, args.temperature, args.max_tokens, args.debug
            )
            console.print("[grey50]Processing...[/grey50]", end="\r")
            response_data = get_chat_completion(
                messages, args.model, args.temperature, args.max_tokens
            )
            console.print(" " * 30, end="\r")  # Clear processing message
            if response_data:
                console.print(Markdown(response_data))
                console.print(
                    "─" * console.width
                )  # Full-width horizontal line separator
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
                list_models()
                continue
            elif prompt_lower.startswith("model:"):
                model_id = prompt[len("model:") :].strip()
                if model_id:
                    get_model_details(model_id)
                else:
                    console.print(
                        "[yellow]Please specify a model ID after 'model:'.[/yellow]"
                    )
                continue
            elif prompt_lower.startswith("image:"):
                image_prompt = prompt[len("image:") :].strip()
                if image_prompt:
                    generate_image(image_prompt, args.size)
                    # Don't add image prompts/responses to chat history for now
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

                # Prepare message list *specifically* for command generation
                command_messages = [
                    {
                        "role": "system",
                        "content": get_system_prompt(),
                    },  # Use base system prompt if needed
                    {
                        "role": "user",
                        "content": f"{COMMAND_GENERATION_PROMPT} {command_desc}",
                    },
                ]

                console.print("[grey50]Generating command...[/grey50]", end="\r")
                print_debug_info(
                    command_messages,
                    args.model,
                    args.temperature,
                    args.max_tokens,
                    args.debug,
                )
                command_output = get_chat_completion(
                    command_messages, args.model, args.temperature, args.max_tokens
                )
                console.print(" " * 30, end="\r")  # Clear

                if command_output:
                    console.print(
                        f"[bold cyan]Suggested Command:[/bold cyan]\n{command_output}"
                    )
                    # Log the original 'command:' request and the generated command
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
                            # Use shell=True cautiously
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
                # Don't add the command generation interaction to the main chat history list `messages`
                continue  # Go to next prompt

            # --- Regular Chat ---
            messages.append({"role": "user", "content": prompt})

            console.print("[grey50]ChatGPT is thinking...[/grey50]", end="\r")
            print_debug_info(
                messages, args.model, args.temperature, args.max_tokens, args.debug
            )
            response_data = get_chat_completion(
                messages, args.model, args.temperature, args.max_tokens
            )
            console.print(" " * 30, end="\r")  # Clear thinking message

            if response_data:
                console.print("[bold cyan]ChatGPT:[/bold cyan]")
                console.print(Markdown(response_data))
                console.print(
                    "─" * console.width
                )  # Full-width horizontal line separator
                messages.append({"role": "assistant", "content": response_data})
                append_history(prompt, response_data)

                # Simple context management: Keep only the last N pairs + system prompt
                if len(messages) > (1 + MAX_CONTEXT_MESSAGES * 2):  # 1 system + N pairs
                    # Keep system prompt and the last MAX_CONTEXT_MESSAGES*2 messages (user+assistant)
                    messages = [messages[0]] + messages[-(MAX_CONTEXT_MESSAGES * 2) :]
            else:
                console.print("[red]Failed to get response.[/red]")
                # Remove the user message that failed
                messages.pop()


if __name__ == "__main__":
    main()
