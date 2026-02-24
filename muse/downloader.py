import os
import subprocess
import re
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4

from .colors import CYAN, GREEN, YELLOW, RED, DIM, RESET

BAR_LENGTH = 40

_NOISE_PATTERNS = [
    r'\(Official\s*(Music\s*)?Video\)',
    r'\(Official\s*(Audio|Lyric)\)',
    r'\(Lyrics?\|Letra\)',
    r'\(Letra\)',
    r'\(Lyrics?\)',
    r'\(HD\)',
    r'\(.*?cover.*?\)',
    r'\(.*?(?:Official|Video|Audio|Lyric|HD|MV|mv|Session|sessions|acoustic|live).*?\)',
    r'\[.*?(?:Official|Video|Audio|Lyric|HD|MV|mv|Session|sessions|acoustic|live).*?\]',
    r'(?:ft|feat)\.?\s+[^\-\(]+',
    r'\([^)]*$',                           # unclosed "("
    r'\[[^\]]*$',                          # unclosed "["
    r'\s{2,}',
]

_SEPARATORS = [' - ', ' – ', ' — ', ': ']


def _strip_noise(text: str) -> str:
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


def extract_video_info(url: str) -> tuple[str, str, str, bool]:
    """Returns (artist, title, video_id, is_cover)."""
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

    # Check for cover on raw title BEFORE stripping noise
    is_cover = bool(re.search(r'\bcover\b', raw_title, flags=re.IGNORECASE))

    if raw_artist and raw_artist.lower() not in ("na", "none", "unknown", ""):
        return _clean_channel_name(raw_artist), _strip_noise(raw_title), video_id, is_cover

    split = _split_title(raw_title)
    if split:
        return split[0], split[1], video_id, is_cover

    channel_candidate = raw_channel or raw_uploader or ""
    artist = _clean_channel_name(channel_candidate) if channel_candidate else "Unknown Artist"
    return artist, _strip_noise(raw_title) or raw_title, video_id, is_cover


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


def find_latest_audio(artist_dir: str, audio_format: str) -> str:
    ext = f".{audio_format}"
    audio_files = []
    try:
        for name in os.listdir(artist_dir):
            if name.endswith(ext):
                fp = os.path.join(artist_dir, name)
                audio_files.append((fp, os.path.getctime(fp)))
    except OSError:
        pass
    if not audio_files:
        raise Exception(f"[E04] No {ext} file found — is ffmpeg installed?")
    return max(audio_files, key=lambda x: x[1])[0]


def _write_tags(filepath: str, title: str, artist: str, album: str,
                year: str, audio_format: str):
    try:
        if audio_format == "mp3":
            audio = EasyID3(filepath)
            audio["title"]  = [title]
            audio["artist"] = [artist]
            audio["genre"]  = ["Music"]
            if album:
                audio["album"] = [album]
            if year:
                audio["date"] = [year]
            audio.save()
        else:
            audio = MP4(filepath)
            audio["\xa9nam"] = [title]
            audio["\xa9ART"] = [artist]
            audio["\xa9gen"] = ["Music"]
            if album:
                audio["\xa9alb"] = [album]
            if year:
                audio["\xa9day"] = [year]
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

        # ── Fetch video info ─────────────────────────────────────────────────
        print(f"{DIM}   Fetching info...{RESET}", end="\r")
        artist, title, video_id, is_cover = extract_video_info(url)
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

        # ── MusicBrainz metadata lookup ──────────────────────────────────────
        print(f"{DIM}   Looking up metadata...{RESET}", end="\r")
        from .metadata import lookup_metadata
        mb = lookup_metadata(artist, title, is_cover=is_cover)

        # Use MusicBrainz data if found, fall back to YouTube data
        final_artist = mb.get('artist') or artist
        final_title  = mb.get('title')  or title
        album        = mb.get('album')  or ""
        year         = mb.get('year')   or ""

        if mb:
            print(f"{DIM}   Metadata: {final_artist} — {final_title}"
                  f"{(' / ' + album) if album else ''}"
                  f"{(' (' + year + ')') if year else ''}{RESET}          ")
        else:
            print(f"   {DIM}Metadata not found on MusicBrainz{RESET}          ")

        # ── Download ─────────────────────────────────────────────────────────
        safe_artist = _sanitize_path_component(final_artist)
        safe_title  = _sanitize_path_component(final_title)
        safe_album  = _sanitize_path_component(album) if album else "Unknown Album"

        artist_dir = os.path.join(output_base, safe_artist, safe_album)
        os.makedirs(artist_dir, exist_ok=True)
        output_template = os.path.join(artist_dir, f"{safe_title}.%(ext)s")

        print(f"{DIM}   Downloading...{RESET}")
        downloaded_file = download_with_progress(url, output_template, audio_format)

        desired_path = os.path.join(artist_dir, f"{safe_title}.{audio_format}")
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

        # ── Lyrics ───────────────────────────────────────────────────────────
        print(f"{DIM}   Fetching lyrics...{RESET}", end="\r")
        result = lyrics_manager.fetch_and_embed(
            downloaded_file, final_title, final_artist,
            user_query=user_query, audio_format=audio_format,
            is_cover=is_cover
        )

        # ── Write tags ───────────────────────────────────────────────────────
        _write_tags(downloaded_file, final_title, final_artist,
                    album, year, audio_format)

        # ── Register + Apple Music ────────────────────────────────────────────
        file_hash = duplicate_checker.compute_file_hash(downloaded_file)
        duplicate_checker.register(video_id, file_hash, downloaded_file)
        _add_to_apple_music(downloaded_file)

        # ── Summary ──────────────────────────────────────────────────────────
        print(f"{GREEN}✅ {final_artist} — {final_title}{RESET}")
        if album:
            print(f"{DIM}   Album: {album}{(' (' + year + ')') if year else ''}{RESET}")
        print(result.status)

    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(f"{RED}❌ {e}{RESET}")
        print(f"{DIM}   See github.com/Ulasti/muse-cli for error codes{RESET}")