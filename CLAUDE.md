# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
just install        # create venv and install dependencies via uv
just run <url>      # transcribe a YouTube URL or bare video ID
just config --show  # print current config
just config --edit  # open config in $EDITOR
just models         # list available Whisper model sizes
```

There are no tests and no linter configured.

## Architecture

Two source files under `src/transcribe/`:

- **`cli.py`** — all CLI logic via Typer. Two commands: `run` (transcribe) and `config` (show/edit config file). The `run` command tries YouTube captions first (`fetch_youtube_captions`), falls back to Whisper (`transcribe_with_whisper`). Output path resolution order: `--output` flag → `output_dir` in config → `~/Downloads`.

- **`config.py`** — loads `~/.config/yt-transcribe/config.toml` (path determined by `platformdirs.user_config_dir`). Merges user TOML over hardcoded `_DEFAULTS`. Creates the file with documented defaults on `config --edit` if it doesn't exist yet.

## Key behaviours

- `faster-whisper` and `yt-dlp` are lazy imports — only loaded when captions are unavailable, so caption-only runs have no heavy dependency startup cost.
- Audio is downloaded to `tempfile.TemporaryDirectory()` and deleted automatically after transcription.
- `unique_path()` appends `(1)`, `(2)`, … to avoid silently overwriting existing files.
- `--print` suppresses all Rich console output and writes only the transcript to stdout — safe for piping.
- Config path is platform-specific via `platformdirs`: `~/Library/Application Support/yt-transcribe/` on macOS, `~/.config/yt-transcribe/` on Linux, `%LOCALAPPDATA%\yt-transcribe\` on Windows.
