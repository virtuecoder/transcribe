import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from transcribe.cli import _extract_video_id, sanitize_filename, unique_path, app

runner = CliRunner()


class TestExtractVideoId:
    def test_standard_watch_url(self):
        assert _extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_watch_url_with_extra_params(self):
        assert _extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&list=PLxxx") == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert _extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url_with_params(self):
        assert _extract_video_id("https://youtu.be/dQw4w9WgXcQ?si=abc123") == "dQw4w9WgXcQ"

    def test_embed_url(self):
        assert _extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_bare_video_id(self):
        assert _extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_invalid_returns_none(self):
        assert _extract_video_id("https://example.com/watch?v=tooshort") is None

    def test_empty_string_returns_none(self):
        assert _extract_video_id("") is None

    def test_random_text_returns_none(self):
        assert _extract_video_id("not a url at all") is None

    def test_id_with_hyphens_and_underscores(self):
        # YouTube IDs are exactly 11 chars and can contain - and _
        assert _extract_video_id("abc-def_ghi") == "abc-def_ghi"


class TestSanitizeFilename:
    @pytest.mark.parametrize("char", ['<', '>', ':', '"', '/', '\\', '|', '?', '*'])
    def test_illegal_chars_replaced(self, char):
        assert "_" in sanitize_filename(f"name{char}here")

    def test_normal_name_unchanged(self):
        assert sanitize_filename("My Video Title") == "My Video Title"

    def test_leading_trailing_spaces_stripped(self):
        assert sanitize_filename("  hello  ") == "hello"

    def test_max_length_truncated(self):
        long_name = "a" * 300
        assert len(sanitize_filename(long_name)) == 200

    def test_custom_max_length(self):
        assert len(sanitize_filename("a" * 50, max_length=10)) == 10

    def test_empty_string(self):
        assert sanitize_filename("") == ""


class TestUniquePath:
    def test_nonexistent_path_returned_unchanged(self, tmp_path):
        p = tmp_path / "file.txt"
        assert unique_path(p) == p

    def test_existing_file_gets_counter(self, tmp_path):
        p = tmp_path / "file.txt"
        p.write_text("x")
        result = unique_path(p)
        assert result == tmp_path / "file (1).txt"

    def test_counter_increments_until_free(self, tmp_path):
        p = tmp_path / "file.txt"
        p.write_text("x")
        (tmp_path / "file (1).txt").write_text("x")
        (tmp_path / "file (2).txt").write_text("x")
        assert unique_path(p) == tmp_path / "file (3).txt"

    def test_preserves_extension(self, tmp_path):
        p = tmp_path / "audio.mp3"
        p.write_text("x")
        assert unique_path(p).suffix == ".mp3"

    def test_no_extension(self, tmp_path):
        p = tmp_path / "transcript"
        p.write_text("x")
        result = unique_path(p)
        assert result == tmp_path / "transcript (1)"


# ---------------------------------------------------------------------------
# Integration tests for the `run` command (external I/O fully mocked)
# ---------------------------------------------------------------------------

YT_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
YT_ID = "jNQXAC9IVRw"
CAPTION_TEXT = "Hello from captions"
WHISPER_TEXT = "Hello from Whisper"


@pytest.fixture()
def captions_found():
    """Patch fetch_youtube_captions to return a fake transcript."""
    with patch("transcribe.cli.fetch_youtube_captions", return_value=(CAPTION_TEXT, False)) as m:
        yield m


@pytest.fixture()
def no_captions():
    """Patch fetch_youtube_captions to signal no captions available."""
    with patch("transcribe.cli.fetch_youtube_captions", return_value=None) as m:
        yield m


@pytest.fixture()
def whisper_ok():
    """Patch _run_whisper to return a fake transcript without loading a model."""
    with patch("transcribe.cli._run_whisper", return_value=(WHISPER_TEXT, 1.5)) as m:
        yield m


