"""Setup script for anki-mini."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="anki-mini",
    version="1.0.0",
    author="Anki Mini Team",
    description="Portable CLI flashcard app with spaced repetition",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/anki-mini",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - stdlib only
    ],
    entry_points={
        "console_scripts": [
            "anki-mini=anki_mini.cli:main",
        ],
    },
)
