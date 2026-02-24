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
SCROLL_START = 11  # first row of the user-input scroll region


def print_banner():
    """Draw the banner with a status line, then lock it with a scroll region."""
    # Clear screen, cursor to 1,1
    sys.stdout.write("\033[2J\033[H")

    for line in BANNER_LINES:
        if "▄▀▄" in line or "▀▀█" in line:
            print(f"{CYAN}{line}{RESET}")
        else:
            print(f"{WHITE}{line}{RESET}")

    print(f"{CYAN}{SEPARATOR}{RESET}")          # row 8
    print(f"{WHITE}{PROMPT_TEXT}{RESET}")         # row 9  (STATUS_ROW)
    print(f"{CYAN}{SEPARATOR}{RESET}")          # row 10

    # Lock rows 1-10: set scroll region to rows 11+
    sys.stdout.write(f"\033[{SCROLL_START};999r")
    # Move cursor into the scroll region
    sys.stdout.write(f"\033[{SCROLL_START};1H")
    sys.stdout.flush()
