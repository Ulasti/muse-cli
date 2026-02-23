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

OS="$(uname -s)"
ARCH="$(uname -m)"

has() { command -v "$1" &>/dev/null; }

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

# Convert bash booleans to Python booleans explicitly
PY_FFMPEG="False"
PY_YTDLP="False"
[[ "$INSTALLED_FFMPEG" == "true" ]] && PY_FFMPEG="True"
[[ "$INSTALLED_YTDLP"  == "true" ]] && PY_YTDLP="True"

if [[ -f "$CONFIG_FILE" ]]; then
    python3 - <<PYEOF
import json, os
path = "$CONFIG_FILE"
with open(path) as f:
    cfg = json.load(f)
cfg["script_installed_ffmpeg"] = $PY_FFMPEG
cfg["script_installed_ytdlp"]  = $PY_YTDLP
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
PYEOF
else
    python3 - <<PYEOF
import json, os
path = "$CONFIG_FILE"
os.makedirs(os.path.dirname(path), exist_ok=True)
seed = {
    "script_installed_ffmpeg": $PY_FFMPEG,
    "script_installed_ytdlp":  $PY_YTDLP,
}
with open(path, "w") as f:
    json.dump(seed, f, indent=2)
PYEOF
fi

echo ""
echo -e "${GREEN}  All done! Run: muse-cli${RESET}"
echo -e "${DIM}  If 'muse-cli' is not found, restart your terminal or run: pipx ensurepath${RESET}"
echo ""