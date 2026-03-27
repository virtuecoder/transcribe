# User Manual

## Commands

```bash
just install        # create venv and install dependencies
just run <source>   # transcribe a YouTube URL, video ID, or local file
just config         # show config file path
just config --show  # print current config values
just config --edit  # open config in $EDITOR
just models         # list available Whisper model sizes
just test           # run unit tests
just smoke          # run smoke tests (requires network)
```

## Transcribing

### YouTube videos

```bash
# Full URL
just run "https://youtube.com/watch?v=VIDEO_ID"

# Short URL
just run "https://youtu.be/VIDEO_ID"

# Bare video ID
just run VIDEO_ID
```

For YouTube, captions are fetched first (instant, no download). Whisper is used as fallback when captions are unavailable.

### Local files

```bash
just run recording.mp3
just run /path/to/interview.mp4
just run ~/Downloads/lecture.m4a
```

Any format FFmpeg handles is accepted. See [supported formats](TECHNICAL.md#supported-file-formats).

## Options

| Flag | Short | Default | Description |
|---|---|---|---|
| `--output` | `-o` | — | Save to this exact path (overrides `output_dir` in config) |
| `--model` | `-m` | from config | Whisper model size |
| `--language` | `-l` | auto-detect | Force language code, e.g. `en`, `fr`, `de` |
| `--force-whisper` | `-w` | off | Skip caption lookup, always use Whisper (ignored for local files) |
| `--print` | `-p` | off | Print to stdout instead of saving; suppresses all status output |

CLI flags always override config values.

## Output

By default transcripts are saved to `~/Downloads/<video title>.txt`. Three ways to control this:

1. **`--output path/to/file.txt`** — save to an exact path
2. **`output_dir` in config** — change the default save directory
3. **`--print`** — write to stdout instead of a file

If a file with the target name already exists, `(1)`, `(2)`, … is appended automatically.

### Clipboard

```bash
# macOS
just run "https://youtube.com/watch?v=VIDEO_ID" --print | pbcopy

# Linux
just run "https://youtube.com/watch?v=VIDEO_ID" --print | xclip -selection clipboard

# Windows
just run "https://youtube.com/watch?v=VIDEO_ID" --print | clip
```

## Config

Config is stored in a platform-specific TOML file:

| Platform | Path |
|---|---|
| macOS | `~/Library/Application Support/yt-transcribe/config.toml` |
| Linux | `~/.config/yt-transcribe/config.toml` |
| Windows | `%LOCALAPPDATA%\yt-transcribe\config.toml` |

Default config:

```toml
[defaults]
model = "turbo"              # tiny | base | small | medium | turbo | large-v3
language = ""                # empty = auto-detect per video
output_dir = "~/Downloads"   # transcripts saved here (video title as filename)
output_extension = "txt"

[whisper]
device = "cpu"               # cpu | cuda (use cuda if you have a GPU)
compute_type = "int8"        # int8 (fast CPU) | float16 (GPU) | float32 (precise)
beam_size = 5                # higher = more accurate, slower (1–10)
vad_filter = true            # skip silent segments (recommended)
```

**`output_dir`** — every transcription is auto-saved to `<output_dir>/<video title>.<output_extension>`. Supports `~` expansion. Useful for batch use.

**`device = "cuda"`** — if you have an NVIDIA GPU, set this and `compute_type = "float16"` for much faster transcription.

**`language`** — set a default language to skip auto-detection. Useful if you primarily transcribe content in one language.

## Whisper models

Model weights are downloaded from HuggingFace on first use and cached at:
- macOS/Linux: `~/.cache/huggingface/hub/`
- Windows: `%USERPROFILE%\.cache\huggingface\hub\`

Override with the `HF_HUB_CACHE` environment variable.

| Model | Size | Speed | Accuracy |
|---|---|---|---|
| `tiny` | ~75 MB | fastest | lowest |
| `base` | ~140 MB | fast | decent |
| `small` | ~460 MB | moderate | good |
| `medium` | ~1.5 GB | slow | better |
| `turbo` | ~800 MB | fast | best for size — **default** |
| `large-v3` | ~3 GB | slowest | highest |

`turbo` is the default: good accuracy across languages at reasonable speed. For quick drafts or batch jobs, `base` is a solid middle ground. See [performance benchmarks](TECHNICAL.md#whisper-performance) for timing data.

## Authentication (YouTube rate-limiting)

If YouTube rate-limits caption requests, you can supply cookies from a logged-in browser session:

```bash
YOUTUBE_COOKIES_FILE=/path/to/cookies.txt just run "https://youtube.com/watch?v=VIDEO_ID"
```

The file must be in Netscape cookie format (exportable via browser extensions like "Get cookies.txt").
