# 🎵 muse-cli

Music downloading made easy with built in lyrics embedding packaged into a cli-tool.

---

## Requirements

- Python 3.10+
- pipx
- ffmpeg

### Install muse

```bash

MacOS/Linux
curl -fsSL https://raw.githubusercontent.com/Ulasti/muse-cli/main/install.sh | bash
```

---

## Update

```bash
muse-cli --update
```

---

## Usage

Launch the app:

```bash
muse-cli
```

Then type at the prompt:

| Input | What it does |
|---|---|
| `Song title (optional artist name)` | Searches the internet, downloads the most compatible result instantly|
| `search song title (optional artist name)` | Shows top 5 results to choose from |
| `https://y...` | Downloads directly from URL |

---

## Commands

```bash
muse-cli --config     # Edit settings (output folder, Genius token)
muse-cli --update     # Pull and install latest version from GitHub
muse-cli --uninstall  # Remove muse-cli and optionally clean up dependencies
```

---

## Lyrics (Optional)

muse-cli can automatically fetch and embed lyrics into downloaded files via the Genius API.

1. Go to https://genius.com/api-clients
2. Create an account and generate a token
3. Copy the **Client Access Token**
4. Paste it when prompted on first launch, or run `muse-cli --config` to set it later

---

## Output Structure

```
~/Documents/Music/
├── ARTIST NAME/
│   └── TRACK NAME.mp3
└── ARTIST NAME 2/
    └── TRACK NAME.mp3
```

---

## Update

```bash
muse-cli --update
```

---

## Uninstall

```bash
muse-cli --uninstall
```

---

## Error code list

| Code | Cause | Fix |
|---|---|---|
| `E01` | Connection timeout | Check your internet |
| `E02` | yt-dlp failed | Run muse-cli --update |
| `E03` | Download failed | Try again or use URL directly |
| `E04` | No MP3 after download | Check ffmpeg is installed |
| `E05` | Genius init failed | Run muse-cli --config |
| `E06` | Genius token expired | Run muse-cli --config |
| `E07` | Genius rate limit | Wait a moment and retry |



---

## Development

```bash
git clone https://github.com/Ulasti/muse-cli.git
cd muse-cli
python3 -m venv venv
source venv/bin/activate
pip install -e .
muse-cli
```

To run without installing:

```bash
python -m muse
```

---

## Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Genius](https://genius.com)
- [lyricsgenius](https://github.com/johnwmillr/LyricsGenius)
- Created by ulasti

---

## License

MIT — see [LICENSE](LICENSE)