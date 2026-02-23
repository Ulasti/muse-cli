import os
import sys
import subprocess
import re

# ANSI colors
CYAN = "\033[36m"
WHITE = "\033[97m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"


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
                    "/opt/homebrew/bin/ffmpeg",
                    "/usr/local/bin/ffmpeg",
                    "/opt/local/bin/ffmpeg"
                ]
                for location in common_locations:
                    if os.path.exists(location) and os.access(location, os.X_OK):
                        os.environ["PATH"] = f"{os.path.dirname(location)}:{os.environ.get('PATH', '')}"
                        found = True
                        print(f"{GREEN}✓ Found {tool} at {location}{RESET}")
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
    else:
        print(f"{GREEN}✓ All system dependencies found{RESET}")


def install_system_dependencies(tools):
    """Attempt to install system dependencies."""
    for tool in tools:
        if tool == "yt-dlp":
            print(f"{CYAN}Installing yt-dlp...{RESET}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "yt-dlp"])
                print(f"{GREEN}✓ yt-dlp installed{RESET}")
            except:
                print(f"{RED}Failed to install yt-dlp{RESET}")
        
        elif tool == "ffmpeg":
            print(f"{YELLOW}ffmpeg must be installed manually:{RESET}")
            if sys.platform == "darwin":
                print(f"  brew install ffmpeg")
            elif sys.platform.startswith("linux"):
                print(f"  sudo apt install ffmpeg")
            print(f"{YELLOW}Please install it and restart muse-cli{RESET}")
            sys.exit(1)


def clean_title(title: str) -> str:
    """Clean title for lyrics search."""
    title = re.sub(r"\(.*?\)", "", title)
    title = re.split(r"[｜|]", title)[0]
    return title.strip()


def clean_filename(name: str) -> str:
    """Remove invalid file/folder characters."""
    return re.sub(r'[\/\\\:\*\?\"\<\>\|]', '', name).strip()