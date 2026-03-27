# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Commands

```bash
just install        # create venv and install dependencies via uv
just run <source>   # transcribe a YouTube URL, video ID, or local file
just config --show  # print current config
just config --edit  # open config in $EDITOR
just models         # list available Whisper model sizes
just test           # unit tests (no network)
just smoke          # integration tests (requires network)
```

## Source files

- **`src/transcribe/cli.py`** — all CLI logic via Typer. Two commands: `run` and `config`. `run` routes to `_transcribe_youtube` or `_run_whisper` directly for local files.
- **`src/transcribe/config.py`** — loads `~/.config/yt-transcribe/config.toml` via `platformdirs`. Merges user TOML over hardcoded `_DEFAULTS`.

## Documentation

- [docs/USER_MANUAL.md](docs/USER_MANUAL.md) — usage, options, config reference
- [docs/TECHNICAL.md](docs/TECHNICAL.md) — architecture, flow, performance, dependencies

## Key behaviours

- `faster-whisper` and `yt-dlp` are lazy imports — only loaded when captions are unavailable.
- Audio is downloaded to `tempfile.TemporaryDirectory()` and deleted automatically.
- `unique_path()` appends `(1)`, `(2)`, … to avoid overwriting existing files.
- `--print` suppresses all Rich output and writes only the transcript to stdout.
- Output path resolution: `--output` flag → `output_dir` in config → `~/Downloads`.
- `YOUTUBE_COOKIES_FILE` env var enables authenticated caption/download requests.

## No linter or formatter configured.
