import sys
import os

from .config import first_launch_setup, get_config, interactive_config
from .utils import check_dependencies
from .banner import print_banner
from .search import search_youtube, display_search_results
from .downloader import download_song
from .duplicate import DuplicateChecker
from .lyrics import LyricsManager

# ANSI colors
CYAN = "\033[36m"
WHITE = "\033[97m"
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"
YELLOW = "\033[33m"


def _handle_uninstall():
    import shutil
    print(f"\n{WHITE}🗑️  muse-cli uninstaller{RESET}\n")

    # Music library
    try:
        config = get_config()
        music_dir = config.get("output_base", "")
    except Exception:
        music_dir = ""

    if music_dir and os.path.exists(music_dir):
        print(f"   Music library: {music_dir}")
        keep = input(f"{YELLOW}   Keep your downloaded music? (Y/n): {RESET}").strip().lower()
        if keep == 'n':
            try:
                shutil.rmtree(music_dir)
                print(f"{GREEN}   ✅ Music library removed{RESET}")
            except Exception as e:
                print(f"{RED}   ❌ {e}{RESET}")

    # Config
    config_dir = os.path.expanduser("~/.config/muse-cli")
    if os.path.exists(config_dir):
        choice = input(f"{YELLOW}Remove config (~/.config/muse-cli)? (y/N): {RESET}").strip().lower()
        if choice == 'y':
            try:
                shutil.rmtree(config_dir)
                print(f"{GREEN}   ✅ Config removed{RESET}")
            except Exception as e:
                print(f"{RED}   ❌ {e}{RESET}")

    # ffmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        choice = input(f"{YELLOW}Remove ffmpeg? (y/N): {RESET}").strip().lower()
        if choice == 'y':
            try:
                result = subprocess.run(["brew", "list", "ffmpeg"], capture_output=True)
                if result.returncode == 0:
                    subprocess.run(["brew", "uninstall", "ffmpeg"], check=True)
                    print(f"{GREEN}   ✅ ffmpeg removed{RESET}")
                else:
                    print(f"{YELLOW}   Not installed via Homebrew, remove manually: {ffmpeg_path}{RESET}")
            except Exception as e:
                print(f"{RED}   ❌ {e}{RESET}")

    # muse-cli itself
    print(f"\n{CYAN}Removing muse-cli...{RESET}")
    try:
        import subprocess
        subprocess.run(["pipx", "uninstall", "muse-cli"], check=True)
        print(f"{GREEN}✅ Done. Goodbye!{RESET}\n")
    except Exception as e:
        print(f"{RED}❌ {e}{RESET}")
        print(f"{YELLOW}Try manually: pipx uninstall muse-cli{RESET}\n")


def main():
    """Main entry point."""

    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        _handle_uninstall()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--update":
        import subprocess
        print(f"{CYAN}🔄 Updating muse-cli from GitHub...{RESET}")
        try:
            subprocess.run(
                ["pipx", "install", "--force",
                "git+https://github.com/Ulasti/muse-cli.git"],
                check=True
            )
            print(f"{GREEN}✅ Updated successfully!{RESET}")
        except subprocess.CalledProcessError:
            print(f"{RED}❌ Update failed. Try manually: pipx install --force git+https://github.com/Ulasti/muse-cli.git{RESET}")
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        interactive_config()
        return

    config = first_launch_setup()
    check_dependencies()

    lyrics_manager   = LyricsManager(config["genius_token"])
    duplicate_checker = DuplicateChecker(config["output_base"])

    try:
        os.makedirs(config["output_base"], exist_ok=True)
    except Exception as e:
        print(f"{RED}❌ Failed to create output directory: {e}{RESET}")
        sys.exit(1)

    print_banner()

    try:
        while True:
            user_input = input(f"{CYAN}>>> {RESET}").strip()

            if not user_input:
                continue

            # ── Search mode ──────────────────────────────────────────────────
            if user_input.lower().startswith("search "):
                query = user_input[7:].strip()
                if not query:
                    continue

                print(f"{CYAN}🔍 Searching YouTube for: {query}{RESET}")
                results = search_youtube(query, max_results=5)

                if results:
                    display_search_results(results)

                    while True:
                        try:
                            choice = input(f"\n{WHITE}Enter number to download (or press Enter to cancel): {RESET}").strip()

                            if not choice:
                                break

                            idx = int(choice)
                            if 1 <= idx <= len(results):
                                selected = results[idx - 1]
                                print(f"\n{GREEN}Selected:{RESET} {selected['title']}")
                                download_song(
                                    selected['url'],
                                    config["output_base"],
                                    duplicate_checker,
                                    lyrics_manager,
                                    user_query=query,
                                    audio_format=config["audio_format"]
                                )
                                break
                            else:
                                print(f"{RED}Invalid number{RESET}")
                        except ValueError:
                            print(f"{RED}Please enter a valid number{RESET}")
                        except KeyboardInterrupt:
                            break

            # ── URL download ─────────────────────────────────────────────────
            elif user_input.startswith(("http://", "https://", "www.")):
                if user_input.startswith("www."):
                    user_input = "https://" + user_input
                download_song(
                    user_input,
                    config["output_base"],
                    duplicate_checker,
                    lyrics_manager,
                    user_query="",
                    audio_format=config["audio_format"]
                )

            # ── Direct download ──────────────────────────────────────────────
            else:
                print(f"{CYAN}🔍 Searching for top result: {user_input}{RESET}")
                results = search_youtube(user_input, max_results=1)

                if results:
                    top = results[0]
                    print(f"{GREEN}Found:{RESET} {top['title']}  {CYAN}by{RESET} {top['uploader']}")
                    download_song(
                        top['url'],
                        config["output_base"],
                        duplicate_checker,
                        lyrics_manager,
                        user_query=user_input,
                        audio_format=config["audio_format"]
                    )
                else:
                    print(f"{RED}No results found{RESET}")

            print()

    except (KeyboardInterrupt, EOFError):
        print(f"\n{CYAN}Exiting MUSE-CLI. Goodbye!{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()