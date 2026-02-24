import sys

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

# The status line sits at this terminal row (between the two separators).
# Banner art = 7 lines (rows 1-7), separator (row 8), status (row 9), separator (row 10).
STATUS_ROW = 9
BANNER_HEIGHT = 10  # total rows the banner occupies (art + separators + status)


def print_banner():
    """Clear screen and draw the banner with a status line between separators."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

    for line in BANNER_LINES:
        if "▄▀▄" in line or "▀▀█" in line:
            print(f"{CYAN}{line}{RESET}")
        else:
            print(f"{WHITE}{line}{RESET}")

    print(f"{CYAN}{SEPARATOR}{RESET}")          # row 8
    print(f"{WHITE}{PROMPT_TEXT}{RESET}")         # row 9  (STATUS_ROW)
    print(f"{CYAN}{SEPARATOR}{RESET}")          # row 10
