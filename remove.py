#!/usr/bin/env python3
import os
import sys
from pathlib import Path


def getUserHome():
    sudoUser = os.environ.get("SUDO_USER")
    if sudoUser:
        import pwd

        return Path(pwd.getpwnam(sudoUser).pw_dir)
    return Path.home()


def removeLineFromFile(filePath, keyword):
    if not filePath.exists():
        return
    with filePath.open("r") as f:
        lines = f.readlines()
    with filePath.open("w") as f:
        for line in lines:
            if keyword not in line:
                f.write(line)


def main():
    userHome = getUserHome()
    profiles = [
        userHome / ".bashrc",
        userHome / ".zprofile",
        userHome / ".zshrc",
        userHome / ".bash_profile",
        userHome / ".profile",
    ]

    # Remove OPENAI_KEY and PATH modifications
    for profile in profiles:
        print(f"[*] Cleaning {profile}")
        removeLineFromFile(profile, "export OPENAI_KEY")
        removeLineFromFile(profile, "export PATH=$PATH:/usr/local/bin")

    # Remove chatgpt script
    gptPath = Path("/usr/local/bin/gpt")
    if gptPath.exists():
        gptPath.unlink()
        print("[+] Removed /usr/local/bin/gpt")

    print("[✔] Removal complete")


if __name__ == "__main__":
    main()
