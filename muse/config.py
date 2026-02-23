import os
import json
import sys

# ANSI colors
CYAN = "\033[36m"
WHITE = "\033[97m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"

CONFIG_DIR = os.path.expanduser("~/.config/muse-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "genius_token": "",
    "output_base": os.path.expanduser("~/Documents/Music"),
    "first_launch": True
}


def ensure_config_dir():
    """Create config directory if it doesn't exist."""
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config():
    """Load configuration from file."""
    ensure_config_dir()
    
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Merge with defaults for any missing keys
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception as e:
        print(f"{RED}Error loading config: {e}{RESET}")
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save configuration to file."""
    ensure_config_dir()
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"{RED}Error saving config: {e}{RESET}")


def first_launch_setup():
    """Interactive setup for first launch."""
    config = load_config()
    
    if not config.get("first_launch", True):
        return config
    
    print(f"\n{CYAN}{'═' * 60}{RESET}")
    print(f"{WHITE}Welcome to MUSE-CLI! 🎵{RESET}")
    print(f"{CYAN}{'═' * 60}{RESET}\n")
    
    # Check and install dependencies
    print(f"{CYAN}📦 Checking Python dependencies...{RESET}")
    missing_deps = check_python_dependencies()
    
    if missing_deps:
        print(f"{YELLOW}Missing dependencies: {', '.join(missing_deps)}{RESET}")
        install = input(f"{WHITE}Install them now? (Y/n): {RESET}").strip().lower()
        
        if install != 'n':
            install_dependencies(missing_deps)
        else:
            print(f"{RED}Cannot proceed without dependencies. Exiting.{RESET}")
            sys.exit(1)
    else:
        print(f"{GREEN}✓ All Python dependencies installed{RESET}")
    
    # Genius API token setup
    print(f"\n{CYAN}🎤 Genius API Setup (Optional - for lyrics){RESET}")
    print(f"{WHITE}Get your free token at: https://genius.com/api-clients{RESET}")
    token = input(f"{WHITE}Enter your Genius API token (or press Enter to skip): {RESET}").strip()
    
    if token:
        config["genius_token"] = token
        print(f"{GREEN}✓ Genius API token saved{RESET}")
    else:
        print(f"{YELLOW}⚠️  Lyrics will be unavailable without a token{RESET}")
    
    # Output directory
    print(f"\n{CYAN}📁 Output Directory{RESET}")
    default_output = config["output_base"]
    custom_output = input(f"{WHITE}Music folder [{default_output}]: {RESET}").strip()
    
    if custom_output:
        config["output_base"] = os.path.expanduser(custom_output)
    
    # Mark first launch as complete
    config["first_launch"] = False
    save_config(config)
    
    print(f"\n{GREEN}✓ Setup complete! Starting MUSE-CLI...{RESET}\n")
    return config


def check_python_dependencies():
    """Check which Python dependencies are missing."""
    missing = []
    required = ["yt_dlp", "mutagen", "lyricsgenius"]
    
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    return missing


def install_dependencies(deps):
    """Install missing Python dependencies."""
    import subprocess
    
    print(f"\n{CYAN}Installing dependencies...{RESET}")
    
    # Map module names to package names
    package_map = {
        "yt_dlp": "yt-dlp",
        "mutagen": "mutagen",
        "lyricsgenius": "lyricsgenius"
    }
    
    packages = [package_map.get(dep, dep) for dep in deps]
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--break-system-packages"
        ] + packages)
        print(f"{GREEN}✓ Dependencies installed successfully{RESET}")
    except subprocess.CalledProcessError:
        print(f"{RED}❌ Failed to install dependencies{RESET}")
        print(f"{YELLOW}Please run manually: pip install {' '.join(packages)}{RESET}")
        sys.exit(1)


def interactive_config():
    """Interactive configuration editor."""
    config = load_config()
    
    print(f"\n{CYAN}{'═' * 60}{RESET}")
    print(f"{WHITE}MUSE-CLI Configuration{RESET}")
    print(f"{CYAN}{'═' * 60}{RESET}\n")
    
    # Show current config
    print(f"{WHITE}Current Settings:{RESET}")
    print(f"  {CYAN}1.{RESET} Genius API Token: {config['genius_token'][:20] + '...' if config['genius_token'] else 'Not set'}")
    print(f"  {CYAN}2.{RESET} Output Directory: {config['output_base']}")
    print(f"  {CYAN}3.{RESET} Reset to defaults")
    print(f"  {CYAN}4.{RESET} Exit")
    
    choice = input(f"\n{WHITE}Select option (1-4): {RESET}").strip()
    
    if choice == "1":
        token = input(f"{WHITE}Enter new Genius API token: {RESET}").strip()
        if token:
            config["genius_token"] = token
            save_config(config)
            print(f"{GREEN}✓ Token updated{RESET}")
    
    elif choice == "2":
        path = input(f"{WHITE}Enter new output directory: {RESET}").strip()
        if path:
            config["output_base"] = os.path.expanduser(path)
            save_config(config)
            print(f"{GREEN}✓ Output directory updated{RESET}")
    
    elif choice == "3":
        confirm = input(f"{YELLOW}Reset all settings to defaults? (y/N): {RESET}").strip().lower()
        if confirm == 'y':
            config = DEFAULT_CONFIG.copy()
            config["first_launch"] = False
            save_config(config)
            print(f"{GREEN}✓ Settings reset to defaults{RESET}")
    
    elif choice == "4":
        return
    
    else:
        print(f"{RED}Invalid option{RESET}")


def get_config():
    """Get current configuration."""
    return load_config()