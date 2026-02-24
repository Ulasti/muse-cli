import sys
import os
import queue
import threading
import shutil
import platform

from .config import first_launch_setup, get_config, interactive_config, CONFIG_DIR
from .utils import check_dependencies
from .banner import print_banner, STATUS_ROW, BANNER_HEIGHT
from .search import search_youtube, display_search_results
from .downloader import download_song
from .duplicate import DuplicateChecker
from .lyrics import LyricsManager
from .colors import CYAN, WHITE, GREEN, RED, RESET, YELLOW, DIM


# ── Compact single-line output helpers ────────────────────────────────────────

# Tracks how many lines the main thread has printed below the banner.
# When this approaches the terminal height the banner is about to scroll
# off-screen, so we redraw it.
_lines_below_banner = 0


def _compact_line(text):
    """Overwrite the banner status line (row 9) using absolute positioning.

    Uses DECSC / DECRC (ESC 7 / ESC 8) for save-restore — more reliable
    across terminals than the SCO sequences (CSI s / CSI u).
    """
    cols = shutil.get_terminal_size((80, 24)).columns
    truncated = text[:cols - 1] if len(text) >= cols else text
    padding = " " * max(0, cols - len(truncated) - 1)
    sys.stdout.write(f"\0337\033[{STATUS_ROW};1H{truncated}{padding}\0338")
    sys.stdout.flush()


def _read_input(prompt):
    """Show prompt and read a line from stdin (no readline, no cursor conflicts)."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        line = sys.stdin.readline()
        if not line:          # EOF
            return None
        return line.strip()
    except KeyboardInterrupt:
        raise


def _maybe_redraw_banner(stats):
    """Redraw the banner if it's about to scroll off-screen."""
    global _lines_below_banner
    rows = shutil.get_terminal_size((80, 24)).lines
    # Redraw when the output area is nearly full
    if _lines_below_banner >= rows - BANNER_HEIGHT - 2:
        print_banner()
        # Update status line with current progress if available
        current = stats.get("current_status")
        if current:
            _compact_line(current)
        _lines_below_banner = 0


def _tracked_print(*args, **kwargs):
    """print() wrapper that counts lines for banner-redraw tracking."""
    global _lines_below_banner
    print(*args, **kwargs)
    _lines_below_banner += 1


def _queue_worker(q, config, duplicate_checker, lyrics_manager, stats):
    """Daemon thread: pulls items from the queue and downloads sequentially."""
    while True:
        item = q.get()
        if item is None:
            q.task_done()
            break

        entry = item["entry"]
        user_query = item["user_query"]

        def compact_cb(stage, detail):
            icon = {"searching": "⏳", "found": "⏳", "metadata": "⏳",
                    "downloading": "⏳", "lyrics": "⏳",
                    "done": "✅", "skip": "⏭️ ", "error": "❌"}.get(stage, "⏳")
            pending = q.qsize()
            suffix = f"  [{pending} pending]" if pending > 0 else ""
            line = f"{icon} {detail}{suffix}"
            stats["current_status"] = line
            _compact_line(line)

        try:
            if entry.startswith(("http://", "https://", "www.")):
                url = entry
                if url.startswith("www."):
                    url = "https://" + url
                download_song(
                    url,
                    config["output_base"],
                    duplicate_checker,
                    lyrics_manager,
                    user_query=user_query,
                    audio_format=config["audio_format"],
                    batch_mode=True,
                    on_progress=compact_cb,
                )
            else:
                compact_cb("searching", f"searching: {entry}")
                results = search_youtube(entry, max_results=1)
                if results:
                    top = results[0]
                    compact_cb("found", f"{top['title']} · found, downloading...")
                    download_song(
                        top["url"],
                        config["output_base"],
                        duplicate_checker,
                        lyrics_manager,
                        user_query=entry,
                        audio_format=config["audio_format"],
                        batch_mode=True,
                        on_progress=compact_cb,
                    )
                else:
                    compact_cb("error", f"{entry} · no results found")
        except KeyboardInterrupt:
            q.task_done()
            return
        except Exception as e:
            compact_cb("error", f"{entry} · {e}")

        stats["completed"] += 1
        q.task_done()

        # If queue is empty, show session summary on the status line
        if q.empty():
            n = stats["completed"]
            line = f"✅ {n} song{'s' if n != 1 else ''} downloaded this session"
            stats["current_status"] = line
            _compact_line(line)


