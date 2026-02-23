from mutagen.id3 import ID3, USLT
from mutagen.mp4 import MP4
import re

# ANSI colors
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
DIM    = "\033[2m"
RED    = "\033[31m"
RESET  = "\033[0m"


def _clean_for_search(text: str) -> str:
    """Strip all noise from a title for Genius search."""
    text = text.split('|')[0]                                                     # "SONG | ALBUM" → "SONG"
    text = re.split(r'\s*/\s*', text)[0]                                          # "SONG / Live" → "SONG"
    text = re.sub(r'\(.*?cover.*?\)', '', text, flags=re.IGNORECASE)              # "(Tame Impala cover)"
    text = re.sub(r'\([^)]*$', '', text)                                          # unclosed "(" like "(Cabin Sessions 1"
    text = re.sub(r'\(.*?\)', '', text)                                           # remaining (...)
    text = re.sub(r'\[.*?\]', '', text)                                           # [...]
    text = re.sub(r'\s*(?:ft|feat|con)\.?\s+.+', '', text, flags=re.IGNORECASE)  # feat. artist
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip(' -–—|')


def _embed_lyrics(file_path: str, lyrics_text: str, audio_format: str):
    """Write lyrics tag — USLT for MP3, \©lyr for M4A."""
    if audio_format == "mp3":
        from mutagen.id3 import USLT
        id3 = ID3(file_path)
        id3["USLT"] = USLT(encoding=3, lang='eng', desc='desc', text=lyrics_text)
        id3.save()
    else:
        audio = MP4(file_path)
        audio["\xa9lyr"] = [lyrics_text]
        audio.save()


def _titles_match(a: str, b: str) -> bool:
    def normalize(s):
        s = s.lower()
        s = re.sub(r'[^\w\s]', '', s)
        return set(s.split())
    words_a = normalize(a)
    words_b = normalize(b)
    if not words_a or not words_b:
        return False
    if words_a <= words_b or words_b <= words_a:
        return True
    return len(words_a & words_b) / max(len(words_a), len(words_b)) >= 0.7


class LyricsResult:
    """Carries lyrics status + any metadata Genius returned."""
    def __init__(self, status: str, album: str = "", release_date: str = ""):
        self.status       = status
        self.album        = album
        self.release_date = release_date


class LyricsManager:
    def __init__(self, genius_token):
        self.genius = None
        if genius_token:
            try:
                import lyricsgenius
                self.genius = lyricsgenius.Genius(
                    genius_token,
                    skip_non_songs=True,
                    excluded_terms=["(Remix)", "(Live)"],
                    remove_section_headers=False,
                )
                self.genius.verbose = False
            except Exception as e:
                print(f"{YELLOW}⚠  [E05] Genius init failed: {e}{RESET}")

    def fetch_and_embed(self, file_path: str, title: str, artist: str,
                        user_query: str = "", audio_format: str = "m4a") -> LyricsResult:
        if not self.genius:
            return LyricsResult(f"{YELLOW}⚠  Lyrics unavailable — no API token (run muse-cli --config){RESET}")

        clean_title  = _clean_for_search(title)
        clean_artist = _clean_for_search(artist)

        # Strategy 1: clean title only
        song = self._search(clean_title, None)

        # Strategy 2: clean title + artist
        if not song:
            song = self._search(clean_title, clean_artist)

        # Strategy 3: user query as last resort
        if not song and user_query and user_query.strip():
            song = self._search(user_query.strip(), None)

        # Strategy 4: walk artist's song list
        if not song and clean_artist and clean_artist.lower() not in ("unknown artist", "na", ""):
            try:
                genius_artist = self.genius.search_artist(
                    clean_artist, max_songs=10, sort="popularity"
                )
                if genius_artist:
                    for s in genius_artist.songs:
                        if _titles_match(s.title, clean_title) or _titles_match(s.title, user_query):
                            song = self._search(s.title, clean_artist)
                            if song:
                                break
            except Exception:
                pass

        if song:
            try:
                _embed_lyrics(file_path, song.lyrics, audio_format)
            except Exception as e:
                return LyricsResult(f"{YELLOW}⚠  Lyrics found but embed failed: {e}{RESET}")

            # Extract metadata from Genius song object
            album        = ""
            release_date = ""
            try:
                if hasattr(song, 'album') and song.album:
                    album = song.album
                if hasattr(song, 'release_date') and song.release_date:
                    release_date = str(song.release_date)[:4]  # just the year
            except Exception:
                pass

            status = f"{DIM}   Lyrics: \"{song.title}\" by {song.artist}{RESET}"
            return LyricsResult(status, album=album, release_date=release_date)

        return LyricsResult(f"{YELLOW}⚠  Lyrics not found for \"{clean_title}\"{RESET}")

    def _search(self, title: str, artist: str | None):
        try:
            song = self.genius.search_song(title, artist or "")
            if song and song.lyrics:
                return song
        except Exception as e:
            err = str(e)
            if "401" in err:
                print(f"{RED}❌ [E06] Genius token expired — run muse-cli --config{RESET}")
            elif "429" in err:
                print(f"{YELLOW}⚠  [E07] Genius rate limit — wait a moment and retry{RESET}")
        return None