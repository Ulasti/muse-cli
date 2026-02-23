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
            echo -e "${RED}  Homebrew not found. Install from https://brew.sh then re-run.${RESET}"
            exit 1
        fi
        # Redirect all brew output to /dev/null to avoid corrupting the pipe
        brew install ffmpeg >/dev/null 2>&1
    elif [[ "$OS" == "Linux" ]]; then
        sudo apt-get update -qq >/dev/null 2>&1
        sudo apt-get install -y -qq ffmpeg >/dev/null 2>&1
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
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux_armv7" 2>/dev/null
        sudo chmod +x /usr/local/bin/yt-dlp
        echo -e "${GREEN}  ✓ yt-dlp installed (ARM binary)${RESET}"
    elif [[ "$OS" == "Linux" && "$ARCH" == "aarch64" ]]; then
        sudo curl -fsSL -o /usr/local/bin/yt-dlp \
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux_aarch64" 2>/dev/null
        sudo chmod +x /usr/local/bin/yt-dlp
        echo -e "${GREEN}  ✓ yt-dlp installed (ARM64 binary)${RESET}"
    elif [[ "$OS" == "Darwin" ]]; then
        sudo curl -fsSL -o /usr/local/bin/yt-dlp \
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos" 2>/dev/null
        sudo chmod +x /usr/local/bin/yt-dlp
        echo -e "${GREEN}  ✓ yt-dlp installed${RESET}"
    else
        sudo curl -fsSL -o /usr/local/bin/yt-dlp \
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux" 2>/dev/null
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
        brew install pipx >/dev/null 2>&1
    elif [[ "$OS" == "Linux" ]]; then
        sudo apt-get install -y -qq pipx >/dev/null 2>&1
    fi
    pipx ensurepath --quiet
    echo -e "${GREEN}  ✓ pipx installed${RESET}"
fi

# ── 4. muse-cli ──────────────────────────────────────────────────────────────
echo -e "  Installing muse-cli..."

# Find pipx — may not be on PATH yet if just installed
PIPX_BIN="$(command -v pipx 2>/dev/null || echo "")"
if [[ -z "$PIPX_BIN" ]]; then
    for candidate in "$HOME/.local/bin/pipx" "/opt/homebrew/bin/pipx" "/usr/local/bin/pipx"; do
        if [[ -x "$candidate" ]]; then
            PIPX_BIN="$candidate"
            break
        fi
    done
fi

if [[ -z "$PIPX_BIN" ]]; then
    echo -e "${RED}  pipx not found after install — try restarting terminal and running: pipx install git+$REPO${RESET}"
    exit 1
fi

if "$PIPX_BIN" list 2>/dev/null | grep -q "muse-cli"; then
    "$PIPX_BIN" upgrade "git+$REPO" --quiet
    echo -e "${GREEN}  ✓ muse-cli updated to latest${RESET}"
else
    "$PIPX_BIN" install "git+$REPO" --quiet
    echo -e "${GREEN}  ✓ muse-cli installed${RESET}"
fi

# ── 5. Write install provenance ───────────────────────────────────────────────
mkdir -p "$CONFIG_DIR"

PY_FFMPEG="False"
PY_YTDLP="False"
[[ "$INSTALLED_FFMPEG" == "true" ]] && PY_FFMPEG="True"
[[ "$INSTALLED_YTDLP"  == "true" ]] && PY_YTDLP="True"

if [[ -f "$CONFIG_FILE" ]]; then
    python3 - <<PYEOF
import json
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

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}  ✅ All done!${RESET}"
echo ""
echo -e "  To start muse-cli, restart your terminal then run:"
echo -e "${CYAN}      muse-cli${RESET}"
echo ""
echo -e "${DIM}  Or run now without restarting:${RESET}"
echo -e "${CYAN}      source ~/.zprofile 2>/dev/null || source ~/.bash_profile 2>/dev/null && muse-cli${RESET}"
echo ""