from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="muse-cli",
    version="1.0.0",
    author="ulasti",
    description="A CLI tool to download music from the internet with lyrics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ulasti/muse-cli",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "yt-dlp>=2023.3.4",
        "mutagen>=1.47.0",
        "lyricsgenius>=3.0.1",
    ],
    entry_points={
        "console_scripts": [
            "muse-cli=muse.__main__:main",
        ],
    },
)