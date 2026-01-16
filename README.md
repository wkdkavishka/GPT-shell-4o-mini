### original work
https://github.com/0xacx/chatGPT-shell-cli

<div align=center>
I translated it to python, and added some features, Few things was not working for me, also updated to gpt 4o-mini
</div>
<div align=center>
** greate work from the original authour **
</div>

<div align="center">

<h1>chatGPT-shell-cli</h1>

A simple, lightweight CLI to use OpenAI's ChatGPT and DALL-E from the terminal.  
This project now uses a Python installer (`install.py`) for setup and a Python uninstaller (`remove.py`) for clean removal.  
The main shell script is `chatgpt.sh`, which is installed to your system path for easy access.

</div>

## Getting Started

### Prerequisites

This script relies on `curl` for API requests and `jq` to parse JSON responses.

* [curl](https://www.curl.se)
  ```sh
  sudo apt install curl   # Debian/Ubuntu
  sudo dnf install curl   # Fedora/Redhat linux
  # or
  brew install curl       # macOS
  ```
* [jq](https://stedolan.github.io/jq/)
  ```sh
  sudo apt install jq     # Debian/Ubuntu
  sudo dnf install jq     # Fedora/Redhat Linux
  # or
  brew install jq         # macOS
  ```
* An OpenAI API key. Create an account and get a free API Key at [OpenAI](https://platform.openai.com/account/api-keys)

* Optionally, you can install [glow](https://github.com/charmbracelet/glow) to render responses in markdown 

### Installation

**For a quick install without cloning:**

```sh
curl -O https://raw.githubusercontent.com/wkdkavishka/GPT-shell-4o-mini/origin/install.py
sudo python3 install.py
```

**To install, clone this repository and run the Python installer as root**

```sh
git clone https://github.com/wkdkavishka/chatGPT-shell-cli.git
cd chatGPT-shell-cli
sudo python3 install.py
```

You will be prompted for your OpenAI API key.  
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
