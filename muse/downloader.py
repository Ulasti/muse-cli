import os
import subprocess
import re
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4

# ANSI colors
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
DIM    = "\033[2m"
RESET  = "\033[0m"

BAR_LENGTH = 40

_NOISE_PATTERNS = [
    r'\(Official\s*(Music\s*)?Video\)',
    r'\(Official\s*(Audio|Lyric)\)',
    r'\(Lyrics?\|Letra\)',
    r'\(Letra\)',                          # Spanish "lyrics"
    r'\(Lyrics?\)',
    r'\(HD\)',
    r'\(.*?cover.*?\)',
    r'\(.*?(?:Official|Video|Audio|Lyric|HD|MV|mv|Session|sessions|acoustic|live).*?\)',
    r'\[.*?(?:Official|Video|Audio|Lyric|HD|MV|mv|Session|sessions|acoustic|live).*?\]',
    r'(?:ft|feat)\.?\s+[^\-\(]+',
    r'\([^)]*$',                           # unclosed parenthesis like "(Cabin Sessions 1"
    r'\[[^\]]*$',                          # unclosed bracket
    r'\s{2,}',
]

_SEPARATORS = [' - ', ' – ', ' — ', ': ']


def _strip_noise(text: str) -> str:
    """Strip album bleed, session/live tags, and all YouTube noise from a title."""
    text = text.split('|')[0]
    text = re.split(r'\s*/\s*', text)[0]
    for pattern in _NOISE_PATTERNS[:-1]:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    text = re.sub(_NOISE_PATTERNS[-1], ' ', text)
    return text.strip(' -–—|')


def _split_title(raw_title: str) -> tuple[str, str] | None:
    cleaned = _strip_noise(raw_title)
    for sep in _SEPARATORS:
        if sep in cleaned:
            parts = cleaned.split(sep, 1)
            artist_part = parts[0].strip()
            title_part  = parts[1].strip()
            if artist_part and title_part and len(artist_part) < 80:
                return artist_part, title_part
    return None


def _clean_channel_name(name: str) -> str:
    suffixes = [r'\s*-\s*Topic$', r'\s*VEVO$', r'\s*Official\s*$', r'\s*Music\s*$']
    for s in suffixes:
        name = re.sub(s, '', name, flags=re.IGNORECASE)
    return name.strip()


def extract_video_info(url: str) -> tuple[str, str, str]:
    info_cmd = [
        "yt-dlp", "--no-playlist", "--quiet",
        "--print", "%(artist)s\n%(title)s\n%(uploader)s\n%(channel)s\n%(id)s",
        "--add-header", "Accept-Language:en-US,en;q=0.9",
        "--extractor-args", "youtube:lang=en",
        url
    ]
    try:
        result = subprocess.run(
            info_cmd, capture_output=True, text=True, check=True, timeout=30
        )
    except subprocess.TimeoutExpired:
        raise Exception("[E01] Timeout fetching video info — check your connection")
    except subprocess.CalledProcessError as e:
        raise Exception(f"[E02] yt-dlp failed: {e.stderr.strip()}")

    lines = [l.strip() for l in result.stdout.strip().split("\n")]
    while len(lines) < 5:
        lines.append("")

    raw_artist, raw_title, raw_uploader, raw_channel, video_id = lines[:5]

    if raw_artist and raw_artist.lower() not in ("na", "none", "unknown", ""):
        return _clean_channel_name(raw_artist), _strip_noise(raw_title), video_id

    split = _split_title(raw_title)
    if split:
        return split[0], split[1], video_id

    channel_candidate = raw_channel or raw_uploader or ""
    artist = _clean_channel_name(channel_candidate) if channel_candidate else "Unknown Artist"
    return artist, _strip_noise(raw_title) or raw_title, video_id


