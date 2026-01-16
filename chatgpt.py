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
USER_PROFILE_FILE = Path.home() / ".chatgpt_py_info"
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


# --- First-Run Setup Functions ---


def verify_api_key(api_key):
    """Verify that an OpenAI API key is valid by making a test request."""
    try:
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                return True
        return False
    except Exception:
        return False


# --- Terminal Context Functions ---


def capture_tmux_session(lines=30):
    """Capture recent lines from current tmux pane."""
    try:
        if os.environ.get('TMUX'):
            result = subprocess.run(
                ['tmux', 'capture-pane', '-p', '-S', f'-{lines}'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout
    except Exception:
        pass
    return None


def capture_screen_session():
    """Capture from GNU screen."""
    try:
        if os.environ.get('STY'):
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as f:
                temp_file = f.name
            
            subprocess.run(['screen', '-X', 'hardcopy', temp_file], timeout=2)
            
            if os.path.exists(temp_file):
                with open(temp_file, 'r') as f:
                    content = f.read()
                os.unlink(temp_file)
                return content
    except Exception:
        pass
    return None


def get_shell_history(max_commands=5):
    """Get recent shell commands from history."""
    import platform
    
    system = platform.system()
    history = []
    
    try:
        if system == "Windows":
            # PowerShell history
            ps_history = Path.home() / "AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt"
            if ps_history.exists():
                with open(ps_history, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    history = [line.strip() for line in lines[-max_commands:] if line.strip()]
        else:
            # Try bash history
            bash_history = Path.home() / ".bash_history"
            if bash_history.exists():
                with open(bash_history, 'r') as f:
                    lines = f.readlines()
                    history = [line.strip() for line in lines[-max_commands:] if line.strip()]
            
            # Try zsh history if bash not found
            elif (Path.home() / ".zsh_history").exists():
                zsh_history = Path.home() / ".zsh_history"
                with open(zsh_history, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    lines = content.split('\n')
                    # zsh history format: : timestamp:0;command
                    history = []
                    for line in lines[-max_commands:]:
                        if ';' in line:
                            cmd = line.split(';', 1)[1].strip()
                            if cmd:
                                history.append(cmd)
                        elif line.strip() and not line.startswith(':'):
                            history.append(line.strip())
    except Exception:
        pass
    
    return history


def get_current_shell():
    """Detect current shell."""
    import platform
    
    if platform.system() == "Windows":
        if os.environ.get("PSModulePath"):
            return "PowerShell"
        return "cmd"
    
    shell_path = os.environ.get("SHELL", "")
    return shell_path.split("/")[-1] if shell_path else "unknown"


def clean_terminal_output(text):
    """Remove ANSI color codes and clean up terminal output."""
    import re
    
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    
    # Remove carriage returns that mess up display
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Limit to avoid token limits (last 2000 chars)
    if len(text) > 2000:
        text = "...(truncated)\n" + text[-2000:]
    
    return text


def get_terminal_session(max_lines=30):
    """
    Capture recent terminal session (commands + outputs).
    Tries multiple methods in order.
    Returns: (method_name, session_text)
    """
    
    # Try tmux first (most common for developers)
    session = capture_tmux_session(lines=max_lines)
    if session:
        return ("tmux", session)
    
    # Try screen
    session = capture_screen_session()
    if session:
        return ("screen", session)
    
    # Fallback: command history only (no outputs)
    history = get_shell_history(max_commands=5)
    if history:
        return ("history", "\n".join([f"$ {cmd}" for cmd in history]))
    
    return (None, None)


def format_terminal_session():
    """Format terminal session as context string."""
    try:
        method, session = get_terminal_session(max_lines=30)
        
        if not session:
            return ""
        
        # Clean the output
        session = clean_terminal_output(session)
        
        # Build header
        parts = [
            f"Shell: {get_current_shell()}",
            f"CWD: {os.getcwd()}"
        ]
        
        if method:
            parts.append(f"Source: {method}")
        
        header = " | ".join(parts)
        
        return f"[Terminal Session ({header}):\n{session}\n]"
    except Exception:
        # Silently fail if context collection fails
        return ""


# --- Static User Profile Functions ---


def collect_user_profile():
    """Collect static user profile information (done once during setup)."""
    import platform
    import getpass
    
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
        f"OS: {profile.get('os', 'unknown')}"
    ]
    
    if profile.get("distro"):
        parts.append(f"Distro: {profile['distro']}")
    
    parts.append(f"Version: {profile.get('os_version', 'unknown')}")
    
    return "[Static Profile: " + " | ".join(parts) + "]"


# --- Environment Variable Setup Functions ---


def update_shell_profile(api_key):
    """Add or update the OPENAI_KEY in the user's shell profile or system."""
    import platform
    
    system = platform.system()
    
    if system == "Windows":
        # Windows: Use setx to set user environment variable
        try:
            subprocess.run(['setx', 'OPENAI_KEY', api_key], 
                          check=True, capture_output=True)
            # Also set for current session
            os.environ['OPENAI_KEY'] = api_key
            console.print(f"[green]✓[/green] Added OPENAI_KEY to Windows environment variables")
            console.print(f"[yellow]Note:[/yellow] Restart your terminal for the change to take effect")
            return True
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not set environment variable: {e}")
            console.print(f"[yellow]Please manually set OPENAI_KEY in System Settings[/yellow]")
            return False
            
    else:  # macOS or Linux
        # Existing Unix shell profile logic
        profile_paths = [
            Path.home() / ".bashrc",
            Path.home() / ".zprofile",
            Path.home() / ".zshrc",
            Path.home() / ".bash_profile",
            Path.home() / ".profile",
        ]

        for profile_path in profile_paths:
            if profile_path.exists():
                try:
                    with profile_path.open("r") as f:
                        content = f.read()

                    if "export OPENAI_KEY" not in content:
                        with profile_path.open("a") as f:
                            f.write(f"\n# OpenAI API Key for GPT-shell-4o-mini\n")
                            f.write(f"export OPENAI_KEY={api_key}\n")
                        console.print(f"[green]✓[/green] Added OPENAI_KEY to {profile_path}")
                        return True
                    else:
                        console.print(f"[yellow]![/yellow] OPENAI_KEY already exists in {profile_path}")
                        return True
                except Exception as e:
                    console.print(f"[yellow]Warning:[/yellow] Could not update {profile_path}: {e}")
                    continue

        # If no profile found
        console.print("[yellow]Warning:[/yellow] No shell profile found.")
        console.print(f"[yellow]Please manually add to your shell config:[/yellow]")
        console.print(f"  export OPENAI_KEY={api_key}")
        return False


def first_run_setup():
    """Interactive setup wizard for first-time users."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Welcome to GPT-shell-4o-mini![/bold cyan]")
    console.print("=" * 60)
    console.print("\nIt looks like you haven't set up your OpenAI API key yet.")
    console.print("\n[bold]Where to get an API key:[/bold]")
    console.print("  https://platform.openai.com/account/api-keys")
    console.print("\n" + "=" * 60 + "\n")

    try:
        user_input = console.input("[bold]Do you have an OpenAI API key? (yes/no):[/bold] ").strip().lower()
        
        if user_input not in ["yes", "y"]:
            console.print("\n[yellow]Please get an API key from:[/yellow]")
            console.print("  https://platform.openai.com/account/api-keys")
            console.print("\n[cyan]After getting your key, run 'gpt' again to set it up.[/cyan]\n")
            sys.exit(0)

        api_key = console.input("\n[bold]Enter your OpenAI API key:[/bold] ").strip()
        
        if not api_key:
            console.print("[red]Error:[/red] No API key provided.")
            sys.exit(1)

        console.print("\n[cyan]Verifying API key...[/cyan]")
        
        if not verify_api_key(api_key):
            console.print("[red]Error:[/red] Invalid API key or unable to verify.")
            console.print("Please check your key and try again.\n")
            sys.exit(1)

        console.print("[green]✓[/green] API key verified successfully!")
        
        # Update shell profile
        console.print("\n[cyan]Saving API key to your shell profile...[/cyan]")
        profile_saved = update_shell_profile(api_key)
        
        # Collect and save user profile
        console.print("\n[cyan]Setting up your profile...[/cyan]")
        profile = collect_user_profile()
        
        # Allow username customization
        console.print(f"\n[bold]Detected username:[/bold] {profile['username']}")
        custom_name = console.input(
            "[bold]Press Enter to use this, or type a different name:[/bold] "
        ).strip()
        
        if custom_name:
            profile['username'] = custom_name
        
        # Save profile
        if save_user_profile(profile):
            console.print(f"\n[green]✓[/green] Profile saved:")
            console.print(f"  Username: {profile['username']}")
            console.print(f"  OS: {profile['os']}")
            if 'distro' in profile:
                console.print(f"  Distribution: {profile['distro']}")
        
        if profile_saved:
            console.print("\n[green]✓[/green] Setup complete!")
            console.print("\n[bold]Important:[/bold] For the key to be available, run:")
            console.print("  [cyan]source ~/.bashrc[/cyan]  (or your shell's config file)")
            console.print("\nOr restart your terminal, then run '[cyan]gpt[/cyan]' again.\n")
        else:
            console.print("\n[yellow]Setup complete, but you'll need to manually add the key.[/yellow]\n")
        
        sys.exit(0)
        
    except (EOFError, KeyboardInterrupt):
        console.print("\n\n[yellow]Setup cancelled.[/yellow]\n")
        sys.exit(0)


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
    global API_KEY
    if not API_KEY:
        # Run first-time setup wizard
        first_run_setup()
        # If we get here, setup was cancelled or failed
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
