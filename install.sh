#!/usr/bin/env bash

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
ERRORS=0

# Expand PATH upfront so freshly installed tools are visible immediately
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

has() { command -v "$1" &>/dev/null; }
ok()   { echo -e "${GREEN}  ✓ $1${RESET}"; }
skip() { echo -e "${DIM}  • $1 already installed, skipping${RESET}"; }
fail() { echo -e "${RED}  ✗ $1${RESET}"; ERRORS=$((ERRORS + 1)); }

INSTALLED_FFMPEG=false
INSTALLED_YTDLP=false

# ── 1. ffmpeg ─────────────────────────────────────────────────────────────────
if has ffmpeg; then
    skip "ffmpeg"
else
    echo -e "  Installing ffmpeg..."
    if [[ "$OS" == "Darwin" ]]; then
        if has brew; then
            brew install ffmpeg >/dev/null 2>&1 || true
            if has ffmpeg; then
                INSTALLED_FFMPEG=true; ok "ffmpeg installed"
            else
                fail "ffmpeg install failed — try: brew install ffmpeg"
            fi
        else
            fail "Homebrew not found — install from https://brew.sh then re-run"
        fi
    elif [[ "$OS" == "Linux" ]]; then
        sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq >/dev/null 2>&1 || true
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg >/dev/null 2>&1 || true
        if has ffmpeg; then
            INSTALLED_FFMPEG=true; ok "ffmpeg installed"
        else
            fail "ffmpeg install failed — try: sudo apt install ffmpeg"
        fi
    else
        fail "Unsupported OS: $OS — install ffmpeg manually"
    fi
fi

# ── 2. yt-dlp ────────────────────────────────────────────────────────────────
if has yt-dlp; then
    skip "yt-dlp"
else
    echo -e "  Installing yt-dlp..."
    YTDLP_URL=""
    if [[ "$OS" == "Darwin" ]]; then
        YTDLP_URL="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"
    elif [[ "$OS" == "Linux" ]]; then
        case "$ARCH" in
            armv7l|armv6l) YTDLP_URL="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux_armv7" ;;
            aarch64)       YTDLP_URL="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux_aarch64" ;;
            *)             YTDLP_URL="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux" ;;
        esac
    fi

    if [[ -n "$YTDLP_URL" ]]; then
        sudo curl -fsSL "$YTDLP_URL" -o /usr/local/bin/yt-dlp >/dev/null 2>&1 || true
        sudo chmod +x /usr/local/bin/yt-dlp >/dev/null 2>&1 || true
        if has yt-dlp; then
            INSTALLED_YTDLP=true; ok "yt-dlp installed"
        else
            # Fallback: no sudo, install to ~/.local/bin
            mkdir -p "$HOME/.local/bin"
            curl -fsSL "$YTDLP_URL" -o "$HOME/.local/bin/yt-dlp" >/dev/null 2>&1 || true
            chmod +x "$HOME/.local/bin/yt-dlp" 2>/dev/null || true
            if has yt-dlp; then
                INSTALLED_YTDLP=true; ok "yt-dlp installed (to ~/.local/bin)"
            else
                fail "yt-dlp install failed"
            fi
        fi
    else
        fail "yt-dlp: unsupported OS ($OS)"
    fi
fi

# ── 3. pipx ──────────────────────────────────────────────────────────────────
if has pipx; then
    skip "pipx"
else
    echo -e "  Installing pipx..."
    if [[ "$OS" == "Darwin" ]] && has brew; then
        brew install pipx >/dev/null 2>&1 || true
    elif [[ "$OS" == "Linux" ]]; then
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq pipx >/dev/null 2>&1 || true
        if ! has pipx; then
            python3 -m pip install --user pipx --quiet 2>/dev/null || true
        fi
    fi
    pipx ensurepath >/dev/null 2>&1 || true
    if has pipx; then
        ok "pipx installed"
    else
        fail "pipx install failed — try: brew install pipx"
    fi
    
fi

# Add to .bashrc/.zprofile permanently so muse-cli is found after restart
if ! grep -q '\.local/bin' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi
if ! grep -q '\.local/bin' "$HOME/.zprofile" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zprofile" 2>/dev/null || true
fi
export PATH="$HOME/.local/bin:$PATH"

# ── Find pipx binary ──────────────────────────────────────────────────────────
PIPX_BIN=""
for candidate in \
    "$(command -v pipx 2>/dev/null || true)" \
    "$HOME/.local/bin/pipx" \
    "/opt/homebrew/bin/pipx" \
    "/usr/local/bin/pipx" \
    "/usr/bin/pipx"
do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
        PIPX_BIN="$candidate"
        break
    fi
done

# ── 4. muse-cli ──────────────────────────────────────────────────────────────
if [[ -z "$PIPX_BIN" ]]; then
    fail "pipx not found — cannot install muse-cli. Try: pipx install git+$REPO"
else
    echo -e "  Installing muse-cli..."
    if "$PIPX_BIN" list 2>/dev/null | grep -q "muse-cli"; then
        "$PIPX_BIN" upgrade "git+$REPO" --quiet 2>/dev/null || true
        if "$PIPX_BIN" list 2>/dev/null | grep -q "muse-cli"; then
            ok "muse-cli updated to latest"
        else
            fail "muse-cli update failed — try: pipx upgrade git+$REPO"
        fi
    else
        "$PIPX_BIN" install "git+$REPO" --quiet 2>/dev/null || true
        if "$PIPX_BIN" list 2>/dev/null | grep -q "muse-cli"; then
            ok "muse-cli installed"
        else
            fail "muse-cli install failed — try: pipx install git+$REPO"
        fi
    fi
fi

# ── 5. Write provenance ───────────────────────────────────────────────────────
mkdir -p "$CONFIG_DIR"
PY_FFMPEG="False"; [[ "$INSTALLED_FFMPEG" == "true" ]] && PY_FFMPEG="True"
PY_YTDLP="False";  [[ "$INSTALLED_YTDLP"  == "true" ]] && PY_YTDLP="True"

python3 - "$CONFIG_FILE" "$PY_FFMPEG" "$PY_YTDLP" <<'PYEOF'
import json, os, sys
path, py_ffmpeg, py_ytdlp = sys.argv[1], sys.argv[2] == "True", sys.argv[3] == "True"
cfg = {}
if os.path.exists(path):
    try:
        with open(path) as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
cfg["script_installed_ffmpeg"] = py_ffmpeg
cfg["script_installed_ytdlp"]  = py_ytdlp
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
PYEOF

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
if [[ $ERRORS -eq 0 ]]; then
    echo -e "${GREEN}  ✅ Installation complete!${RESET}"
else
    echo -e "${YELLOW}  ⚠  Finished with $ERRORS error(s) — see above${RESET}"
fi
echo ""
echo -e "  Restart your terminal, then run:  ${CYAN}muse-cli${RESET}"
echo -e "${DIM}  Or without restarting: source ~/.zprofile 2>/dev/null || source ~/.bashrc 2>/dev/null && muse-cli${RESET}"
echo ""