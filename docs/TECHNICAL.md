# Technical Details

## Architecture

Two source files under `src/transcribe/`:

- **`cli.py`** — all CLI logic via Typer. Two commands: `run` (transcribe) and `config` (show/edit). The `run` command routes to either `_transcribe_youtube` or `_run_whisper` directly for local files.
- **`config.py`** — loads `~/.config/yt-transcribe/config.toml` via `platformdirs.user_config_dir`. Merges user TOML over hardcoded `_DEFAULTS`. Writes the file with documented defaults on `config --edit` if it doesn't exist yet.

## Flow

```
      ┌─────────────────────┐          ┌──────────────────────┐
      │   YouTube URL / ID  │          │   Local audio/video  │
      └──────────┬──────────┘          └───────────┬──────────┘
                 │ extract video ID                 │
                 ▼                                  │
    ┌────────────────────────┐                      │
    │  Fetch YouTube captions │  ◄── youtube-transcript-api
    │  (any available lang)   │      prefers manual over auto-generated
    └────────────┬───────────┘                      │
                 │                                  │
  ┌──────────────┴─────────────┐                    │
  │ Captions found?            │                    │
  ▼                            ▼                    │
Yes: done              No: fallback                 │
                              │                     │
                       ┌──────▼──────┐              │
                       │  Download   │  ◄── yt-dlp + ffmpeg
                       │  audio      │      best quality stream
                       └──────┬──────┘              │
                              │                     │
                              └──────────┬──────────┘
                                         │
                                  ┌──────▼──────┐
                                  │   Whisper   │  ◄── faster-whisper
                                  │  transcribe │      CTranslate2, CPU/GPU
                                  └──────┬──────┘
                                         │ temp audio deleted (YouTube only)
                                         ▼
                       ┌─────────────────────────────┐
                       │  --output / output_dir / stdout │
                       └─────────────────────────────┘
```

## Key behaviours

- **Lazy imports** — `faster-whisper` and `yt-dlp` are imported only when needed. Caption-only runs have no heavy dependency startup cost.
- **Temp audio** — YouTube audio is downloaded to `tempfile.TemporaryDirectory()` and deleted automatically after transcription.
- **Collision avoidance** — `unique_path()` appends `(1)`, `(2)`, … to avoid silently overwriting existing files.
- **`--print` mode** — suppresses all Rich console output and writes only the transcript to stdout, safe for piping.
- **Config merging** — `_merge()` deep-merges user TOML over hardcoded defaults, so missing keys always fall back to defaults.

## Caption lookup

Uses [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) to fetch captions from YouTube's internal API — no audio download needed, instant. Prefers manually uploaded captions over auto-generated ones. Falls back to Whisper when:

- The video owner disabled captions
- The video is too new for auto-generation to finish
- YouTube rate-limits the request (use `YOUTUBE_COOKIES_FILE` env var to mitigate)

## Whisper transcription

1. **Download** — `yt-dlp` fetches the best available audio stream to a temp directory (`bestaudio/best`).
2. **Transcribe** — `faster-whisper` runs the Whisper model with `vad_filter=True` to skip silent segments. Language is auto-detected unless overridden.
3. **Cleanup** — temp audio deleted automatically when the `TemporaryDirectory` context exits.

`faster-whisper` uses [CTranslate2](https://github.com/OpenNMT/CTranslate2) under the hood — 4–8× faster than OpenAI's original Whisper on CPU with `int8` quantization.

## Supported file formats

`faster-whisper` uses [PyAV](https://github.com/PyAV-Org/PyAV) (bundled FFmpeg) to decode audio, so any format FFmpeg handles is accepted — no system ffmpeg installation required for local files.

| Type | Extensions |
|---|---|
| Audio | `.mp3` `.m4a` `.aac` `.wav` `.flac` `.ogg` `.opus` `.wma` `.aiff` |
| Video (audio extracted) | `.mp4` `.mkv` `.mov` `.avi` `.webm` `.ts` |

## Whisper performance

Measured on a 4m 52s audio clip (Polish speech, CPU, `int8`):

| Model | Elapsed | Seconds per audio-minute | Time for 1h video |
|---|---|---|---|
| `tiny` | 15.4s | 3.2s | ~3 min |
| `base` | 25.4s | 5.2s | ~5 min |
| `small` | 70.1s | 14.4s | ~14 min |
| `turbo` | 90.8s | 18.7s | ~19 min |

`medium` and `large-v3` not measured — extrapolate the trend.

- `tiny` is nearly 6× faster than `turbo` on CPU
- `turbo` is the default: much better accuracy (especially non-English), acceptable speed
- GPU with `float16` compute type will be dramatically faster across all models

## Dependencies

| Package | Purpose |
|---|---|
| [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) | Fetch YouTube captions |
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | Download audio from YouTube |
| [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) | Local speech-to-text via CTranslate2 |
| [`typer`](https://typer.tiangolo.com/) | CLI framework |
| [`rich`](https://rich.readthedocs.io/) | Terminal output formatting |
| [`platformdirs`](https://platformdirs.readthedocs.io/) | Platform-appropriate config paths |

## Tests

```bash
just test    # unit tests, no network required
just smoke   # integration tests against real YouTube (requires network)
```

Tests live in `tests/`. Unit tests are marked without `@pytest.mark.network`; smoke tests use `@pytest.mark.network` and are excluded from `just test`.
