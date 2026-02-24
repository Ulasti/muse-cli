from setuptools import setup, find_packages

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = ""

setup(
    name="muse-cli",
    version="1.0.0",
    author="ulasti",
    description="A CLI tool to download audio from YouTube with lyrics and metadata",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ulasti/muse-cli",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "yt-dlp>=2023.3.4",
        "mutagen>=1.47.0",
        "lyricsgenius>=3.0.1",
        "musicbrainzngs>=0.7.1",
    ],
    entry_points={
        "console_scripts": [
            "muse-cli=muse.__main__:main",
        ],
    },
)