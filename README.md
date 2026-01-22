### original work

https://github.com/0xacx/chatGPT-shell-cli

<div align=center>
I translated it to python, and added some features, Few things was not working for me, also updated to gpt 4o-mini
</div>
<div align=center>
** greate work from the original authour **
</div>

<div align="center">

<h1>GPT-shell-4o-mini</h1>

A simple, lightweight Python CLI to use OpenAI's ChatGPT and DALL-E from the terminal.

</div>

## Features ✨

### 🌍 **Cross-Platform Support**

- **Windows 10/11** - Full support with automatic environment variable setup
- **macOS** - Works seamlessly on all versions
- **Linux** - Supports all major distributions (Ubuntu, Fedora, Debian, Arch, etc.)

### 🧠 **Smart Terminal Context**

- **User Profile** - Remembers your OS, username, and distribution
- **Terminal Session Info** - Sends current working directory, shell type, and environment to ChatGPT
- **Intelligent Responses** - ChatGPT sees your context and environment for better assistance

### 🚀 **Easy Setup**

- **First-run wizard** - Automatic API key setup and verification
- **Python Package** - Installable via pip for easy management
- **Cross-platform** - Works on Windows, macOS, and Linux

---

## Getting Started

### Prerequisites

- **Python 3.7+** (usually pre-installed)
- **An OpenAI API key** - Get one free at [OpenAI](https://platform.openai.com/account/api-keys)

---

### Installation

#### Installation

**Pip Installation (Recommended for all platforms):**

```sh
pip install gpt-shell-4o-mini
```

After installation, run `gpt` to start the setup wizard:

```sh
gpt
```

The wizard will:

- Prompt for your OpenAI API key
- Verify the key with OpenAI
- Save it securely in your os environment
- Create your user profile
- Files Will be created at your home directory as chatgpt_py\*\*

### Uninstallation

#### **IMPORTANT: Command Order Matters**

**Always run `gpt-remove` BEFORE `pip uninstall`** - the `gpt-remove` command is part of the package and will be removed by `pip uninstall`.

---

#### **Method 1: Complete Uninstall (Recommended)**

```bash
gpt-remove
```

**What `gpt-remove` does:**

- **Interactive confirmation** - asks before proceeding
- **Removes configuration files** - deletes `~/.chatgpt_py_*` files
- **Cleans environment variables** - removes OPENAI_KEY from shell profiles
- **Uninstalls Python package** - runs `pip uninstall gpt-shell-4o-mini` automatically
- **Shows progress** - detailed feedback throughout the process

**Result:** Complete removal of all traces of the package

---

#### **Method 2: Basic Package Removal**

```bash
pip uninstall gpt-shell-4o-mini
```

**What `pip uninstall` does:**

- **Removes Python package** - deletes package from site-packages
- **Removes commands** - deletes `gpt`, `chatgpt`, and `gpt-remove` commands
- **Leaves configuration files** - `~/.chatgpt_py_*` files remain
- **Leaves environment variables** - OPENAI_KEY in shell profiles remains

**Result:** Package removed but manual cleanup required

---

#### **Method 3: Manual Cleanup After Basic Uninstall**

If you already ran `pip uninstall` and need to clean up:

```bash
# Download and run the uninstall module
curl -O https://raw.githubusercontent.com/wkdkavishka/GPT-shell-4o-mini/main/chatgpt/uninstall.py
python uninstall.py
```

**What this does:**

- **Removes configuration files** - cleans up `~/.chatgpt_py_*` files
- **Cleans environment variables** - removes OPENAI_KEY from shell profiles
- **Cannot uninstall package** - package already removed

**Result:** Configuration cleanup only

---

### **Manual Cleanup Required After `pip uninstall`**

If you used `pip uninstall` without `gpt-remove`, manually remove:

- **Chat history**: `~/.chatgpt_py_history`
- **Custom system prompt**: `~/.chatgpt_py_sys_prompt`
- **User profile**: `~/.chatgpt_py_info`
- **Environment variables**: OPENAI_KEY from shell profiles (`~/.bashrc`, `~/.zshrc`, etc.)

## Usage

### Command Line Options

```bash
gpt [OPTIONS]
```

#### Basic Options

- `-h, --help` - Show help message and exit
- `-p, --prompt PROMPT` - Provide prompt directly instead of starting chat
- `--prompt-from-file FILE` - Provide prompt from a file
- `-l, --list` - List available OpenAI models

#### Model & Response Options

- `-m, --model MODEL` - Model to use (default: gpt-4o-mini)
- `-t, --temperature TEMPERATURE` - Sampling temperature (default: 0.7)
- `--max-tokens MAX_TOKENS` - Max tokens for completion (default: 1024)
- `-s, --size SIZE` - Image size for DALL-E (default: 512x512)

#### System Prompt Management

- `-i, --init-prompt PROMPT` - Provide initial system prompt (overrides default)
- `--init-prompt-from-file FILE` - Provide initial system prompt from file
- `--sys-prompt PROMPT` - Set or update custom system prompt (saved to ~/.chatgpt_py_sys_prompt)
- `--get-sys-prompt` - Show current custom system prompt
- `--reset-sys-prompt` - Remove custom system prompt and use default

#### Debug Options

- `--debug` - Print debug information including context sent to AI

### Usage Examples

#### Interactive Chat Mode

```bash
gpt
# Starts interactive chat with ChatGPT
```

#### Single Prompt Mode

```bash
gpt -p "What is the regex to match an email address?"
gpt --prompt "Translate to French: Hello World!"
```

#### Pipe Mode

```bash
echo "What is the command to get all pdf files created yesterday?" | gpt
ls -la | gpt -p "Explain these file permissions"
```

#### File Input

```bash
gpt --prompt-from-file my_prompt.txt
gpt --init-prompt-from-file custom_system_prompt.txt
```

#### Model Configuration

```bash
gpt --model gpt-4 --temperature 0.9 --max-tokens 2000
gpt -m gpt-4o -t 0.5
```

#### System Prompt Management

```bash
# Set custom system prompt
gpt --sys-prompt "You are a helpful Python programmer. Always provide code examples."

# View current system prompt
gpt --get-sys-prompt

# Reset to default
gpt --reset-sys-prompt

# Use temporary system prompt
gpt -i "You are a chef. Provide cooking advice." -p "How do I make pasta?"
```

#### Debug Mode

```bash
gpt --debug -p "Why is my script not working?"
gpt --debug  # Starts interactive chat with debug info
```

---

## 🧠 Terminal Context Feature

### How It Works

GPT-shell-4o-mini automatically sends contextual information with every prompt:

**User Profile** (`~/.chatgpt_py_info`):

- Your username
- Operating system and version
- Linux distribution (if applicable)

**Terminal Session** (captured in real-time):

- Current working directory
- Shell type (bash, zsh, PowerShell, etc.)
- Environment information

### Example

When you run `gpt`, ChatGPT sees:

```
[Static Profile: User: john | OS: Linux | Distro: Ubuntu 22.04]
[Terminal Session (Shell: bash | CWD: /home/john/project):
]

You: How do I fix this Python error?
```

ChatGPT response will be context-aware:

> "I see you're working in the `/home/john/project` directory on Ubuntu..."

### Debug Mode

Use `--debug` to see exactly what context is sent to ChatGPT:

```bash
gpt --debug -p "Help me debug this issue"
```

This will show:

- The full user profile
- Terminal session information
- Complete message history being sent
- Model parameters being used

---

## Support

For issues, questions, or contributions, please visit the  
[GitHub Repository](https://github.com/wkdkavishka/GPT-shell-4o-mini)

## Interactive Commands

During interactive chat mode, you can use these special commands:

- `image:` Generate images - Start a prompt with `image:` followed by description
  - Example: `image: a cute cat sitting on a laptop`
- `history` View your chat history
- `models` List available OpenAI models
- `model:` Get details on a specific model - Start with `model:` followed by model ID
  - Example: `model: gpt-4o-mini`
- `command:` Generate and execute commands - Start with `command:` followed by description
  - Example: `command: list all files larger than 100MB in current directory`
- `exit`, `quit`, `q` Exit the chat

### Image Generation

```bash
# In interactive mode
image: a beautiful sunset over mountains

# With specific size
gpt -s "1024x1024" -p "image: futuristic cityscape"
```

Available image sizes: `256x256`, `512x512`, `1024x1024`, `1792x1024`, `1024x1792`, `2048x2048`, `4096x4096`

### Command Generation

```bash
# In interactive mode
command: find all Python files with syntax errors

# As single prompt
gpt -p "command: compress all log files older than 30 days"
```

**⚠️ Safety Warning:** Generated commands are checked for dangerous patterns. You'll be asked to confirm before execution.
