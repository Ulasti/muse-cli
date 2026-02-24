import os

from .colors import CYAN, WHITE, GREEN, RESET

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


def print_banner(stats=None):
    """Display the CLI banner, optionally with session stats."""
    os.system('clear')
    for line in BANNER_LINES:
        if "▄▀▄" in line or "▀▀█" in line:
            print(f"{CYAN}{line}{RESET}")
        else:
            print(f"{WHITE}{line}{RESET}")
    print(f"{CYAN}{SEPARATOR}{RESET}")
    if stats and stats.get("completed", 0) > 0:
        print(f"  {GREEN}✅ {stats['completed']} songs downloaded this session{RESET}")
    else:
        print(f"{WHITE}{PROMPT_TEXT}{RESET}")
    print(f"{CYAN}{SEPARATOR}{RESET}")
