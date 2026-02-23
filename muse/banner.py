import os

# ANSI colors
CYAN = "\033[36m"
WHITE = "\033[97m"
YELLOW = "\033[33m"
RESET = "\033[0m"

BANNER_LINES = [
    "   ▄▀▄     ▄▀▄          ███╗   ███╗██╗   ██╗███████╗███████╗",
    "  ▄█▀▀▀▀▀▀▀▀▀█▄     █   ████╗ ████║██║   ██║██╔════╝██╔════╝",
    " ▄▄█▄▄▄▄▄▄▄▄▄▄█▄▄   █   ██╔████╔██║██║   ██║███████╗█████╗",
    " ▀▀█  █     █  █▀▀  █   ██║╚██╔╝██║██║   ██║╚════██║██╔══╝",
    "    ▀▀▀▀▀▀▀▀▀▀▀     █   ██║ ╚═╝ ██║╚██████╔╝███████║███████╗",
    "    by ulasti           ╚═╝     ╚═╝ ╚═════╝╚══════╝╚══════╝",
    "                                 M U S E - C L I"
]

SEPARATOR = "∙" * 60
PROMPT_TEXT = "Type song title and artist name to download instantly"
def print_banner():
    """Display the CLI banner."""
    os.system("clear" if os.name != "nt" else "cls")
    for line in BANNER_LINES:
        if "▄▀▄" in line or "▀▀█" in line:
            print(f"{CYAN}{line}{RESET}")
        else:
            print(f"{WHITE}{line}{RESET}")
    print(f"{CYAN}{SEPARATOR}{RESET}")
    print(f"{WHITE}{PROMPT_TEXT}{RESET}")
    print(f"{CYAN}{SEPARATOR}{RESET}")