# ── Batch mode (--batch flag) — unchanged ─────────────────────────────────────

def _collect_batch_entries() -> list[str]:
    """Prompt user to enter songs one per line. Returns list of entries."""
    print(f"\n{CYAN}📦 Batch mode — enter songs, URLs, or drag a .txt file (empty line to start){RESET}")
    entries = []
    counter = 1
    try:
        while True:
            line = input(f" {DIM}{counter}:{RESET} ").strip()
            if not line:
                break

            # Detect .txt file path — expand its contents
            candidate = line.strip("'\"")  # strip quotes from drag-and-drop
            if candidate.endswith('.txt') and os.path.isfile(candidate):
                try:
                    with open(candidate, 'r') as f:
                        file_lines = [l.strip() for l in f if l.strip()]
                    if file_lines:
                        for i, fl in enumerate(file_lines):
                            prefix = "├─" if i < len(file_lines) - 1 else "└─"
                            print(f"    {DIM}{prefix} {fl}{RESET}")
                            entries.append(fl)
                        counter += 1
                        continue
                except Exception as e:
                    print(f"    {YELLOW}⚠  Could not read file: {e}{RESET}")

            entries.append(line)
            counter += 1
    except (KeyboardInterrupt, EOFError):
        print()

    return entries


def _process_batch(entries: list[str], config, duplicate_checker, lyrics_manager):
    """Process a list of batch entries sequentially."""
    if not entries:
        print(f"{YELLOW}No entries to process.{RESET}")
        return

    print(f"\n{CYAN}Processing {len(entries)} songs...{RESET}\n")

    for i, entry in enumerate(entries, 1):
        print(f"{CYAN}[{i}/{len(entries)}]{RESET} {entry}")

        if entry.startswith(("http://", "https://", "www.")):
            url = entry
            if url.startswith("www."):
                url = "https://" + url
            download_song(
                url,
                config["output_base"],
                duplicate_checker,
                lyrics_manager,
                user_query="",
                audio_format=config["audio_format"],
                batch_mode=True,
            )
        else:
            results = search_youtube(entry, max_results=1)
            if results:
                top = results[0]
                print(f"{GREEN}Found:{RESET} {top['title']}  {CYAN}by{RESET} {top['uploader']}")
                download_song(
                    top['url'],
                    config["output_base"],
                    duplicate_checker,
                    lyrics_manager,
                    user_query=entry,
                    audio_format=config["audio_format"],
                    batch_mode=True,
                )
            else:
                print(f"{RED}No results found{RESET}")

        print()

    print(f"{GREEN}✅ Batch complete — processed {len(entries)} songs{RESET}")


