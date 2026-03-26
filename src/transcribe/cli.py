import re
import tempfile
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from transcribe import config as cfg_module

app = typer.Typer(help="Transcribe a YouTube video or local audio/video file.")
_console = Console(stderr=True)



def _is_local_file(source: str) -> bool:
    return Path(source).exists()


def _extract_video_id(url: str) -> Optional[str]:
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?#]|$)",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"^([0-9A-Za-z_-]{11})$",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def fetch_youtube_captions(video_id: str, language: Optional[str], console: Console) -> Optional[tuple[str, bool]]:
    """Returns (transcript_text, is_generated) or None if no captions available."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)
        # Materialise to avoid exhausting a one-shot iterator on the language scan below.
        all_transcripts = list(transcript_list)

        # prefer manually created transcripts over auto-generated
        transcript = None
        try:
            langs = [language] if language else [t.language_code for t in all_transcripts]
            transcript = transcript_list.find_manually_created_transcript(langs)
        except Exception:
            pass

        if transcript is None:
            transcript = next(iter(all_transcripts), None)

        if transcript is None:
            return None

        is_generated = getattr(transcript, "is_generated", True)
        fetched = transcript.fetch()
        text = "\n".join(
            s.text if hasattr(s, "text") else s["text"]
            for s in fetched
        )
        return text, is_generated
    except Exception:
        return None


def sanitize_filename(name: str, max_length: int = 200) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name).strip()
    return sanitized[:max_length]


def unique_path(path: Path) -> Path:
    """Return path unchanged if it doesn't exist, otherwise append (1), (2), … until free."""
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    counter = 1
    while True:
        candidate = path.with_name(f"{stem} ({counter}){suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _run_whisper(
    audio_file: str,
    model_size: str,
    language: Optional[str],
    whisper_cfg: dict,
    console: Console,
) -> tuple[str, float]:
    """Load Whisper and transcribe audio_file. Returns (transcript, elapsed_seconds)."""
    from faster_whisper import WhisperModel

    with console.status(f"Loading Whisper model [bold]{model_size}[/bold]..."):
        model = WhisperModel(
            model_size,
            device=whisper_cfg["device"],
            compute_type=whisper_cfg["compute_type"],
        )

    t0 = time.monotonic()
    with console.status("Transcribing..."):
        segments, transcription_info = model.transcribe(
            audio_file,
            language=language or None,
            beam_size=whisper_cfg["beam_size"],
            vad_filter=whisper_cfg["vad_filter"],
        )
        segments = list(segments)
    elapsed = time.monotonic() - t0

    console.print(
        f"[dim]Language: {transcription_info.language} "
        f"({transcription_info.language_probability:.0%} confidence)[/dim]"
    )
    return "\n".join(s.text.strip() for s in segments), elapsed


def _transcribe_youtube(
    url: str,
    video_id: str,
    model_size: str,
    language: Optional[str],
    force_whisper: bool,
    whisper_cfg: dict,
    console: Console,
) -> tuple[str, Optional[str]]:
    """Returns (transcript, video_title_or_None)."""
    transcript: Optional[str] = None
    video_title: Optional[str] = None

    if not force_whisper:
        with console.status("Fetching YouTube captions..."):
            captions_result = fetch_youtube_captions(video_id, language, console)

        if captions_result:
            transcript, is_generated = captions_result
            label = "auto-generated captions" if is_generated else "captions"
            console.print(f"[green]✓[/green] Found YouTube {label}")
        else:
            console.print("[yellow]No captions found[/yellow] — falling back to Whisper")

    if transcript is None:
        import yt_dlp

        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": str(Path(tmpdir) / "audio.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
            }

            with console.status("Downloading audio..."):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    download_info = ydl.extract_info(url, download=True)

            audio_files = list(Path(tmpdir).glob("audio.*"))
            if not audio_files:
                console.print("[red]Error:[/red] Audio download produced no file.")
                raise typer.Exit(1)

            transcript, elapsed = _run_whisper(str(audio_files[0]), model_size, language, whisper_cfg, console)

        video_title = download_info.get("title") if download_info else None
        console.print(f"[green]✓[/green] Transcription complete [dim]({elapsed:.0f}s)[/dim]")

    return transcript, video_title


