import re
from turtle import title

# ANSI colors
DIM   = "\033[2m"
RESET = "\033[0m"

_PREFERRED_TYPES = ["Album", "Single", "EP"]
_REJECTED_TYPES  = ["Spokenword", "Broadcast", "DJ Mix", "Compilation", "Interview", "Live", "Remix",]


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()


def _title_score(result_title: str, query_title: str) -> float:
    a = set(_normalize(result_title).split())
    b = set(_normalize(query_title).split())
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return len(a & b) / max(len(a), len(b))


def _pick_best_release(releases: list) -> dict:
    if not releases:
        return {}

    def release_score(rel):
        rtype = rel.get('release-group', {}).get('type', '')
        if rtype in _REJECTED_TYPES:
            return -1
        type_score = len(_PREFERRED_TYPES) - _PREFERRED_TYPES.index(rtype) \
                     if rtype in _PREFERRED_TYPES else 0
        title   = rel.get('title', '').lower()
        penalty = 1 if any(w in title for w in [
            'reissue', 'remaster', 'compilation', 'mix', 'commentary',
            'live', 'concert', 'festival', 'bootleg', 'tour', 'unplugged'
        ]) else 0
        return type_score - penalty

    scored = sorted(releases, key=release_score, reverse=True)
    return scored[0] if release_score(scored[0]) >= 0 else {}


def lookup_metadata(artist: str, title: str, is_cover: bool = False) -> dict:
    """
    Query MusicBrainz for metadata.
    If is_cover=True, search by title only and take the most popular result
    so covers correctly return the original artist's album info.
    Returns { 'artist', 'title', 'album', 'year' } or empty dict.
    """
    try:
        import musicbrainzngs
        musicbrainzngs.set_useragent(
            'muse-cli', '1.0', 'https://github.com/Ulasti/muse-cli'
        )

        if is_cover:
            # Title only — top result by MusicBrainz score = most popular version
            result = musicbrainzngs.search_recordings(
                recording=title, limit=1
            )
        else:
            result = musicbrainzngs.search_recordings(
                artist=artist, recording=title, limit=5
            )

        recordings = result.get('recording-list', [])

        for recording in recordings:
            rec_title  = recording.get('title', '')
            rec_artist = recording.get('artist-credit-phrase', '')
            title_score = _title_score(rec_title, title)

            threshold = 0.85 if is_cover else 0.6
            if title_score < threshold:
                continue

            releases = recording.get('release-list', [])
            best_rel = _pick_best_release(releases)

            if not best_rel:
                continue

            album = best_rel.get('title', '')
            year  = ''
            date  = best_rel.get('date', '')
            if date:
                year = date[:4]

            return {
                'artist': rec_artist or artist,
                'title':  rec_title  or title,
                'album':  album,
                'year':   year,
            }

    except ImportError:
        pass
    except Exception:
        pass

    return {}