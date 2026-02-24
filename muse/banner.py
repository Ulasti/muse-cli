from .colors import CYAN, WHITE, RESET

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
    for line in BANNER_LINES:
        if "▄▀▄" in line or "▀▀█" in line:
            print(f"{CYAN}{line}{RESET}")
        else:
            print(f"{WHITE}{line}{RESET}")
    print(f"{CYAN}{SEPARATOR}{RESET}")
    print(f"{WHITE}{PROMPT_TEXT}{RESET}")
    print(f"{CYAN}{SEPARATOR}{RESET}")