def _handle_uninstall():
    import shutil
    import subprocess
    import platform

    WHITE  = "\033[97m"
    GREEN  = "\033[32m"
    RED    = "\033[31m"
    YELLOW = "\033[33m"
    CYAN   = "\033[36m"
    RESET  = "\033[0m"

    print(f"\n{WHITE}🗑️  muse-cli uninstaller{RESET}\n")

    # ── Load config FIRST before anything is deleted ──────────────────────────
    try:
        config = get_config()
    except Exception:
        config = {}

    music_dir               = config.get("output_base", "")
    script_installed_ffmpeg = config.get("script_installed_ffmpeg", False)
    script_installed_ytdlp  = config.get("script_installed_ytdlp",  False)

    # ── Find pipx path now, before config/env might be affected ──────────────
    pipx_path = shutil.which("pipx") or ""
    if not pipx_path:
        # Common install locations
        for candidate in [
            os.path.expanduser("~/.local/bin/pipx"),
            "/usr/local/bin/pipx",
            "/opt/homebrew/bin/pipx",
        ]:
            if os.path.exists(candidate):
                pipx_path = candidate
                break

    # ── Music library ─────────────────────────────────────────────────────────
    if music_dir and os.path.exists(music_dir):
        print(f"   Music library: {music_dir}")
        keep = input(f"{YELLOW}   Keep your downloaded music? (Y/n): {RESET}").strip().lower()
        if keep == 'n':
            try:
                shutil.rmtree(music_dir)
                print(f"{GREEN}   ✅ Music library removed{RESET}")
            except Exception as e:
                print(f"{RED}   ❌ Could not remove music library: {e}{RESET}")

    # ── Config ────────────────────────────────────────────────────────────────
    config_dir = os.path.expanduser("~/.config/muse-cli")
    if os.path.exists(config_dir):
        choice = input(f"{YELLOW}   Remove config (~/.config/muse-cli)? (y/N): {RESET}").strip().lower()
        if choice == 'y':
            try:
                shutil.rmtree(config_dir)
                print(f"{GREEN}   ✅ Config removed{RESET}")
            except Exception as e:
                print(f"{RED}   ❌ Could not remove config: {e}{RESET}")

    # ── yt-dlp ────────────────────────────────────────────────────────────────
    ytdlp_path = shutil.which("yt-dlp") or "/usr/local/bin/yt-dlp"
    if os.path.exists(ytdlp_path):
        if script_installed_ytdlp:
            choice = input(f"{YELLOW}   Remove yt-dlp (installed by muse-cli)? (y/N): {RESET}").strip().lower()
            if choice == 'y':
                try:
                    subprocess.run(["sudo", "rm", ytdlp_path], check=True)
                    print(f"{GREEN}   ✅ yt-dlp removed{RESET}")
                except Exception as e:
                    print(f"{RED}   ❌ Could not remove yt-dlp: {e}{RESET}")
                    print(f"{YELLOW}   Try manually: sudo rm {ytdlp_path}{RESET}")
        else:
            print(f"   yt-dlp was not installed by muse-cli — skipping")

    # ── ffmpeg ────────────────────────────────────────────────────────────────
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        if script_installed_ffmpeg:
            choice = input(f"{YELLOW}   Remove ffmpeg (installed by muse-cli)? (y/N): {RESET}").strip().lower()
            if choice == 'y':
                try:
                    if platform.system() == "Darwin":
                        result = subprocess.run(
                            ["brew", "list", "ffmpeg"],
                            capture_output=True
                        )
                        if result.returncode == 0:
                            subprocess.run(["brew", "uninstall", "ffmpeg"], check=True)
                            print(f"{GREEN}   ✅ ffmpeg removed{RESET}")
                        else:
                            print(f"{YELLOW}   ffmpeg not managed by Homebrew.{RESET}")
                            print(f"{YELLOW}   Remove manually: sudo rm {ffmpeg_path}{RESET}")
                    else:
                        subprocess.run(["sudo", "apt-get", "remove", "-y", "ffmpeg"], check=True)
                        print(f"{GREEN}   ✅ ffmpeg removed{RESET}")
                except Exception as e:
                    print(f"{RED}   ❌ Could not remove ffmpeg: {e}{RESET}")
        else:
            print(f"   ffmpeg was not installed by muse-cli — skipping")

    # ── muse-cli itself ───────────────────────────────────────────────────────
    print(f"\n{CYAN}   Removing muse-cli...{RESET}")
    if not pipx_path:
        print(f"{RED}   ❌ pipx not found — cannot auto-uninstall{RESET}")
        print(f"{YELLOW}   Try manually: pipx uninstall muse-cli{RESET}\n")
        return
    try:
        subprocess.run([pipx_path, "uninstall", "muse-cli"], check=True)
        print(f"{GREEN}✅ Done. Goodbye!{RESET}\n")
    except Exception as e:
        print(f"{RED}❌ {e}{RESET}")
        print(f"{YELLOW}   Try manually: {pipx_path} uninstall muse-cli{RESET}\n")



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

    is_batch = len(sys.argv) > 1 and sys.argv[1] == "--batch"

    config = first_launch_setup()
    if not config.get("deps_verified"):
        check_dependencies()
        config["deps_verified"] = True
        from .config import save_config
        save_config(config)

    lyrics_manager   = LyricsManager(config["genius_token"])
    duplicate_checker = DuplicateChecker(CONFIG_DIR, output_base=config["output_base"])

    try:
        os.makedirs(config["output_base"], exist_ok=True)
    except Exception as e:
        print(f"{RED}❌ Failed to create output directory: {e}{RESET}")
        sys.exit(1)

    # ── Batch mode (--batch flag) ────────────────────────────────────────
    if is_batch:
        entries = _collect_batch_entries()
        _process_batch(entries, config, duplicate_checker, lyrics_manager)
        return

    # ── Non-interactive single-shot mode ─────────────────────────────────
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:]).strip()
        if query:
            if query.startswith(("http://", "https://", "www.")):
                if query.startswith("www."):
                    query = "https://" + query
                download_song(
                    query,
                    config["output_base"],
                    duplicate_checker,
                    lyrics_manager,
                    user_query="",
                    audio_format=config["audio_format"]
                )
            else:
                print(f"{CYAN}🔍 Searching for top result: {query}{RESET}")
                results = search_youtube(query, max_results=1)

                if results:
                    top = results[0]
                    print(f"{GREEN}Found:{RESET} {top['title']}  {CYAN}by{RESET} {top['uploader']}")
                    download_song(
                        top['url'],
                        config["output_base"],
                        duplicate_checker,
                        lyrics_manager,
                        user_query=query,
                        audio_format=config["audio_format"]
                    )
                else:
                    print(f"{RED}No results found{RESET}")

        return

    # ── Interactive queue mode ────────────────────────────────────────────
    global _lines_below_banner
    print_banner()
    _lines_below_banner = 0

    stats = {"completed": 0, "current_status": None}
    q = queue.Queue()

    worker = threading.Thread(
        target=_queue_worker,
        args=(q, config, duplicate_checker, lyrics_manager, stats),
        daemon=True,
    )
    worker.start()

    try:
        while True:
            _maybe_redraw_banner(stats)

            user_input = _read_input(f"{CYAN}>>> {RESET}")
            _lines_below_banner += 1  # the prompt + typed text counts as a line

            if user_input is None:   # EOF
                break
            if not user_input:
                continue

            # ── Batch sub-mode ────────────────────────────────────────────
            if user_input.lower() == "batch":
                entries = _collect_batch_entries()
                _process_batch(entries, config, duplicate_checker, lyrics_manager)
                _tracked_print()
                continue

            # ── Search mode (synchronous — user picks) ────────────────────
            if user_input.lower().startswith("search "):
                query = user_input[7:].strip()
                if not query:
                    continue

                _tracked_print(f"{CYAN}🔍 Searching YouTube for: {query}{RESET}")
                results = search_youtube(query, max_results=5)

                if results:
                    display_search_results(results)
                    _lines_below_banner += len(results) * 3 + 4  # rough line count

                    while True:
                        try:
                            choice = _read_input(f"\n{WHITE}Enter number to download (or press Enter to cancel): {RESET}")
                            _lines_below_banner += 2

                            if not choice:
                                break

                            idx = int(choice)
                            if 1 <= idx <= len(results):
                                selected = results[idx - 1]
                                q.put({"entry": selected["url"], "user_query": query})
                                pending = q.qsize()
                                _tracked_print(f"⏳ Queued: {selected['title']} [{pending} pending]")
                                break
                            else:
                                _tracked_print(f"{RED}Invalid number{RESET}")
                        except ValueError:
                            _tracked_print(f"{RED}Please enter a valid number{RESET}")
                        except KeyboardInterrupt:
                            break
                else:
                    _tracked_print(f"{RED}No results found{RESET}")

                continue

            # ── .txt file expansion ───────────────────────────────────────
            candidate = user_input.strip("'\"")
            if candidate.endswith('.txt') and os.path.isfile(candidate):
                try:
                    with open(candidate, 'r') as f:
                        file_lines = [l.strip() for l in f if l.strip()]
                    if file_lines:
                        for fl in file_lines:
                            q.put({"entry": fl, "user_query": fl})
                        fname = os.path.basename(candidate)
                        pending = q.qsize()
                        _tracked_print(f"📦 Loaded {len(file_lines)} songs from {fname} [{pending} pending]")
                    else:
                        _tracked_print(f"{YELLOW}File is empty{RESET}")
                except Exception as e:
                    _tracked_print(f"{RED}❌ Could not read file: {e}{RESET}")
                continue

            # ── URL or song name → queue ──────────────────────────────────
            entry = user_input
            user_query = ""
            if not entry.startswith(("http://", "https://", "www.")):
                user_query = entry

            q.put({"entry": entry, "user_query": user_query})
            pending = q.qsize()
            _tracked_print(f"⏳ Queued: {entry} [{pending} pending]")

    except KeyboardInterrupt:
        if not q.empty():
            print(f"\n{YELLOW}Finishing current download...{RESET}")
            while not q.empty():
                try:
                    q.get_nowait()
                    q.task_done()
                except queue.Empty:
                    break
            q.join()

        print(f"\n{CYAN}Exiting MUSE-CLI. Goodbye!{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
