import re
import time

from .colors import DIM, RESET

_SECONDARY_REJECT = {"Live", "Compilation", "Remix", "DJ-mix", "Mixtape/Street",
                      "Demo", "Soundtrack", "Spokenword", "Interview", "Audiobook"}


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


def _release_score(rel: dict) -> tuple:
    """
    Score a release for picking the best album.
    Returns a tuple for sorting (higher = better):
      (type_rank, -title_penalty, has_date, earliest_year)
    """
    rg = rel.get('release-group', {})
    primary = rg.get('type', '')
    secondary = set(rg.get('secondary-type-list', []))

    # Reject anything with unwanted secondary types
    if secondary & _SECONDARY_REJECT:
        return (-1, 0, 0, 0)

    # Reject unwanted primary types
    if primary in ("Broadcast", "Other"):
        return (-1, 0, 0, 0)

    # Rank: Album > Single > EP > everything else
    type_rank = {"Album": 3, "Single": 2, "EP": 1}.get(primary, 0)

    # Penalize titles that suggest non-studio releases
    title = rel.get('title', '').lower()
    title_penalty = 1 if any(w in title for w in [
        'reissue', 'remaster', 'compilation', 'mix', 'commentary',
        'live', 'concert', 'festival', 'bootleg', 'tour', 'unplugged',
        'deluxe', 'anniversary', 'promo', 'unmastered', 'advance',
        'sampler', 'demo', 'bonus',
    ]) else 0

    # Prefer releases with dates, and prefer earlier dates (original release)
    date = rel.get('date', '')
    year = int(date[:4]) if len(date) >= 4 and date[:4].isdigit() else 9999

    return (type_rank, -title_penalty, 1 if date else 0, -year)


def _pick_best_release(releases: list) -> dict:
    if not releases:
        return {}
    scored = sorted(releases, key=_release_score, reverse=True)
    best = scored[0]
    if _release_score(best)[0] < 0:
        return {}
    return best


def _artist_matches(rec_artist: str, query_artist: str) -> bool:
    """Check if the recording artist is compatible with the query artist."""
    a = _normalize(rec_artist)
    b = _normalize(query_artist)
    if not a or not b:
        return True  # no data to compare, don't reject
    # One contains the other, or significant word overlap
    if a in b or b in a:
        return True
    words_a = set(a.split())
    words_b = set(b.split())
    overlap = len(words_a & words_b)
    return overlap >= 1 and overlap / max(len(words_a), len(words_b)) >= 0.5


def _pick_best_recording(recordings: list, title: str, artist: str,
                          is_cover: bool) -> dict:
    """
    Scan all recordings and pick the one most likely to be the canonical
    studio version, then return the best release from it.

    Strategy: recordings with more releases are more likely to be the
    canonical studio version (many country editions), so we pick the
    recording whose best release scores highest, breaking ties by
    number of releases (proxy for "canonical-ness").
    """
    threshold = 0.85 if is_cover else 0.6
    best_result = None
    best_key = (-1,)

    for recording in recordings:
        rec_title  = recording.get('title', '')
        rec_artist = recording.get('artist-credit-phrase', '')

        if _title_score(rec_title, title) < threshold:
            continue

        # Skip recordings by different artists (unless searching covers)
        if not is_cover and not _artist_matches(rec_artist, artist):
            continue

        releases = recording.get('release-list', [])
        rel = _pick_best_release(releases)
        if not rel:
            continue

        score = _release_score(rel)
        # Tie-break: prefer recordings with more releases (studio versions
        # typically appear on many regional editions)
        key = (*score, len(releases))
        if key > best_key:
            best_key = key
            date = rel.get('date', '')
            best_result = {
                'artist': rec_artist or rec_title,
                'title':  rec_title  or title,
                'album':  rel.get('title', ''),
                'year':   date[:4] if len(date) >= 4 else '',
            }

    return best_result or {}


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
        time.sleep(1)

        for attempt in range(2):
            try:
                if is_cover:
                    result = musicbrainzngs.search_recordings(
                        recording=title, limit=10
                    )
                else:
                    result = musicbrainzngs.search_recordings(
                        artist=artist, recording=title, limit=50
                    )
                break
            except Exception:
                if attempt == 0:
                    time.sleep(2)
                    continue
                return {}

        recordings = result.get('recording-list', [])
        match = _pick_best_recording(recordings, title, artist, is_cover)
        if match:
            return match

    except ImportError:
        pass
    except Exception:
        pass

    return {}