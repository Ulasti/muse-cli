# muse-cli

A command-line tool that downloads music from the Internet and automatically tags it with metadata from MusicBrainz and lyrics from Genius.

Type a song name, get a properly tagged audio file. That's it.

## Install

Requires **Python 3.10+** and **ffmpeg**. The install script handles everything else (ffmpeg, yt-dlp, pipx).

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/Ulasti/muse-cli/main/install.sh | bash
```

**Manual install** (if you prefer):

```bash
# install dependencies first
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Ubuntu/Debian

# then install muse-cli
pipx install git+https://github.com/Ulasti/muse-cli.git
```

After installing, restart your terminal and run `muse-cli`.

## Usage

```bash
muse-cli                              # launch interactive mode
muse-cli artist, song title.          # download top result and exit
muse-cli https://youtube.com/watch?v=... # download from URL and exit
```

### Interactive mode

Once inside the interactive prompt (`>>>`):

| Input | What happens |
|---|---|
| `artist, song title` | Downloads the best match from the internet |
| `search artist, song title` | Shows 5 results to pick from |
| `https://example.com/watch?v=...` | Downloads directly from URL |

### What muse-cli does for each download

1. Searches the Internet (or takes your URL)
2. Downloads audio via yt-dlp (M4A or MP3)
3. Looks up metadata on MusicBrainz (artist, album, year)
4. Fetches and embeds lyrics from Genius
5. Writes ID3/MP4 tags and organizes into artist/album folders
6. Detects duplicates by video ID and file hash

### Output structure

Files are saved to `~/Documents/Music` by default (configurable):

```
~/Documents/Music/
  Artist Name/
    Album Name/
      Song Title.m4a
  Another Artist/
    Unknown Album/
      Track.m4a
```

## Configuration

```bash
muse-cli --config
```

Settings menu lets you change:

- **Genius API token** - for lyrics (see below)
- **Output directory** - where music is saved
- **Audio format** - M4A (default, better quality) or MP3

Settings are stored in `~/.config/muse-cli/config.json`.

### Lyrics setup (optional)

To enable automatic lyrics embedding:

1. Create an account at [genius.com/api-clients](https://genius.com/api-clients)
2. Generate a **Client Access Token**
3. Enter it when prompted on first launch, or via `muse-cli --config`

Without a token, everything else works fine, you just won't get lyrics.

## Other commands

```bash
muse-cli --update      # update to latest version from GitHub
muse-cli --uninstall   # remove muse-cli and optionally clean up dependencies
```

## Error codes

| Code | Cause | Fix |
|---|---|---|
| E01 | Connection timeout | Check your internet |
| E02 | yt-dlp failed | Run `muse-cli --update` or update yt-dlp |
| E03 | Download failed | Try again or use a direct URL |
| E04 | No audio file after download | Make sure ffmpeg is installed |
| E05 | Genius init failed | Check your token with `muse-cli --config` |
| E06 | Genius token expired | Regenerate token, update with `muse-cli --config` |
| E07 | Genius rate limit | Wait a moment and retry |

## Development

```bash
git clone https://github.com/Ulasti/muse-cli.git
cd muse-cli
python3 -m venv venv && source venv/bin/activate
pip install -e .
muse-cli
```

## Credits

Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp), [MusicBrainz](https://musicbrainz.org), [lyricsgenius](https://github.com/johnwmillr/LyricsGenius), and [mutagen](https://github.com/quodlibet/mutagen).

Created by [ulasti](https://github.com/Ulasti).

## License

MIT - see [LICENSE](LICENSE)