def download_with_progress(url: str, output_template: str, audio_format: str) -> str:
    download_cmd = [
        "yt-dlp", "--no-playlist",
        "--extract-audio",
        "--audio-format", audio_format,
        "--audio-quality", "0",
        "--embed-thumbnail",
        "--add-metadata",
        "--newline", "--progress",
        "--progress-template", "download:%(progress.percentage)s",
        "--add-header", "Accept-Language:en-US,en;q=0.9",
        "--extractor-args", "youtube:lang=en",
        "-o", output_template,
        url
    ]
    try:
        proc = subprocess.Popen(
            download_cmd, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        last_percent = -1
        for line in proc.stdout:
            line = line.strip()
            try:
                if line and not line.startswith('['):
                    m = re.search(r'(\d+\.?\d*)%', line)
                    if m:
                        percent = float(m.group(1))
                        if abs(percent - last_percent) >= 1:
                            filled = int((percent / 100) * BAR_LENGTH)
                            bar = (
                                f"{CYAN}[{'█' * filled}{'▒' * (BAR_LENGTH - filled)}]{RESET}"
                                f" {CYAN}{int(percent)}%{RESET}"
                            )
                            print(f"\r   {bar}", end="", flush=True)
                            last_percent = percent
            except Exception:
                continue
        print()
        proc.wait()
        if proc.returncode != 0:
            raise Exception(f"[E03] yt-dlp exited with code {proc.returncode}")
        return find_latest_audio(os.path.dirname(output_template), audio_format)
    except Exception as e:
        raise Exception(f"[E03] Download failed: {e}")


def find_latest_audio(base_path: str, audio_format: str) -> str:
    ext = f".{audio_format}"
    audio_files = []
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.endswith(ext):
                fp = os.path.join(root, f)
                audio_files.append((fp, os.path.getctime(fp)))
    if not audio_files:
        raise Exception(f"[E04] No {ext} file found — is ffmpeg installed?")
    return max(audio_files, key=lambda x: x[1])[0]


def _write_tags(filepath: str, title: str, artist: str, album: str,
                release_date: str, audio_format: str):
    """Write metadata tags — ID3 for MP3, MP4 atoms for M4A."""
    try:
        if audio_format == "mp3":
            audio = EasyID3(filepath)
            audio["title"]  = [title]
            audio["artist"] = [artist]
            audio["genre"]  = ["Music"]
            if album:
                audio["album"] = [album]
            if release_date:
                audio["date"] = [release_date]
            audio.save()
        else:
            audio = MP4(filepath)
            audio["\xa9nam"] = [title]
            audio["\xa9ART"] = [artist]
            audio["\xa9gen"] = ["Music"]
            if album:
                audio["\xa9alb"] = [album]
            if release_date:
                audio["\xa9day"] = [release_date]
            audio.save()
    except Exception as e:
        print(f"{YELLOW}⚠  Could not write tags: {e}{RESET}")


def _add_to_apple_music(filepath: str):
    import platform
    if platform.system() != "Darwin":
        return
    try:
        subprocess.run([
            "osascript", "-e",
            f'tell application "Music" to add POSIX file "{filepath}"'
        ], check=True, capture_output=True)
    except Exception:
        pass


def _sanitize_path_component(name: str) -> str:
    return re.sub(r'[\/\\\:\*\?\"\<\>\|]', '', name).strip() or "Unknown"


def download_song(url: str, output_base: str, duplicate_checker, lyrics_manager,
                  user_query: str = "", audio_format: str = "m4a"):
    try:
        if not url.startswith(("http://", "https://")):
            print(f"{RED}❌ Invalid URL{RESET}")
            return

        # ── Fetch info ───────────────────────────────────────────────────────
        print(f"{DIM}   Fetching info...{RESET}", end="\r")
        artist, title, video_id = extract_video_info(url)
        print(f"   {GREEN}▶ {artist} — {title}{RESET}          ")

        # ── Duplicate check ──────────────────────────────────────────────────
        is_dup, existing_file = duplicate_checker.is_duplicate_by_id(video_id)
        if is_dup:
            print(f"{YELLOW}⚠  Already in library: {existing_file}{RESET}")
            try:
                choice = input(f"{YELLOW}   Overwrite? (y/N): {RESET}").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print()
                return
            if choice != 'y':
                print(f"{DIM}   Skipped.{RESET}")
                return
            try:
                os.remove(existing_file)
            except Exception:
                pass
            duplicate_checker.remove_entries(video_id, existing_file)

        # ── Download ─────────────────────────────────────────────────────────
        safe_artist = _sanitize_path_component(artist)
        safe_title  = _sanitize_path_component(title)

        # Temp dir while we don't know the album yet
        temp_dir = os.path.join(output_base, safe_artist, "Unknown Album")
        os.makedirs(temp_dir, exist_ok=True)
        output_template = os.path.join(temp_dir, f"{safe_title}.%(ext)s")

        print(f"{DIM}   Downloading...{RESET}")
        downloaded_file = download_with_progress(url, output_template, audio_format)

        desired_path = os.path.join(temp_dir, f"{safe_title}.{audio_format}")
        if downloaded_file != desired_path and os.path.exists(downloaded_file):
            os.replace(downloaded_file, desired_path)
            downloaded_file = desired_path

        # ── Content duplicate check ──────────────────────────────────────────
        is_dup, existing_file = duplicate_checker.is_duplicate(downloaded_file)
        if is_dup:
            print(f"{YELLOW}⚠  Duplicate content, removing...{RESET}")
            try:
                os.remove(downloaded_file)
            except Exception:
                pass
            return

        # ── Lyrics + metadata from Genius ────────────────────────────────────
        print(f"{DIM}   Fetching lyrics...{RESET}", end="\r")
        result = lyrics_manager.fetch_and_embed(
            downloaded_file, title, artist,
            user_query=user_query, audio_format=audio_format
        )

        # ── Move to final folder if we got an album name ──────────────────────
        album = result.album or "Unknown Album"
        safe_album = _sanitize_path_component(album)
        final_dir  = os.path.join(output_base, safe_artist, safe_album)

        if final_dir != temp_dir:
            os.makedirs(final_dir, exist_ok=True)
            final_path = os.path.join(final_dir, f"{safe_title}.{audio_format}")
            os.replace(downloaded_file, final_path)
            downloaded_file = final_path
            # Clean up empty temp dir
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass

        # ── Write tags with album info ────────────────────────────────────────
        _write_tags(downloaded_file, title, artist, album,
                    result.release_date, audio_format)

        # ── Register + Apple Music ────────────────────────────────────────────
        file_hash = duplicate_checker.compute_file_hash(downloaded_file)
        duplicate_checker.register(video_id, file_hash, downloaded_file)
        _add_to_apple_music(downloaded_file)

        # ── Summary ───────────────────────────────────────────────────────────
        print(f"{GREEN}✅ {artist} — {title}{RESET}")
        if album != "Unknown Album":
            print(f"{DIM}   Album: {album}{RESET}")
        print(result.status)

    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(f"{RED}❌ {e}{RESET}")
        print(f"{DIM}   See github.com/Ulasti/muse-cli for error codes{RESET}")