# yt-transcribe

CLI tool that extracts transcripts from YouTube videos. Fetches existing captions when available; otherwise downloads audio and transcribes locally with [Whisper](https://github.com/SYSTRAN/faster-whisper).

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [just](https://just.systems/) — `brew install just`

## Setup

```bash
cd transcribe
just install
```

## Usage

```bash
# Fetch captions if available, otherwise run Whisper — saves to current dir by default
just run "https://youtube.com/watch?v=VIDEO_ID"

# Save to a specific file
just run "https://youtube.com/watch?v=VIDEO_ID" --output transcript.txt

# Print to stdout (all status output suppressed — safe to pipe)
just run "https://youtube.com/watch?v=VIDEO_ID" --print
just run "https://youtube.com/watch?v=VIDEO_ID" --print | pbcopy

# Force Whisper even if captions exist
just run "https://youtube.com/watch?v=VIDEO_ID" --force-whisper

# Use a specific Whisper model
just run "https://youtube.com/watch?v=VIDEO_ID" --model large-v3

# Force language (auto-detected by default)
just run "https://youtube.com/watch?v=VIDEO_ID" --language de

# See all model options
just models
```

## Config

Defaults are stored in `~/.config/yt-transcribe/config.toml`. On first run with `just config --edit` the file is created with all options documented inline.

```bash
just config           # show config file path
just config --show    # print current config
just config --edit    # open in $EDITOR
```

Default config:

```toml
[defaults]
model = "turbo"         # tiny | base | small | medium | turbo | large-v3
language = ""           # empty = auto-detect per video
output_dir = ""         # if set, transcripts are auto-saved here (uses video title as filename)
output_extension = "txt"

[whisper]
device = "cpu"          # cpu | cuda (use cuda if you have a GPU)
compute_type = "int8"   # int8 (fast CPU) | float16 (GPU) | float32 (precise)
beam_size = 5           # higher = more accurate, slower (1–10)
vad_filter = true       # skip silent segments (recommended)
```

**`output_dir`** — when set, every transcription is auto-saved to `<output_dir>/<video title>.<output_extension>` without needing `--output`. Useful for batch use.

## Options

| Flag | Short | Default | Description |
|---|---|---|---|
| `--print` | `-p` | off | Print to stdout instead of saving; suppresses all status output (safe to pipe) |
| `--output` | `-o` | — | Save to this exact path (overrides `output_dir` in config) |
| `--model` | `-m` | from config | Whisper model size |
| `--language` | `-l` | auto-detect | Override language, e.g. `en`, `fr`, `de`. Omit to auto-detect — useful only when detection gets it wrong or the video has mixed-language content. |
| `--force-whisper` | `-w` | off | Skip caption lookup, always use Whisper |

By default the transcript is **saved to a file** — to `output_dir` from config if set, otherwise to the current directory, using the video title as the filename. Use `--print` to get stdout behaviour instead.

CLI flags always override config values.

## Whisper models

Model weights are downloaded from HuggingFace on first use and cached at `~/.cache/huggingface/hub/`. Subsequent runs use the cached copy — no re-download. Override the location with the `HF_HUB_CACHE` environment variable.

| Model | Size | Speed | Accuracy |
|---|---|---|---|
| `tiny` | ~75 MB | fastest | lowest |
| `base` | ~140 MB | fast | decent |
| `small` | ~460 MB | moderate | good |
| `medium` | ~1.5 GB | slow | better |
| `turbo` | ~800 MB | fast | best for size — **default** |
| `large-v3` | ~3 GB | slowest | highest |

## How it works

```
                   ┌─────────────────────┐
                   │   YouTube URL / ID  │
                   └──────────┬──────────┘
                              │ extract video ID
                              ▼
                 ┌────────────────────────┐
                 │  Fetch YouTube captions │  ◄── youtube-transcript-api
                 │  (any available lang)   │      prefers manual over auto-generated
                 └────────────┬───────────┘
                              │
              ┌───────────────┴──────────────┐
              │ Captions found?              │
              ▼                              ▼
           Yes: done                  No: fallback
                                           │
                                    ┌──────▼──────┐
                                    │  Download   │  ◄── yt-dlp
                                    │  audio      │      best quality stream
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │   Whisper   │  ◄── faster-whisper
                                    │  transcribe │      CTranslate2, CPU/GPU
                                    └──────┬──────┘
                                           │ audio deleted from temp dir
                                           ▼
                         ┌─────────────────────────────┐
                         │  --output / output_dir / stdout │
                         └─────────────────────────────┘
```

### Caption lookup

Uses [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) to fetch captions from YouTube's internal API — no audio download needed, instant. Prefers manually uploaded captions over auto-generated ones. Falls back to Whisper when:

- The video owner disabled captions
- The video is too new for auto-generation to finish
- YouTube rate-limits the request

### Whisper transcription

1. **Download** — `yt-dlp` fetches the best available audio stream to a temp directory.
2. **Transcribe** — `faster-whisper` runs the Whisper model with `vad_filter=True` to skip silent segments. Language is auto-detected unless overridden.
3. **Cleanup** — temp audio file deleted automatically.

`faster-whisper` uses [CTranslate2](https://github.com/OpenNMT/CTranslate2) under the hood — 4–8× faster than OpenAI's original Whisper on CPU using `int8` quantization.

## Dependencies

| Package | Purpose |
|---|---|
| [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) | Fetch YouTube captions |
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | Download audio |
| [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) | Local speech-to-text |
| [`typer`](https://typer.tiangolo.com/) | CLI framework |
| [`rich`](https://rich.readthedocs.io/) | Terminal output |
