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

# List available Whisper models
models:
    @echo "tiny           (~75MB)   fastest, lowest accuracy"
    @echo "base           (~140MB)  fast, decent"
    @echo "small          (~460MB)  balanced"
    @echo "medium         (~1.5GB)  good"
    @echo "turbo          (~800MB)  fast + accurate  [default]"
    @echo "large-v3       (~3GB)    highest accuracy"
