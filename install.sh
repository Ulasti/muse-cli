#!/usr/bin/env bash

# Do NOT use set -e — we handle errors manually so the script never dies silently
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

has() { command -v "$1" &>/dev/null; }

INSTALLED_FFMPEG=false
INSTALLED_YTDLP=false

# ── Helper: print step result ─────────────────────────────────────────────────
ok()   { echo -e "${GREEN}  ✓ $1${RESET}"; }
skip() { echo -e "${DIM}  • $1 already installed, skipping${RESET}"; }
fail() { echo -e "${RED}  ✗ $1${RESET}"; ERRORS=$((ERRORS + 1)); }

# ── 1. ffmpeg ─────────────────────────────────────────────────────────────────
if has ffmpeg; then
    skip "ffmpeg"
else
    echo -e "  Installing ffmpeg..."
    if [[ "$OS" == "Darwin" ]]; then
        if has brew; then
            brew install ffmpeg >/dev/null 2>&1 && INSTALLED_FFMPEG=true && ok "ffmpeg installed" \
                || fail "ffmpeg install failed — try: brew install ffmpeg"
        else
            fail "Homebrew not found — install from https://brew.sh then re-run"
        fi
    elif [[ "$OS" == "Linux" ]]; then
        sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq >/dev/null 2>&1
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg >/dev/null 2>&1 \
            && INSTALLED_FFMPEG=true && ok "ffmpeg installed" \
            || fail "ffmpeg install failed — try: sudo apt install ffmpeg"
    else
        fail "Unsupported OS: $OS — install ffmpeg manually"
    fi
fi

# ── 2. yt-dlp (standalone binary — no pip needed) ────────────────────────────
if has yt-dlp; then
    skip "yt-dlp"
else
    echo -e "  Installing yt-dlp..."
    YTDLP_URL=""
    YTDLP_DEST="/usr/local/bin/yt-dlp"

    if [[ "$OS" == "Darwin" ]]; then
        YTDLP_URL="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"
    elif [[ "$OS" == "Linux" ]]; then
        case "$ARCH" in
            armv7l|armv6l) YTDLP_URL="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux_armv7" ;;
            aarch64)        YTDLP_URL="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux_aarch64" ;;
            *)              YTDLP_URL="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux" ;;
        esac
    fi

    if [[ -n "$YTDLP_URL" ]]; then
        if sudo curl -fsSL "$YTDLP_URL" -o "$YTDLP_DEST" 2>/dev/null \
            && sudo chmod +x "$YTDLP_DEST" 2>/dev/null; then
            INSTALLED_YTDLP=true
            ok "yt-dlp installed"
        else
            # Fallback: try without sudo to ~/bin
            mkdir -p "$HOME/.local/bin"
            YTDLP_DEST="$HOME/.local/bin/yt-dlp"
            if curl -fsSL "$YTDLP_URL" -o "$YTDLP_DEST" 2>/dev/null \
                && chmod +x "$YTDLP_DEST" 2>/dev/null; then
                INSTALLED_YTDLP=true
                export PATH="$HOME/.local/bin:$PATH"
                ok "yt-dlp installed (to ~/.local/bin)"
            else
                fail "yt-dlp install failed"
            fi
        fi
    else
        fail "yt-dlp: unsupported OS"
    fi
fi

# ── 3. pipx ──────────────────────────────────────────────────────────────────
PIPX_BIN=""
find_pipx() {
    for candidate in \
        "$(command -v pipx 2>/dev/null)" \
        "$HOME/.local/bin/pipx" \
        "/opt/homebrew/bin/pipx" \
        "/usr/local/bin/pipx" \
        "/usr/bin/pipx"
    do
        if [[ -x "$candidate" ]]; then
            PIPX_BIN="$candidate"
            return 0
        fi
    done
    return 1
}

if find_pipx; then
    skip "pipx (found at $PIPX_BIN)"
else
    echo -e "  Installing pipx..."
    if [[ "$OS" == "Darwin" ]] && has brew; then
        brew install pipx >/dev/null 2>&1 \
            && ok "pipx installed" \
            || fail "pipx install failed — try: brew install pipx"
    elif [[ "$OS" == "Linux" ]]; then
        # Try apt first, fall back to pip
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq pipx >/dev/null 2>&1 \
            || python3 -m pip install --user pipx --quiet 2>/dev/null \
            || fail "pipx install failed"
        ok "pipx installed"
    fi

    # Ensure pipx path
    if has pipx; then
        pipx ensurepath --quiet 2>/dev/null || true
    fi

    # Add common pipx locations to PATH for rest of this script
    export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
    find_pipx || fail "pipx not found after install"
fi

# ── 4. muse-cli ──────────────────────────────────────────────────────────────
if [[ -z "$PIPX_BIN" ]]; then
    fail "Cannot install muse-cli — pipx not available"
else
    echo -e "  Installing muse-cli..."
    if "$PIPX_BIN" list 2>/dev/null | grep -q "muse-cli"; then
        "$PIPX_BIN" upgrade "git+$REPO" --quiet 2>/dev/null \
            && ok "muse-cli updated to latest" \
            || fail "muse-cli update failed"
    else
        "$PIPX_BIN" install "git+$REPO" --quiet 2>/dev/null \
            && ok "muse-cli installed" \
            || fail "muse-cli install failed — try: pipx install git+$REPO"
    fi
fi

# ── 5. Write install provenance ───────────────────────────────────────────────
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

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
if [[ $ERRORS -eq 0 ]]; then
    echo -e "${GREEN}  ✅ Installation complete!${RESET}"
else
    echo -e "${YELLOW}  ⚠  Installation finished with $ERRORS error(s) — see above${RESET}"
fi
echo ""
echo -e "  Restart your terminal, then run:  ${CYAN}muse-cli${RESET}"
echo -e "${DIM}  Or without restarting: source ~/.zprofile 2>/dev/null || source ~/.bashrc 2>/dev/null && muse-cli${RESET}"
echo ""