#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/Ulasti/muse-cli"
CONFIG_DIR="$HOME/.config/muse-cli"
CONFIG_FILE="$CONFIG_DIR/config.json"

GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
DIM="\033[2m"
CYAN="\033[36m"
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

has() { command -v "$1" &>/dev/null; }

# Track what this script installs so uninstall knows what to offer to remove
INSTALLED_FFMPEG=false
INSTALLED_YTDLP=false

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
    INSTALLED_FFMPEG=true
    echo -e "${GREEN}  ✓ ffmpeg installed${RESET}"
fi

# ── 2. yt-dlp ────────────────────────────────────────────────────────────────
if has yt-dlp; then
    echo -e "  yt-dlp already installed, skipping"
else
    echo -e "  Installing yt-dlp..."
    if [[ "$OS" == "Linux" && ("$ARCH" == "armv7l" || "$ARCH" == "armv6l") ]]; then
        sudo curl -fsSL -o /usr/local/bin/yt-dlp \
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux_armv7"
        sudo chmod +x /usr/local/bin/yt-dlp
        echo -e "${GREEN}  ✓ yt-dlp installed (ARM binary)${RESET}"
    elif [[ "$OS" == "Linux" && "$ARCH" == "aarch64" ]]; then
        sudo curl -fsSL -o /usr/local/bin/yt-dlp \
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux_aarch64"
        sudo chmod +x /usr/local/bin/yt-dlp
        echo -e "${GREEN}  ✓ yt-dlp installed (ARM64 binary)${RESET}"
    elif [[ "$OS" == "Darwin" ]]; then
        sudo curl -fsSL -o /usr/local/bin/yt-dlp \
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"
        sudo chmod +x /usr/local/bin/yt-dlp
        echo -e "${GREEN}  ✓ yt-dlp installed${RESET}"
    else
        sudo curl -fsSL -o /usr/local/bin/yt-dlp \
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux"
        sudo chmod +x /usr/local/bin/yt-dlp
        echo -e "${GREEN}  ✓ yt-dlp installed${RESET}"
    fi
    INSTALLED_YTDLP=true
fi

# ── 3. pipx ──────────────────────────────────────────────────────────────────
if has pipx; then
    echo -e "  pipx already installed, skipping"
else
    echo -e "  Installing pipx..."
    if [[ "$OS" == "Darwin" ]]; then
        brew install pipx --quiet
    elif [[ "$OS" == "Linux" ]]; then
        sudo apt-get install -y -qq pipx
    fi
    pipx ensurepath --quiet
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

# ── 5. Write install provenance to config ────────────────────────────────────
mkdir -p "$CONFIG_DIR"

# Merge into existing config if present, otherwise create minimal provenance file
if [[ -f "$CONFIG_FILE" ]]; then
    # Use python to safely merge — it will already be installed via pipx deps
    python3 - <<PYEOF
import json, os
path = os.path.expanduser("$CONFIG_FILE")
with open(path) as f:
    cfg = json.load(f)
cfg["script_installed_ffmpeg"] = $INSTALLED_FFMPEG
cfg["script_installed_ytdlp"]  = $INSTALLED_YTDLP
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
PYEOF
else
    # Config doesn't exist yet (first launch will create the full one)
    # Write a provenance-only seed file that first_launch_setup will merge
    python3 - <<PYEOF
import json, os
path = os.path.expanduser("$CONFIG_FILE")
os.makedirs(os.path.dirname(path), exist_ok=True)
seed = {
    "script_installed_ffmpeg": $INSTALLED_FFMPEG,
    "script_installed_ytdlp":  $INSTALLED_YTDLP,
}
with open(path, "w") as f:
    json.dump(seed, f, indent=2)
PYEOF
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}  All done! Run: muse-cli${RESET}"
echo -e "${DIM}  If 'muse-cli' is not found, restart your terminal or run: pipx ensurepath${RESET}"
echo ""
