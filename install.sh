#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/Ulasti/muse-cli"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
DIM="\033[2m"
RESET="\033[0m"

echo ""
echo -e "${GREEN}  ███╗   ███╗██╗   ██╗███████╗███████╗${RESET}"
echo -e "${GREEN}  ████╗ ████║██║   ██║██╔════╝██╔════╝${RESET}"
echo -e "${GREEN}  ██╔████╔██║██║   ██║███████╗█████╗  ${RESET}"
echo -e "${GREEN}  ██║╚██╔╝██║██║   ██║╚════██║██╔══╝  ${RESET}"
echo -e "${GREEN}  ██║ ╚═╝ ██║╚██████╔╝███████║███████╗${RESET}"
echo -e "${GREEN}  ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚══════╝${RESET}"
echo -e "${DIM}  muse-cli installer — github.com/Ulasti/muse-cli${RESET}"
echo ""

# ── Detect OS and architecture ───────────────────────────────────────────────
OS="$(uname -s)"
ARCH="$(uname -m)"

# ── Helper: check if a command exists ────────────────────────────────────────
has() { command -v "$1" &>/dev/null; }

# ── 1. ffmpeg ─────────────────────────────────────────────────────────────────
if has ffmpeg; then
    echo -e "  ffmpeg already installed, skipping"
else
    echo -e "  Installing ffmpeg..."
    if [[ "$OS" == "Darwin" ]]; then
        if ! has brew; then
            echo -e "${RED}  Homebrew not found. Install it from https://brew.sh then re-run.${RESET}"
            exit 1
        fi
        brew install ffmpeg --quiet
    elif [[ "$OS" == "Linux" ]]; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq ffmpeg
    else
        echo -e "${RED}  Unsupported OS: $OS. Install ffmpeg manually then re-run.${RESET}"
        exit 1
    fi
    echo -e "${GREEN}  ✓ ffmpeg installed${RESET}"
fi

# ── 2. yt-dlp ────────────────────────────────────────────────────────────────
echo -e "  Installing yt-dlp..."
if [[ "$OS" == "Linux" && ("$ARCH" == "armv7l" || "$ARCH" == "armv6l") ]]; then
    # Pi Zero 2W — use standalone ARM binary (saves ~80MB RAM vs pip version)
    sudo curl -fsSL -o /usr/local/bin/yt-dlp \
        "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux_armv7"
    sudo chmod +x /usr/local/bin/yt-dlp
    echo -e "${GREEN}  ✓ yt-dlp installed (ARM binary)${RESET}"
elif [[ "$OS" == "Linux" && "$ARCH" == "aarch64" ]]; then
    # 64-bit ARM (Pi 4, Pi 5, etc.)
    sudo curl -fsSL -o /usr/local/bin/yt-dlp \
        "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux_aarch64"
    sudo chmod +x /usr/local/bin/yt-dlp
    echo -e "${GREEN}  ✓ yt-dlp installed (ARM64 binary)${RESET}"
else
    # Mac or x86 Linux — install via pipx alongside muse-cli or standalone
    if [[ "$OS" == "Darwin" ]]; then
        sudo curl -fsSL -o /usr/local/bin/yt-dlp \
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"
        sudo chmod +x /usr/local/bin/yt-dlp
    else
        sudo curl -fsSL -o /usr/local/bin/yt-dlp \
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux"
        sudo chmod +x /usr/local/bin/yt-dlp
    fi
    echo -e "${GREEN}  ✓ yt-dlp installed (standalone binary)${RESET}"
fi

# ── 3. pipx ──────────────────────────────────────────────────────────────────
if has pipx; then
    echo -e "${DIM}  pipx already installed, skipping${RESET}"
else
    echo -e "  Installing pipx..."
    if [[ "$OS" == "Darwin" ]]; then
        brew install pipx --quiet
        pipx ensurepath --quiet
    elif [[ "$OS" == "Linux" ]]; then
        sudo apt-get install -y -qq pipx
        pipx ensurepath --quiet
    fi
    echo -e "${GREEN}  ✓ pipx installed${RESET}"
fi

# ── 4. muse-cli ──────────────────────────────────────────────────────────────
echo -e "  Installing muse-cli..."
if pipx list 2>/dev/null | grep -q "muse-cli"; then
    pipx upgrade "git+$REPO" --quiet
    echo -e "${GREEN}  ✓ muse-cli updated to latest${RESET}"
else
    pipx install "git+$REPO" --quiet
    echo -e "${GREEN}  ✓ muse-cli installed${RESET}"
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}  All done! Run: muse-cli${RESET}"
echo -e "${DIM}  If 'muse-cli' is not found, restart your terminal or run: pipx ensurepath${RESET}"
echo ""
