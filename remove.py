#!/usr/bin/env python3
"""
Comprehensive uninstaller for GPT-shell-4o-mini.

This script removes the package whether it was installed via:
- pip install gpt-shell-4o-mini
- pip install -e . (editable mode)
- Manual installation to /usr/local/bin/gpt

Usage:
    python3 remove.py
    # or with sudo for manual installations
    sudo python3 remove.py
"""

import os
import sys
import subprocess
from pathlib import Path


def getUserHome():
    """Get the home directory of the original user (not root if using sudo)."""
    sudoUser = os.environ.get("SUDO_USER")
    if sudoUser:
        import pwd
        return Path(pwd.getpwnam(sudoUser).pw_dir)
    return Path.home()


def removeLineFromFile(filePath, keyword):
    """Remove lines containing the keyword from a file."""
    if not filePath.exists():
        return False
    
    with filePath.open("r") as f:
        lines = f.readlines()
    
    modified = False
    with filePath.open("w") as f:
        for line in lines:
            if keyword not in line:
                f.write(line)
            else:
                modified = True
    
    return modified


def isPipPackageInstalled(packageName):
    """Check if a package is installed via pip."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", packageName],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def uninstallPipPackage(packageName):
    """Uninstall a package using pip."""
    try:
        print(f"[*] Uninstalling {packageName} from pip...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", packageName],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print(f"[+] Successfully uninstalled {packageName} from pip")
            return True
        else:
            print(f"[!] Failed to uninstall {packageName} from pip")
            if result.stderr:
                print(f"    Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[!] Error during pip uninstall: {e}")
        return False


def removeManualInstallation():
    """Remove manually installed files from /usr/local/bin."""
    removed = False
    
    # Remove main gpt script
    gptPath = Path("/usr/local/bin/gpt")
    if gptPath.exists():
        try:
            gptPath.unlink()
            print("[+] Removed /usr/local/bin/gpt")
            removed = True
        except PermissionError:
            print("[!] Permission denied: Cannot remove /usr/local/bin/gpt")
            print("    Please run this script with sudo: sudo python3 remove.py")
            return False
    
    # Remove chatgpt symlink if it exists
    chatgptPath = Path("/usr/local/bin/chatgpt")
    if chatgptPath.exists():
        try:
            chatgptPath.unlink()
            print("[+] Removed /usr/local/bin/chatgpt")
            removed = True
        except PermissionError:
            print("[!] Permission denied: Cannot remove /usr/local/bin/chatgpt")
            return False
    
    return removed


def cleanShellProfiles():
    """Remove OPENAI_KEY and PATH modifications from shell profiles."""
    userHome = getUserHome()
    profiles = [
        userHome / ".bashrc",
        userHome / ".zprofile",
        userHome / ".zshrc",
        userHome / ".bash_profile",
        userHome / ".profile",
    ]

    cleaned = False
    for profile in profiles:
        if profile.exists():
            print(f"[*] Cleaning {profile}")
            if removeLineFromFile(profile, "export OPENAI_KEY"):
                print(f"    - Removed OPENAI_KEY")
                cleaned = True
            if removeLineFromFile(profile, "export PATH=$PATH:/usr/local/bin"):
                print(f"    - Removed PATH modification")
                cleaned = True
    
    return cleaned


def removeHistoryFile():
    """Remove the chat history file."""
    userHome = getUserHome()
    historyFile = userHome / ".chatgpt_py_history"
    
    if historyFile.exists():
        try:
            historyFile.unlink()
            print("[+] Removed chat history file")
            return True
        except Exception as e:
            print(f"[!] Could not remove history file: {e}")
            return False
    return False


def removeUserProfile():
    """Remove the user profile file."""
    userHome = getUserHome()
    profileFile = userHome / ".chatgpt_py_info"
    
    if profileFile.exists():
        try:
            profileFile.unlink()
            print("[+] Removed user profile file")
            return True
        except Exception as e:
            print(f"[!] Could not remove profile file: {e}")
            return False
    return False


def cleanWindowsEnvVar():
    """Remove OPENAI_KEY from Windows environment variables."""
    import platform
    
    if platform.system() != "Windows":
        return False
    
    try:
        # Remove user environment variable
        subprocess.run(
            ['reg', 'delete', 'HKCU\\Environment', '/v', 'OPENAI_KEY', '/f'],
            capture_output=True,
            check=False
        )
        print("[+] Removed OPENAI_KEY from Windows environment variables")
        return True
    except Exception as e:
        print(f"[!] Could not remove Windows environment variable: {e}")
        return False


def main():
    """Main uninstaller function."""
    import platform
    
    print("=" * 50)
    print("GPT-shell-4o-mini Uninstaller")
    print("=" * 50)
    print()
    
    removedSomething = False
    
    # Check and remove pip installation
    packageName = "gpt-shell-4o-mini"
    if isPipPackageInstalled(packageName):
        print(f"[*] Found {packageName} installed via pip")
        if uninstallPipPackage(packageName):
            removedSomething = True
    else:
        print(f"[=] {packageName} is not installed via pip")
    
    print()
    
    # Remove manual installation
    print("[*] Checking for manual installation...")
    if removeManualInstallation():
        removedSomething = True
    else:
        print("[=] No manual installation found in /usr/local/bin")
    
    print()
    
    # Clean shell profiles (Unix/Linux/macOS)
    if platform.system() != "Windows":
        print("[*] Cleaning shell profiles...")
        if cleanShellProfiles():
            removedSomething = True
        else:
            print("[=] No shell profile modifications found")
    else:
        # Clean Windows environment variables
        print("[*] Cleaning Windows environment variables...")
        if cleanWindowsEnvVar():
            removedSomething = True
        else:
            print("[=] No Windows environment variables found")
    
    print()
    
    # Remove history file
    print("[*] Checking for chat history...")
    if removeHistoryFile():
        removedSomething = True
    else:
        print("[=] No chat history file found")
    
    print()
    
    # Remove user profile
    print("[*] Checking for user profile...")
    if removeUserProfile():
        removedSomething = True
    else:
        print("[=] No user profile found")
    
    print()
    print("=" * 50)
    
    if removedSomething:
        print("[✔] Uninstallation complete!")
        print()
        if platform.system() != "Windows":
            print("Note: You may need to restart your terminal or run:")
            print("      source ~/.bashrc  (or your shell's config file)")
        else:
            print("Note: Restart your terminal for changes to take effect")
    else:
        print("[=] Nothing to uninstall - package not found")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
