import subprocess
import re

# ANSI colors
CYAN = "\033[36m"
WHITE = "\033[97m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"

_DELIM = "|||"


def _clean_uploader(uploader: str) -> str:
    """Strip common YouTube channel suffixes to get a clean artist name."""
    suffixes = [
        r'\s*-\s*Topic$',
        r'\s*VEVO$',
        r'\s*Official\s*$',
        r'\s*Music\s*$',
    ]
    for s in suffixes:
        uploader = re.sub(s, uploader, uploader, flags=re.IGNORECASE)
    # Also strip anything after | in the uploader field (album bleed)
    uploader = uploader.split('|')[0]
    return uploader.strip()


def search_youtube(query: str, max_results: int = 5) -> list:
    """Search YouTube and return list of results."""
    search_cmd = [
        "yt-dlp",
        f"ytsearch{max_results}:{query}",
        "--print", f"%(id)s{_DELIM}%(title)s{_DELIM}%(uploader)s{_DELIM}%(duration_string)s",
        "--skip-download",
        "--no-warnings",
        "--add-header", "Accept-Language:en-US,en;q=0.9",
        "--extractor-args", "youtube:lang=en",
    ]

    try:
        result = subprocess.run(
            search_cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        lines = result.stdout.strip().split("\n")
        results = []

        for line in lines:
            if line and _DELIM in line:
                parts = line.split(_DELIM, 3)
                if len(parts) >= 4:
                    video_id, title, uploader, duration = parts
                    # Clean the title — strip "| ALBUM" bleed
                    clean_title    = title.split('|')[0].strip()
                    clean_uploader = _clean_uploader(uploader)
                    results.append({
                        "title":    clean_title,
                        "raw_title": title.strip(),
                        "uploader": clean_uploader,
                        "duration": duration.strip(),
                        "id":       video_id.strip(),
                        "url":      f"https://www.youtube.com/watch?v={video_id.strip()}"
                    })

        return results
    except subprocess.CalledProcessError as e:
        print(f"{RED}❌ Search failed: {e.stderr.strip() if e.stderr else 'Unknown error'}{RESET}")
        return []
    except Exception as e:
        print(f"{RED}❌ Search failed: {e}{RESET}")
        return []


def display_search_results(results: list):
    """Display search results in a clean format."""
    if not results:
        print(f"{YELLOW}No results found{RESET}")
        return

    print(f"\n{CYAN}{'─' * 80}{RESET}")
    print(f"{WHITE}Search Results:{RESET}\n")

    for idx, result in enumerate(results, 1):
        print(f"{GREEN}{idx:2d}.{RESET} {WHITE}{result['title']}{RESET}")
        print(f"    {CYAN}Artist:{RESET} {result['uploader']} {CYAN}│{RESET} {CYAN}Duration:{RESET} {result['duration']}")
        print()

    print(f"{CYAN}{'─' * 80}{RESET}")
