import os
import sys
import subprocess

from .colors import CYAN, WHITE, GREEN, YELLOW, RED, RESET


def check_dependencies():
    """Check if required external tools are installed."""
    required_tools = ["yt-dlp", "ffmpeg"]
    missing = []

    for tool in required_tools:
        found = False
        try:
            subprocess.run(
                [tool, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            found = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            if tool == "ffmpeg":
                common_locations = [
                    "/usr/bin/ffmpeg",
                    "/usr/local/bin/ffmpeg",
                    "/opt/homebrew/bin/ffmpeg",
                    "/opt/local/bin/ffmpeg",
                ]
            elif tool == "yt-dlp":
                common_locations = [
                    "/usr/local/bin/yt-dlp",
                    "/usr/bin/yt-dlp",
                    os.path.expanduser("~/.local/bin/yt-dlp"),
                ]
            else:
                common_locations = []

            for location in common_locations:
                if os.path.exists(location) and os.access(location, os.X_OK):
                    os.environ["PATH"] = f"{os.path.dirname(location)}:{os.environ.get('PATH', '')}"
                    found = True
                    break

        if not found:
            missing.append(tool)

    if missing:
        print(f"{RED}❌ Missing required dependencies: {', '.join(missing)}{RESET}")
        print(f"{YELLOW}Install them with:{RESET}")
        for tool in missing:
            if tool == "yt-dlp":
                print(f"  pip install yt-dlp")
            elif tool == "ffmpeg":
                print(f"  brew install ffmpeg  # macOS")
                print(f"  sudo apt install ffmpeg  # Ubuntu/Debian")
        choice = input(f"\n{WHITE}Try to install missing tools automatically? (y/N): {RESET}").strip().lower()
        if choice == 'y':
            install_system_dependencies(missing)
        else:
            sys.exit(1)

    return len(missing) == 0


def install_system_dependencies(tools):
    """Attempt to install system dependencies."""
    for tool in tools:
        if tool == "yt-dlp":
            print(f"{CYAN}Installing yt-dlp...{RESET}")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install",
                    "--break-system-packages", "yt-dlp"
                ], env={**os.environ, "PIP_BREAK_SYSTEM_PACKAGES": "1"})
                print(f"{GREEN}✓ yt-dlp installed{RESET}")
            except Exception:
                print(f"{RED}Failed to install yt-dlp{RESET}")
        elif tool == "ffmpeg":
            print(f"{YELLOW}ffmpeg must be installed manually:{RESET}")
            if sys.platform == "darwin":
                print(f"  brew install ffmpeg")
            elif sys.platform.startswith("linux"):
                print(f"  sudo apt install ffmpeg")
            print(f"{YELLOW}Please install it and restart muse-cli{RESET}")
            sys.exit(1)
