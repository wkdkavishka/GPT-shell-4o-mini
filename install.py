#!/usr/bin/env python3
"""
Installer script for GPT-shell-4o-mini.

This script automates the installation of the GPT-shell-4o-mini tool, including:
- Downloading the main shell script
- Installing dependencies (imgcat, magick) if needed
- Setting up the OpenAI API key in the user's shell profile
- Ensuring /usr/local/bin is in the user's PATH

Usage:
    sudo python3 install.py [--key <OPENAI_API_KEY>]

Arguments:
    --key   (optional) Provide your OpenAI API key directly as a parameter.

If --key is not provided, the script will prompt for the key interactively.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
import argparse


def requireRoot():
    """Ensure the script is run as root. Exit if not."""
    if os.geteuid() != 0:
        print("This script must be run as root")
        sys.exit(1)


def commandExists(cmd):
    """Check if a command exists in the system PATH."""
    return shutil.which(cmd) is not None


def runCommand(cmd):
    """Run a shell command, raising an error if it fails."""
    subprocess.run(cmd, shell=True, check=True)


def installImgcat():
    """
    Install imgcat utility for iTerm2 if running on macOS with iTerm2.
    Tooltip: imgcat allows displaying images in the terminal (iTerm2 only).
    """
    if os.environ.get("TERM_PROGRAM") == "iTerm.app":
        if not commandExists("imgcat"):
            print("[*] Installing imgcat...")
            runCommand(
                "curl -sS https://iterm2.com/utilities/imgcat -o /usr/local/bin/imgcat"
            )
            os.chmod("/usr/local/bin/imgcat", 0o755)
            print("[+] Installed imgcat")
        else:
            print("[=] imgcat already installed")


def installMagick():
    """
    Install magick utility for Kitty terminal if needed.
    Tooltip: magick is part of ImageMagick, used for image display in Kitty terminal.
    """
    if os.environ.get("TERM") == "xterm-kitty":
        if not commandExists("magick"):
            print("[*] Installing magick...")
            runCommand(
                "curl -sS https://imagemagick.org/archive/binaries/magick -o /usr/local/bin/magick"
            )
            os.chmod("/usr/local/bin/magick", 0o755)
            print("[+] Installed magick")
        else:
            print("[=] magick already installed")


def installChatgptScript():
    """
    Download the chatgpt.py script and install it to /usr/local/bin/gpt.
    Also replaces 'open' with 'xdg-open' for Linux/FreeBSD compatibility.
    Tooltip: This is the main CLI script for interacting with ChatGPT from your shell.
    """
    userHome = getUserHome()
    runCommand(
        f"curl -sS https://raw.githubusercontent.com/wkdkavishka/GPT-shell-4o-mini/origin/chatgpt.py -o {userHome}/chatgpt.py"
    )
    print(f"[+] Downloaded chatgpt.py to {userHome}/chatgpt.py")
    localChatFile = Path(f"{userHome}/chatgpt.py")
    src = f"{userHome}/chatgpt.py"
    dst = "/usr/local/bin/gpt"
    runCommand(f"mv {src} {dst}")
    runCommand(f"chmod +x {dst}")
    print(f"[+] Copied chatgpt.py to {dst}")

    # Fix open command on Linux/FreeBSD
    if sys.platform.startswith("linux") or "freebsd" in sys.platform:
        print("[*] Replacing 'open' with 'xdg-open'...")
        with open(dst, "r+") as file:
            content = file.read().replace(
                'open "${image_url}"', 'xdg-open "${image_url}"'
            )
            file.seek(0)
            file.write(content)
            file.truncate()
        print("[+] Replaced 'open' with 'xdg-open'")


def askForApiKey():
    """
    Prompt the user for their OpenAI API key.
    If not provided, instructs the user to follow manual installation.
    Tooltip: Your OpenAI API key is required to use the GPT-shell-4o-mini.
    """
    answer = input("Enter your api key: ").strip().lower()
    if not answer:
        print(
            "[!] Please follow manual installation: https://github.com/wkdkavishka/GPT-shell-4o-mini/blob/main#manual-installation"
        )
        sys.exit(0)
    return input("[?] Please enter your OpenAI API key: ").strip()


def getUserHome():
    """
    Get the home directory of the original user (not root if using sudo).
    Tooltip: Ensures profile changes are made to the correct user's shell config.
    """
    sudoUser = os.environ.get("SUDO_USER")
    if sudoUser:
        import pwd

        return Path(pwd.getpwnam(sudoUser).pw_dir)
    return Path.home()


def verifyUserApiKey(apiKey=None):
    """
    Verify the provided OpenAI API key by making a test request to the OpenAI API.
    Exits if the key is invalid.
    Tooltip: This step ensures your API key is valid before proceeding.
    """
    if apiKey is None:
        apiKey = askForApiKey()

    response = subprocess.run(
        [
            "curl",
            "-s",
            "-H",
            f"Authorization: Bearer {apiKey}",
            "https://api.openai.com/v1/models",
        ],
        capture_output=True,
        text=True,
    )

    if response.returncode != 0:
        print("[!] Invalid OpenAI API key.")
        sys.exit(1)

    print("[+] OpenAI API key is valid.")

    return apiKey


def getApiKey():
    """
    Interactively prompt the user for their OpenAI API key, with guidance if they don't have one.
    Tooltip: Guides the user through obtaining and entering their API key.
    """
    userAnswer = (
        input(
            "If you do not have a api-key get one here https://platform.openai.com/account/api-keys: \n"
            "[?] Would you like to continue? (Yes/No): "
        )
        .strip()
        .lower()
    )
    if userAnswer in ["yes", "y", "ok", "yep"]:
        apiKey = input("[?] Please enter your OpenAI API key: ").strip()
        if not apiKey:
            print("[!] No OpenAI API key provided.")
            sys.exit(0)
        return apiKey
    else:
        print("[!] get one here https://platform.openai.com/account/api-keys:")
        userAnswer = input("Did you get one? (Yes/No): ").strip().lower()
        if userAnswer in ["yes", "y", "ok"]:
            apiKey = input("[?] Please enter your OpenAI API key: ").strip()
        if not apiKey:
            print("[!] No OpenAI API key provided.")
            sys.exit(0)
            return apiKey
        else:
            exit(0)


def updateShellProfile(apiKey):
    """
    Add or update the OPENAI_KEY and /usr/local/bin PATH in the user's shell profile.
    If no profile is found, sets the variable for the current session and prints instructions.
    Tooltip: This step ensures the CLI can find your API key and is available in your PATH.
    """
    userHome = getUserHome()
    profilePaths = [
        userHome / ".bashrc",
        userHome / ".zprofile",
        userHome / ".zshrc",
        userHome / ".bash_profile",
        userHome / ".profile",
    ]

    isAdded = False
    for profilePath in profilePaths:
        print(f"[*] Checking {profilePath}")
        if profilePath.exists():
            print(f"[*] Found profile: {profilePath}")
            with profilePath.open("r") as f:
                fileContent = f.read()

            if "export OPENAI_KEY" not in fileContent:
                with profilePath.open("a") as f:
                    f.write(f"\nexport OPENAI_KEY={apiKey}\n")
                    print(f"[+] Added OPENAI_KEY to {profilePath}")
            else:
                print(f"[=] OPENAI_KEY already exists in {profilePath}")

            if "/usr/local/bin" not in fileContent:
                with profilePath.open("a") as f:
                    f.write("\nexport PATH=$PATH:/usr/local/bin\n")
                    print(f"[+] Added /usr/local/bin to PATH in {profilePath}")

            isAdded = True
            break

    if not isAdded:
        print(
            "[!] No supported shell profile found. Exporting OPENAI_KEY for current session only."
        )
        os.environ["OPENAI_KEY"] = apiKey
        print(f"[!] Please add this to your shell profile: export OPENAI_KEY={apiKey}")


def parseArgs():
    """
    Parse command-line arguments for the installer.
    Tooltip: Allows passing the API key as a command-line argument.
    """
    parser = argparse.ArgumentParser(description="Install GPT-shell-4o-mini")
    parser.add_argument("--key", help="OpenAI API key")
    return parser.parse_args()


def main():
    """
    Main entry point for the installer script.
    Tooltip: Runs all installation steps in order.
    """
    requireRoot()

    args = parseArgs()
    apiKey = args.key

    if not apiKey:
        apiKey = getApiKey()

    print(f"[+] API key: {apiKey}")

    apiKey = verifyUserApiKey(apiKey)

    for dep in ["curl", "jq"]:
        if not commandExists(dep):
            print(f"You need to install '{dep}' to use the chatgpt script.")
            sys.exit(1)

    installImgcat()
    installMagick()
    installChatgptScript()
    updateShellProfile(apiKey)

    print("[✔] Installation complete")


if __name__ == "__main__":
    main()