def _fetch_title(url: str) -> Optional[str]:
    try:
        import json
        import urllib.request
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        with urllib.request.urlopen(oembed_url, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("title")
    except Exception:
        return None


def _save(transcript: str, out_path: Path, console: Console) -> None:
    out_path = unique_path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(transcript, encoding="utf-8")
    console.print(f"[green]Saved to[/green] {out_path}")


@app.command(name="run")
def main(
    source: str = typer.Argument(..., help="YouTube URL, video ID, or path to a local audio/video file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save transcript to this exact path (overrides output_dir in config)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Whisper model: tiny|base|small|medium|turbo|large-v3 (default from config)"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Force language code, e.g. en, fr, de (auto-detected if omitted)"),
    force_whisper: bool = typer.Option(False, "--force-whisper", "-w", help="Skip YouTube captions and always run Whisper (ignored for local files)"),
    print_stdout: bool = typer.Option(False, "--print", "-p", help="Print transcript to stdout instead of saving; suppresses all other output"),
) -> None:
    if print_stdout and output is not None:
        _console.print("[yellow]Warning:[/yellow] --output is ignored when --print is used")

    console = Console(stderr=True)

    cfg = cfg_module.load()
    d = cfg["defaults"]
    whisper_cfg = cfg["whisper"]

    effective_model = model or d["model"]
    effective_language = language or d["language"] or None

    if output is not None and not print_stdout and output.is_dir():
        _console.print(f"[red]Error:[/red] --output '{output}' is a directory, not a file path")
        raise typer.Exit(1)

    save_dir = Path(d["output_dir"]).expanduser() if d["output_dir"] else Path.cwd()

    if _is_local_file(source):
        file_path = Path(source)
        transcript, elapsed = _run_whisper(str(file_path), effective_model, effective_language, whisper_cfg, console)
        console.print(f"[green]✓[/green] Transcription complete [dim]({elapsed:.0f}s)[/dim]")

        if print_stdout:
            print(transcript)
            return

        out_path = output or save_dir / f"{sanitize_filename(file_path.stem)}.{d['output_extension']}"
        _save(transcript, out_path, console)
    else:
        video_id = _extract_video_id(source)
        if video_id is None:
            _console.print(f"[red]Error:[/red] Not a valid YouTube URL/ID or existing file path: {source}")
            raise typer.Exit(1)

        transcript, video_title = _transcribe_youtube(
            source, video_id, effective_model, effective_language, force_whisper, whisper_cfg, console
        )

        if print_stdout:
            print(transcript)
            return

        if output is None:
            if video_title is None:
                with console.status("Getting video title..."):
                    video_title = _fetch_title(source) or video_id
            out_path = save_dir / f"{sanitize_filename(video_title)}.{d['output_extension']}"
        else:
            out_path = output

        _save(transcript, out_path, console)


@app.command(name="config")
def config_cmd(
    edit: bool = typer.Option(False, "--edit", "-e", help="Open config in $EDITOR"),
    show: bool = typer.Option(False, "--show", "-s", help="Print current config"),
) -> None:
    """Show or edit the config file."""
    path = cfg_module.init()
    if edit:
        import os
        import subprocess
        import sys
        default_editor = "notepad" if sys.platform == "win32" else "nano"
        editor = os.environ.get("EDITOR", default_editor)
        subprocess.run([editor, str(path)])
    elif show:
        _console.print(path.read_text())
    else:
        _console.print(f"Config: [bold]{path}[/bold]")
        if not path.exists():
            _console.print("[dim]File does not exist yet — will be created on first edit.[/dim]")


if __name__ == "__main__":
    app()
