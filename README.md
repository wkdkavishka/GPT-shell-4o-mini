![shell](https://user-images.githubusercontent.com/99351112/207697723-a3fabc0b-f067-4f83-96fd-1f7225a0bb38.svg)
<div align="center">
<p>

✨Join the new <a href="https://discord.gg/fwfYAZWKqu">Discord server</a> and start contributing to this project!✨</p>

<h1>chatGPT-shell-cli</h1>

A simple, lightweight CLI to use OpenAI's ChatGPT and DALL-E from the terminal.  
This project now uses a Python installer (`install.py`) for setup and a Python uninstaller (`remove.py`) for clean removal.  
The main shell script is `chatgpt.sh`, which is installed to your system path for easy access.

</div>

## Features

- [Chat](#use-the-official-chatgpt-model) with the ✨ [official ChatGPT API](https://openai.com/blog/introducing-chatgpt-and-whisper-apis) ✨ from the terminal
- [Generate images](#commands) from a text prompt
- View your [chat history](#commands)
- [Chat context](#chat-context), GPT remembers previous chat questions and answers
- Pass the input prompt with [pipe](#pipe-mode), as a [script parameter](#script-parameters) or normal [chat mode](#chat-mode)
- List all available [OpenAI models](#commands) 
- Set OpenAI [request parameters](#set-request-parameters)
- Generate a [command](#commands) and run it in terminal

![Screenshot 2023-01-12 at 13 59 08](https://user-images.githubusercontent.com/99351112/212061157-bc92e221-ad29-46b7-a0a8-c2735a09449d.png)

![Screenshot 2023-01-13 at 16 39 27](https://user-images.githubusercontent.com/99351112/212346562-ea568cce-2ca2-4b03-9ebc-ece8902c923d.png)

![faster_convert](https://user-images.githubusercontent.com/99351112/230916960-aca256c0-a2c0-4193-ace6-7ed7f3db2145.gif)

## Getting Started

### Prerequisites

This script relies on `curl` for API requests and `jq` to parse JSON responses.

* [curl](https://www.curl.se)
  ```sh
  sudo apt install curl   # Debian/Ubuntu
  # or
  brew install curl       # macOS
  ```
* [jq](https://stedolan.github.io/jq/)
  ```sh
  sudo apt install jq     # Debian/Ubuntu
  # or
  brew install jq         # macOS
  ```
* An OpenAI API key. Create an account and get a free API Key at [OpenAI](https://platform.openai.com/account/api-keys)

* Optionally, you can install [glow](https://github.com/charmbracelet/glow) to render responses in markdown 

### Installation

To install, clone this repository and run the Python installer as root:

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

To remove the CLI and all related configuration, run:

```sh
sudo python3 remove.py
```

This will:
- Remove `OPENAI_KEY` and `/usr/local/bin` modifications from your shell profiles
- Remove the installed `gpt` and `chatgpt` commands

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

## Contributors
:pray: Thanks to all the people who used, tested, submitted issues, PRs and proposed changes:

[pfr-dev](https://www.github.com/pfr-dev), [jordantrizz](https://www.github.com/jordantrizz), [se7en-x230](https://www.github.com/se7en-x230), [mountaineerbr](https://www.github.com/mountaineerbr), [oligeo](https://www.github.com/oligeo), [biaocy](https://www.github.com/biaocy), [dmd](https://www.github.com/dmd), [goosegit11](https://www.github.com/goosegit11), [dilatedpupils](https://www.github.com/dilatedpupils), [direster](https://www.github.com/direster), [rxaviers](https://www.github.com/rxaviers), [Zeioth](https://www.github.com/Zeioth), [edshamis](https://www.github.com/edshamis), [nre-ableton](https://www.github.com/nre-ableton), [TobiasLaving](https://www.github.com/TobiasLaving), [RexAckermann](https://www.github.com/RexAckermann), [emirkmo](https://www.github.com/emirkmo), [np](https://www.github.com/np), [camAtGitHub](https://github.com/camAtGitHub), [keyboardsage](https://github.com/keyboardsage) [tomas223](https://github.com/tomas223)

## Contributing
Contributions are very welcome!

If you have ideas or need help to get started join the [Discord server](https://discord.gg/fwfYAZWKqu)

![Discord](https://img.shields.io/discord/1090696025162928158?label=Discord&style=for-the-badge)
