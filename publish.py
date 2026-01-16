#!/usr/bin/env python3
"""
Automated package publishing script for GPT-shell-4o-mini.

This script automates the process of:
1. Cleaning old build files
2. Building the package distribution
3. Uploading to PyPI

Usage:
    python3 publish.py              # Build and upload to PyPI
    python3 publish.py --test       # Upload to TestPyPI instead
    python3 publish.py --build-only # Only build, don't upload
    python3 publish.py --clean      # Only clean build files
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


def print_step(step_num, message):
    """Print a formatted step message."""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {message}")
    print(f"{'='*60}\n")


def clean_build_files():
    """Remove old build artifacts."""
    print_step(1, "Cleaning old build files")
    
    dirs_to_remove = ["dist", "build", "*.egg-info"]
    removed = False
    
    for pattern in dirs_to_remove:
        if "*" in pattern:
            # Handle glob patterns
            for path in Path(".").glob(pattern):
                if path.is_dir():
                    print(f"Removing: {path}")
                    shutil.rmtree(path)
                    removed = True
        else:
            # Handle exact directory names
            if os.path.exists(pattern):
                print(f"Removing: {pattern}")
                shutil.rmtree(pattern)
                removed = True
    
    if not removed:
        print("No old build files found.")
    else:
        print("✓ Build files cleaned successfully!")
    
    return True


def get_version():
    """Extract version from setup.py."""
    try:
        with open("setup.py", "r") as f:
            for line in f:
                if "version=" in line:
                    # Extract version string
                    version = line.split("version=")[1].split(",")[0].strip().strip('"').strip("'")
                    return version
    except Exception as e:
        print(f"Warning: Could not extract version from setup.py: {e}")
    return "unknown"


def build_package():
    """Build the package distribution."""
    print_step(2, "Building package distribution")
    
    version = get_version()
    print(f"Building version: {version}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "build"],
            check=True,
            capture_output=False,
            text=True
        )
        
        print("\n✓ Package built successfully!")
        
        # List created files
        if os.path.exists("dist"):
            print("\nCreated files:")
            for file in os.listdir("dist"):
                file_path = os.path.join("dist", file)
                size = os.path.getsize(file_path) / 1024  # KB
                print(f"  - {file} ({size:.1f} KB)")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False
    except FileNotFoundError:
        print("\n✗ Error: 'build' module not found.")
        print("Install it with: pip install build")
        return False


def upload_to_pypi(test_pypi=False):
    """Upload the package to PyPI or TestPyPI."""
    repository = "TestPyPI" if test_pypi else "PyPI"
    print_step(3, f"Uploading to {repository}")
    
    if not os.path.exists("dist") or not os.listdir("dist"):
        print("✗ Error: No distribution files found in dist/")
        print("Run with --build-only first, or without flags to build and upload.")
        return False
    
    version = get_version()
    
    # Confirm upload
    print(f"About to upload version {version} to {repository}")
    
    try:
        response = input(f"\nProceed with upload? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print("Upload cancelled.")
            return False
    except (EOFError, KeyboardInterrupt):
        print("\n\nUpload cancelled.")
        return False
    
    # Build twine command
    cmd = [sys.executable, "-m", "twine", "upload"]
    
    if test_pypi:
        cmd.extend(["--repository", "testpypi"])
    
    cmd.append("dist/*")
    
    try:
        result = subprocess.run(cmd, check=True)
        
        print(f"\n✓ Successfully uploaded to {repository}!")
        
        # Show PyPI link
        package_name = "gpt-shell-4o-mini"
        if test_pypi:
            url = f"https://test.pypi.org/project/{package_name}/{version}/"
        else:
            url = f"https://pypi.org/project/{package_name}/{version}/"
        
        print(f"\nView at: {url}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Upload failed: {e}")
        return False
    except FileNotFoundError:
        print("\n✗ Error: 'twine' not found.")
        print("Install it with: pip install twine")
        return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Automated package publishing for GPT-shell-4o-mini"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Upload to TestPyPI instead of PyPI"
    )
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="Only build the package, don't upload"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Only clean build files"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("GPT-shell-4o-mini Package Publisher")
    print("="*60)
    
    # Clean only
    if args.clean:
        clean_build_files()
        print("\n✓ Done!")
        return
    
    # Step 1: Clean
    if not clean_build_files():
        sys.exit(1)
    
    # Step 2: Build
    if not build_package():
        sys.exit(1)
    
    # Step 3: Upload (if not build-only)
    if not args.build_only:
        if not upload_to_pypi(test_pypi=args.test):
            sys.exit(1)
    else:
        print("\n✓ Build complete! (Upload skipped)")
    
    print("\n" + "="*60)
    print("✓ All steps completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
