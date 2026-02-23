import re

# ANSI colors
DIM   = "\033[2m"
RESET = "\033[0m"

# Release types to prefer, in order
_PREFERRED_TYPES = ["Album", "Single", "EP"]
_REJECTED_TYPES  = ["Spokenword", "Broadcast", "DJ Mix", "Compilation", "Interview"]




def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()


def _title_score(result_title: str, query_title: str) -> float:
    """Return 0-1 similarity between two titles."""
    a = set(_normalize(result_title).split())
    b = set(_normalize(query_title).split())
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return len(a & b) / max(len(a), len(b))


def _pick_best_release(releases: list) -> dict:
    """
    From a recording's release list pick the best one:
    prefer Album > Single > EP, reject bad types, prefer non-reissue.
    """
    if not releases:
        return {}

    def release_score(rel):
        rtype = rel.get('release-group', {}).get('type', '')
        if rtype in _REJECTED_TYPES:
            return -1
        type_score = len(_PREFERRED_TYPES) - _PREFERRED_TYPES.index(rtype) \
                     if rtype in _PREFERRED_TYPES else 0
        # Penalise reissues / remasters / compilations in the title
        title = rel.get('title', '').lower()
        penalty = 1 if any(w in title for w in ['reissue', 'remaster', 'compilation', 'mix', 'commentary']) else 0
        return type_score - penalty

    scored = sorted(releases, key=release_score, reverse=True)
    return scored[0] if release_score(scored[0]) >= 0 else {}


def lookup_metadata(artist: str, title: str) -> dict:
    """
    Query MusicBrainz for artist/title and return:
      { 'artist': str, 'title': str, 'album': str, 'year': str }
    Returns empty dict if nothing confident found.
    """
    try:
        import musicbrainzngs
        musicbrainzngs.set_useragent(
            'muse-cli', '1.0', 'https://github.com/Ulasti/muse-cli'
        )

        if is_cover:
            # Title only, take most popular result
            result = musicbrainzngs.search_recordings(
                recording=title, limit=1
            )
        else:
            result = musicbrainzngs.search_recordings(
                artist=artist, recording=title, limit=5
            )
            
        recordings = result.get('recording-list', [])

        for recording in recordings:
            rec_title   = recording.get('title', '')
            rec_artist  = recording.get('artist-credit-phrase', '')
            title_score = _title_score(rec_title, title)

            # Require a confident title match
            if title_score < 0.6:
                continue

            releases = recording.get('release-list', [])
            best_rel  = _pick_best_release(releases)

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
        pass  # musicbrainzngs not installed — silently skip
    except Exception:
        pass  # network error or API issue — silently skip

    return {}