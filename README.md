# yt-transcribe

CLI tool that transcribes YouTube videos and local audio/video files. For YouTube, it fetches existing captions when available; otherwise downloads audio and transcribes locally with [Whisper](https://github.com/SYSTRAN/faster-whisper).

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- [just](https://just.systems/)
- [ffmpeg](https://ffmpeg.org/) — required when downloading YouTube audio (not needed for local files)

### macOS

```bash
brew install uv just ffmpeg
```

### Linux (Debian/Ubuntu)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin
sudo apt install ffmpeg
```

### Windows

```powershell
winget install astral-sh.uv
winget install Casey.Just
winget install ffmpeg
```

> **Note:** `faster-whisper` requires the [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) (x64). Install it if you see a DLL error on first Whisper run.

## Setup

```bash
cd transcribe
just install
```

## Quick start

```bash
# Transcribe a YouTube video (captions if available, Whisper otherwise)
just run "https://youtube.com/watch?v=VIDEO_ID"

# Transcribe a local file
just run recording.mp3

# Print to stdout (safe to pipe)
just run "https://youtube.com/watch?v=VIDEO_ID" --print
```

Transcripts are saved to `~/Downloads` by default using the video title as the filename.

## Documentation

- [User Manual](docs/USER_MANUAL.md) — all options, config, examples, clipboard usage
- [Technical Details](docs/TECHNICAL.md) — architecture, dependencies, performance benchmarks
