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

# Anonymize a text file by redacting PII
# Usage: just anonymize <path> [--output file.txt]
[positional-arguments]
anonymize *args:
    @uv run anonymize run "$@"

# Show, edit, or init the anonymize config file
# Usage: just anonymize-config [--edit] [--show]
[positional-arguments]
anonymize-config *args:
    uv run anonymize config "$@"

# Run unit tests (no network)
test:
    uv run pytest tests/ -m "not network" -v

# Run smoke tests against real YouTube (requires network)
smoke:
    uv run pytest tests/test_smoke.py -m network -v

# Run smoke tests in Docker across Python 3.11, 3.12, 3.13 in parallel
smoke-docker:
    #!/usr/bin/env bash
    set -euo pipefail
    versions=(3.11 3.12 3.13)
    pids=()
    for v in "${versions[@]}"; do
        (
            docker build -f Dockerfile.smoke --build-arg PYTHON_VERSION=$v \
                -t transcribe-smoke:$v . --quiet
            cid=$(docker run --cidfile /tmp/smoke-$v.cid -d transcribe-smoke:$v)
            docker wait "$cid" > /tmp/smoke-$v.exit
            exit_code=$(cat /tmp/smoke-$v.exit)
            if [ "$exit_code" -eq 0 ]; then
                echo "✓ Python $v passed"
            else
                echo "✗ Python $v FAILED — logs:"
                docker logs "$cid"
            fi
            rm -f /tmp/smoke-$v.cid /tmp/smoke-$v.exit
            docker rm "$cid"
        ) &
        pids+=($!)
    done
    for pid in "${pids[@]}"; do wait "$pid"; done
    for v in "${versions[@]}"; do docker rmi -f transcribe-smoke:$v 2>/dev/null; done

# List available Whisper models
models:
    @echo "tiny           (~75MB)   fastest, lowest accuracy"
    @echo "base           (~140MB)  fast, decent"
    @echo "small          (~460MB)  balanced"
    @echo "medium         (~1.5GB)  good"
    @echo "turbo          (~800MB)  fast + accurate  [default]"
    @echo "large-v3       (~3GB)    highest accuracy"
