#!/usr/bin/env python3

import os
import sys
import argparse
import json
import subprocess
import shlex
import webbrowser
from datetime import datetime
from pathlib import Path

# Try importing necessary libraries and provide helpful error messages
try:
    from openai import OpenAI, APIError, RateLimitError, APIConnectionError
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


# --- Configuration ---
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
HISTORY_FILE = Path.home() / ".chatgpt_py_history"
DEFAULT_MODEL = "gpt-4o-mini"  # Updated default
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1024
DEFAULT_IMAGE_SIZE = "512x512"
# Max number of *user/assistant* message pairs to keep in context
MAX_CONTEXT_MESSAGES = 10  # Simplified context limit


# --- Prompts ---
# Use f-string for dynamic date insertion
def get_chat_init_prompt():
    return f"You are ChatGPT, a Large Language Model trained by OpenAI. You answer as concisely as possible for each response (e.g. don’t be verbose). If you are generating a list, do not have too many items. Keep the number of items short. Before each user prompt you will be given the chat history in Q&A form. Output your answer directly, with no labels in front. Do not start your answers with A or Anwser. Today's date is {datetime.now().strftime('%m/%d/%Y')}"


def get_system_prompt():
    return f"You are ChatGPT, a large language model trained by OpenAI. Answer as concisely as possible. Current date: {datetime.now().strftime('%m/%d/%Y')}."


COMMAND_GENERATION_PROMPT = "You are a Command Line Interface expert and your task is to provide functioning shell commands. Return a CLI command and nothing else - do not send it in a code block, quotes, or anything else, just the pure text CONTAINING ONLY THE COMMAND. If possible, return a one-line bash command or chain many commands together. Return ONLY the command ready to run in the terminal. The command should do the following:"

# --- Initialization ---
console = Console()
client = None  # Initialize client later after checking API key

# --- Helper Functions ---


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


# --- API Interaction Functions ---


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
        # console.print("[grey50]Waiting for response...[/grey50]", end="\r")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # console.print(" " * 30, end="\r") # Clear waiting message
        content = response.choices[0].message.content
        return content.strip() if content else ""
    except APIError as e:
        handle_api_error(e)
        return None  # Indicate failure


# --- Main Execution ---


def main():
    global client  # Allow modification of the global client variable

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="A Python script to interact with OpenAI's API from the terminal.",
        epilog="Example: python chatgpt.py -p 'Translate to French: Hello World!'",
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
        ],  # Added DALL-E 3 sizes
        help=f"Image size for DALL-E (default: {DEFAULT_IMAGE_SIZE}).",
    )
    # Basic multi-line support might be handled by terminal; this flag is less critical
    # parser.add_argument("-b", "--big-prompt", action="store_true", help="Allow multi-line prompts (often default terminal behavior).")
    # Context is implicitly managed for chat models in this script
    # parser.add_argument("-c", "--chat-context", action="store_true", help="Enable chat context (default for chat models).")

    args = parser.parse_args()

    # --- Initial Checks ---
    if not API_KEY:
        console.print(
            "[bold red]Error:[/bold red] OPENAI_KEY environment variable not set."
        )
        console.print(
            "You can set it temporarily by running: export OPENAI_KEY='YOUR_KEY_HERE'"
        )
        sys.exit(1)

    # Initialize OpenAI client now that we know the key exists
    try:
        client = OpenAI(api_key=API_KEY)
    except Exception as e:
        console.print(f"[bold red]Error initializing OpenAI client:[/bold red] {e}")
        sys.exit(1)

    # --- Handle Standalone Actions ---
    if args.list:
        list_models()
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
            console.print("[grey50]Processing...[/grey50]", end="\r")
            response_data = get_chat_completion(
                messages, args.model, args.temperature, args.max_tokens
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
            response_data = get_chat_completion(
                messages, args.model, args.temperature, args.max_tokens
            )
            console.print(" " * 30, end="\r")  # Clear thinking message

            if response_data:
                console.print("[bold cyan]ChatGPT:[/bold cyan]")
                console.print(Markdown(response_data))
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