@pytest.fixture()
def fake_yt_dlp(tmp_path):
    """Patch yt_dlp and TemporaryDirectory so no audio is downloaded."""
    audio_file = tmp_path / "audio.webm"
    audio_file.write_bytes(b"fake")

    class FakeYDL:
        def __init__(self, opts):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def extract_info(self, url, download):
            return {"title": "Fake Video Title"}

    # yt_dlp is imported lazily inside the function, so patch the module directly
    with patch("yt_dlp.YoutubeDL", FakeYDL):
        # Make TemporaryDirectory yield our tmp_path so the glob finds the audio file
        mock_td = MagicMock()
        mock_td.return_value.__enter__ = MagicMock(return_value=str(tmp_path))
        mock_td.return_value.__exit__ = MagicMock(return_value=False)
        with patch("transcribe.cli.tempfile.TemporaryDirectory", mock_td):
            yield tmp_path


class TestRunCommand:
    # --- caption happy path ---

    def test_print_with_captions(self, captions_found):
        result = runner.invoke(app, ["run", YT_URL, "--print"])
        assert result.exit_code == 0
        assert CAPTION_TEXT in result.stdout

    def test_bare_video_id_with_captions(self, captions_found):
        result = runner.invoke(app, ["run", YT_ID, "--print"])
        assert result.exit_code == 0
        assert CAPTION_TEXT in result.stdout

    def test_captions_saved_to_output(self, captions_found, tmp_path):
        out = tmp_path / "out.txt"
        result = runner.invoke(app, ["run", YT_URL, "--output", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        assert out.read_text() == CAPTION_TEXT

    def test_captions_saved_auto_named(self, captions_found, tmp_path):
        """Without --output, file is saved under output_dir from config."""
        with patch("transcribe.cli._fetch_title", return_value="My Video"):
            with patch("transcribe.cli.cfg_module.load") as mock_load:
                mock_load.return_value = {
                    "defaults": {"model": "turbo", "language": "", "output_dir": str(tmp_path), "output_extension": "txt"},
                    "whisper": {"device": "cpu", "compute_type": "int8", "beam_size": 5, "vad_filter": True},
                }
                result = runner.invoke(app, ["run", YT_URL])
        assert result.exit_code == 0
        assert (tmp_path / "My Video.txt").exists()

    # --- Whisper fallback ---

    def test_print_whisper_fallback(self, no_captions, whisper_ok, fake_yt_dlp):
        result = runner.invoke(app, ["run", YT_URL, "--print"])
        assert result.exit_code == 0
        assert WHISPER_TEXT in result.stdout

    def test_force_whisper_skips_captions(self, captions_found, whisper_ok, fake_yt_dlp):
        result = runner.invoke(app, ["run", YT_URL, "--force-whisper", "--print"])
        assert result.exit_code == 0
        captions_found.assert_not_called()
        assert WHISPER_TEXT in result.stdout

    # --- local file ---

    def test_local_file_whisper(self, whisper_ok, tmp_path):
        audio = tmp_path / "clip.mp3"
        audio.write_bytes(b"fake audio")
        out = tmp_path / "clip.txt"
        result = runner.invoke(app, ["run", str(audio), "--output", str(out)])
        assert result.exit_code == 0
        assert out.read_text() == WHISPER_TEXT
        whisper_ok.assert_called_once()

    def test_local_file_print(self, whisper_ok, tmp_path):
        audio = tmp_path / "clip.mp3"
        audio.write_bytes(b"fake audio")
        result = runner.invoke(app, ["run", str(audio), "--print"])
        assert result.exit_code == 0
        assert WHISPER_TEXT in result.stdout

    # --- error cases ---

    def test_invalid_source_exits_nonzero(self):
        result = runner.invoke(app, ["run", "not-a-url-or-file"])
        assert result.exit_code != 0

    def test_output_is_directory_exits_nonzero(self, captions_found, tmp_path):
        result = runner.invoke(app, ["run", YT_URL, "--output", str(tmp_path)])
        assert result.exit_code != 0

    def test_print_and_output_warns(self, captions_found, tmp_path):
        out = tmp_path / "out.txt"
        result = runner.invoke(app, ["run", YT_URL, "--print", "--output", str(out)])
        assert result.exit_code == 0
        assert "Warning" in result.output
