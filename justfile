# Install dependencies and set up the venv
install:
    uv sync

# Transcribe a YouTube URL, video ID, or local audio/video file
# Usage: just run <url-or-path> [--model turbo] [--force-whisper] [--output file.txt]
[positional-arguments]
run *args:
    @uv run transcribe run "$@"

# Show, edit, or init the config file
# Usage: just config [--edit] [--show]
[positional-arguments]
config *args:
    uv run transcribe config "$@"

# Run unit tests (no network)
test:
    uv run pytest tests/ -m "not network" -v

# Run smoke tests against real YouTube (requires network)
smoke:
    uv run pytest tests/test_smoke.py -m network -v

# List available Whisper models
models:
    @echo "tiny           (~75MB)   fastest, lowest accuracy"
    @echo "base           (~140MB)  fast, decent"
    @echo "small          (~460MB)  balanced"
    @echo "medium         (~1.5GB)  good"
    @echo "turbo          (~800MB)  fast + accurate  [default]"
    @echo "large-v3       (~3GB)    highest accuracy"
