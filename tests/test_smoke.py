"""
Smoke tests — hit real external services to verify the full dependency chain works.

Run with:   uv run pytest -m network -v
Excluded by default from: uv run pytest (fast unit tests only)
"""

import pytest
from typer.testing import CliRunner

from transcribe.cli import app

runner = CliRunner()

# "Me at the zoo" — first ever YouTube video, 18 s, always has captions.
ZOO_ID = "jNQXAC9IVRw"
ZOO_URL = f"https://www.youtube.com/watch?v={ZOO_ID}"


@pytest.mark.network
def test_youtube_captions_via_url():
    """youtube-transcript-api can fetch captions for a known public video."""
    result = runner.invoke(app, ["run", ZOO_URL, "--print"])
    assert result.exit_code == 0, result.output
    assert "elephant" in result.output.lower()


@pytest.mark.network
def test_youtube_captions_via_bare_id():
    """Bare video ID (no URL) is accepted and captions are fetched."""
    result = runner.invoke(app, ["run", ZOO_ID, "--print"])
    assert result.exit_code == 0, result.output
    assert "elephant" in result.output.lower()


@pytest.mark.network
def test_youtube_captions_saved_to_file(tmp_path):
    """Transcript is written to --output path when captions are available."""
    out = tmp_path / "zoo.txt"
    result = runner.invoke(app, ["run", ZOO_URL, "--output", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "elephant" in out.read_text().lower()
