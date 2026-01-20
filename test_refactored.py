#!/usr/bin/env python3
"""
Test script for the refactored GPT-shell-4o-mini package.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path for testing
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing imports...")

    try:
        # Test main package import
        import chatgpt

        print("✓ Main package import successful")

        # Test core modules
        from chatgpt.core import config, initialization, api

        print("✓ Core modules import successful")

        # Test user modules
        from chatgpt.user import profile, history

        print("✓ User modules import successful")

        # Test os_specific modules
        from chatgpt.os_specific import terminal, environment, platform

        print("✓ OS-specific modules import successful")

        # Test utils modules
        from chatgpt.utils import helpers, security

        print("✓ Utils modules import successful")

        return True

    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_configuration():
    """Test configuration constants and functions."""
    print("\nTesting configuration...")

    try:
        from chatgpt.core.config import (
            HISTORY_FILE,
            USER_PROFILE_FILE,
            DEFAULT_MODEL,
            get_chat_init_prompt,
            get_system_prompt,
        )

        # Test constants
        assert DEFAULT_MODEL == "gpt-4o-mini"
        print("✓ Configuration constants are correct")

        # Test prompt functions
        init_prompt = get_chat_init_prompt()
        system_prompt = get_system_prompt()
        assert "ChatGPT" in init_prompt
        assert "ChatGPT" in system_prompt
        print("✓ Prompt functions work correctly")

        return True

    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_user_profile():
    """Test user profile functions."""
    print("\nTesting user profile functions...")

    try:
        from chatgpt.user.profile import collect_user_profile, format_user_profile

        # Test profile collection
        profile = collect_user_profile()
        assert "username" in profile
        assert "os" in profile
        print("✓ User profile collection works")

        # Test profile formatting
        formatted = format_user_profile()
        assert "User:" in formatted
        print("✓ User profile formatting works")

        return True

    except Exception as e:
        print(f"✗ User profile test failed: {e}")
        return False


def test_validation():
    """Test setup validation function."""
    print("\nTesting validation functions...")

    try:
        from chatgpt.core.initialization import validate_setup

        # Test validation (should find missing API key)
        issues = validate_setup(None)
        assert "api_key" in issues
        print("✓ Validation correctly identifies missing API key")

        return True

    except Exception as e:
        print(f"✗ Validation test failed: {e}")
        return False


def test_security():
    """Test security functions."""
    print("\nTesting security functions...")

    try:
        from chatgpt.utils.security import is_dangerous, validate_command

        # Test dangerous command detection
        assert is_dangerous("rm -rf /") == True
        assert is_dangerous("ls -la") == False
        print("✓ Dangerous command detection works")

        # Test command validation
        is_safe, reason = validate_command("ls -la")
        assert is_safe == True

        is_safe, reason = validate_command("rm -rf /")
        assert is_safe == False
        print("✓ Command validation works")

        return True

    except Exception as e:
        print(f"✗ Security test failed: {e}")
        return False


def test_terminal_functions():
    """Test terminal-related functions."""
    print("\nTesting terminal functions...")

    try:
        from chatgpt.os_specific.terminal import (
            get_current_shell,
            clean_terminal_output,
        )

        # Test shell detection
        shell = get_current_shell()
        assert shell is not None
        print(f"✓ Shell detection works: {shell}")

        # Test output cleaning
        dirty_text = "\x1b[31mRed text\x1b[0m"
        clean_text = clean_terminal_output(dirty_text)
        assert "\x1b" not in clean_text
        print("✓ Terminal output cleaning works")

        return True

    except Exception as e:
        print(f"✗ Terminal functions test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=== GPT-shell-4o-mini Refactoring Test ===\n")

    tests = [
        test_imports,
        test_configuration,
        test_user_profile,
        test_validation,
        test_security,
        test_terminal_functions,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! The refactoring was successful.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
