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

A simple, lightweight CLI to use OpenAI's ChatGPT and DALL-E from the terminal.  
This project now uses a Python installer (`install.py`) for setup and a Python uninstaller (`remove.py`) for clean removal.  
The main shell script is `chatgpt.sh`, which is installed to your system path for easy access.

</div>

## Features ✨

### 🌍 **Cross-Platform Support**
* **Windows 10/11** - Full support with automatic environment variable setup
* **macOS** - Works seamlessly on all versions
* **Linux** - Supports all major distributions (Ubuntu, Fedora, Debian, Arch, etc.)

### 🧠 **Advanced Terminal Context**
* **Static User Profile** - Remembers your OS, username, and distribution
* **Dynamic Session Capture** - Sends recent terminal commands AND outputs to ChatGPT
  * tmux support - Captures last 30 lines automatically
  * screen support - GNU screen buffer capture
  * History fallback - Works even without tmux/screen
* **Intelligent Responses** - ChatGPT sees your errors, current directory, and shell type

### 🚀 **Seamless Setup**
* **First-run wizard** - Automatic API key setup and verification
* **No external dependencies** - Uses Python's requests library (no curl needed)
* **Platform-aware** - Automatically configures for your OS

---

## Getting Started

### Prerequisites

* **Python 3.7+** (usually pre-installed)
* **An OpenAI API key** - Get one free at [OpenAI](https://platform.openai.com/account/api-keys)

**Optional (for best terminal context):**
* [tmux](https://github.com/tmux/tmux) - Highly recommended for full terminal session capture
  ```sh
  sudo apt install tmux   # Ubuntu/Debian
  sudo dnf install tmux   # Fedora
  brew install tmux       # macOS
  ```

---

### Installation

#### Windows

**Pip Installation (Only method for Windows):**

```sh
pip install gpt-shell-4o-mini
```

After installation, run `gpt` to start the setup wizard:

```sh
gpt
```

The wizard will:
* Prompt for your OpenAI API key
* Verify the key with OpenAI
* Save it to Windows environment variables automatically
* Create your user profile

> **Note:** Manual installation via `install.py` is not supported on Windows.

#### macOS / Linux

**Option 1: Pip Installation (Recommended)**

```sh
pip install gpt-shell-4o-mini
```

Run `gpt` to start the setup wizard.

**Option 2: Manual Installation**

Quick install without cloning:
```sh
curl -O https://raw.githubusercontent.com/wkdkavishka/GPT-shell-4o-mini/origin/install.py
sudo python3 install.py
```

Or clone and install:
```sh
git clone https://github.com/wkdkavishka/GPT-shell-4o-mini.git
cd GPT-shell-4o-mini
sudo python3 install.py
```

You will be prompted for your OpenAI API key during the installation.
Alternatively, you can provide your key directly:

```sh
sudo python3 install.py --key <YOUR_OPENAI_API_KEY>
```

This will:
- Download and install `chatgpt.sh` to `/usr/local/bin/gpt`
- Optionally create a symlink `/usr/local/bin/chatgpt`
- Add your API key and `/usr/local/bin` to your shell profile

### Uninstallation

The `remove.py` script provides comprehensive uninstallation that works whether you installed via pip or manually.

**For a quick uninstall without cloning:**

```sh
curl -O https://raw.githubusercontent.com/wkdkavishka/GPT-shell-4o-mini/origin/remove.py
python3 remove.py
# Or with sudo if you used manual installation:
sudo python3 remove.py
```

**What it removes:**
- Package installed via pip (if applicable)
- Manual installation from `/usr/local/bin/gpt` and `/usr/local/bin/chatgpt` (if applicable)
- `OPENAI_KEY` and `/usr/local/bin` PATH modifications from your shell profiles
- Chat history file (`~/.chatgpt_py_history`)

The script automatically detects how the package was installed and removes it accordingly.

### Manual Installation

If you want to install manually:

- Download the `chatgpt.sh` file to a directory in your `$PATH`
- Add your OpenAI API key to your shell profile:  
  `export OPENAI_KEY=your_key_here`
- Make sure `/usr/local/bin` is in your `$PATH`
- (Optional) Install [imgcat](https://iterm2.com/utilities/imgcat) for iTerm2 image support

## Usage

### Start

#### Chat Mode
  - Run the script by using the `gpt` or `chatgpt` command anywhere. By default the script uses the `gpt-4o-mini` model.
#### Pipe Mode
  - You can also use it in pipe mode:  
    `echo "What is the command to get all pdf files created yesterday?" | gpt`
#### Script Parameters
  - You can also pass the prompt as a command line argument:  
    `gpt -p "What is the regex to match an email address?"`

---

## 🧠 Terminal Context Feature

### How It Works

GPT-shell-4o-mini automatically sends contextual information with every prompt:

**Static Profile** (`~/.chatgpt_py_info`):
* Your username
* Operating system and version
* Linux distribution (if applicable)

**Dynamic Terminal Session** (captured in real-time):
* Current working directory
* Shell type (bash, zsh, PowerShell, etc.)
* Recent terminal commands AND their outputs!

### Example

When you run `gpt` in tmux, ChatGPT sees:

```
[Static Profile: User: john | OS: Linux | Distro: Ubuntu 22.04]
[Terminal Session (Shell: bash | CWD: /home/john/project | Source: tmux):
john@ubuntu:~/project$ npm run dev
Error: Missing script: "dev"
]

You: How do I fix this?
```

ChatGPT response will be context-aware:
> "I see you're missing the 'dev' script in package.json. Since you're on Ubuntu..."

### Best Experience

For full terminal session capture (commands + outputs):

```bash
# Install tmux
sudo apt install tmux   # Ubuntu/Debian
sudo dnf install tmux   # Fedora  
brew install tmux       # macOS

# Start tmux
tmux

# Now run gpt - it captures your entire session!
gpt
```

Without tmux/screen, it falls back to command history only.

---

## Support

For issues, questions, or contributions, please visit the  
[GitHub Repository](https://github.com/wkdkavishka/GPT-shell-4o-mini)

### Commands

  - `image:` To generate images, start a prompt with `image:`
  - `history` To view your chat history, type `history`
  - `models` To get a list of the models available at OpenAI API, type `models`
  - `model:` To view all the information on a specific model, start a prompt with `model:` and the model `id`
  - `command:` To get a command with the specified functionality and run it, just type `command:` and explain what you want to achieve

### Chat context

  - Enable chat context mode for the model to remember your previous chat questions and answers. Start the script with `-c` or `--chat-context`.

#### Set chat initial prompt
  - Set your own initial chat prompt with `-i` or `--init-prompt`  
    Example: `gpt -i "You are Rick from Rick and Morty, reply with references to episodes."` 

### Use the official ChatGPT model

  - The default model used is `gpt-4o-mini`.

### Use GPT-4
  - If you have access to the GPT-4 model you can use it by setting the model to `gpt-4`, i.e. `gpt --model gpt-4`

### Set request parameters

  - To set request parameters:  
    `gpt --temperature 0.9 --model text-babbage:001 --max-tokens 100 --size 1024x1024`
    - temperature,  `-t` or `--temperature`
    - model, `-m` or `--model`
    - max number of tokens, `--max-tokens`
    - image size, `-s` or `--size`
    - prompt, `-p` or `--prompt` 
    - prompt from a file, `--prompt-from-file`  
