#!/usr/bin/env python3
"""Setup script for GPT-shell-4o-mini package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="gpt-shell-4o-mini",
    version="1.0.1",
    author="wkdkavishka",
    author_email="w.k.d.kavishka@gmail.com",  # Add your email here
    description="A simple, lightweight CLI to use OpenAI's ChatGPT and DALL-E from the terminal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wkdkavishka/GPT-shell-4o-mini",
    project_urls={
        "Bug Tracker": "https://github.com/wkdkavishka/GPT-shell-4o-mini/issues",
        "Source Code": "https://github.com/wkdkavishka/GPT-shell-4o-mini",
    },
    packages=find_packages(),
    py_modules=["chatgpt", "install", "remove"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.7",
    install_requires=[
        "openai>=1.0.0",
        "rich>=10.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "gpt=chatgpt:main",
            "chatgpt=chatgpt:main",
            "gpt-install=install:main",
            "gpt-remove=remove:main",
        ],
    },
    keywords="chatgpt openai cli terminal gpt dalle ai assistant wkdkavishka",
    license="MIT",
)
