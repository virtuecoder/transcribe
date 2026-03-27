from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from anonymize import config as cfg_module
from shared.utils import sanitize_filename, unique_path

app = typer.Typer(help="Anonymize a text file by redacting PII.")
_console = Console(stderr=True)


def anonymize_text(text: str) -> str:
    """Redact PII from text. Extend this function with additional rules as needed."""
    import re

    # Email addresses
    text = re.sub(r"\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b", "[EMAIL]", text)
    # Phone numbers (common formats)
    text = re.sub(r"\b(\+?[\d][\d\s\-().]{7,}\d)\b", "[PHONE]", text)
    # IPv4 addresses
    text = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "[IP]", text)

    return text


@app.command(name="run")
def main(
    source: Path = typer.Argument(..., help="Path to a text file to anonymize"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save result to this exact path"),
    print_stdout: bool = typer.Option(False, "--print", "-p", help="Print result to stdout instead of saving"),
) -> None:
    if print_stdout and output is not None:
        _console.print("[yellow]Warning:[/yellow] --output is ignored when --print is used")

    console = Console(stderr=True)

    if not source.exists():
        _console.print(f"[red]Error:[/red] File not found: {source}")
        raise typer.Exit(1)

    cfg = cfg_module.load()
    d = cfg["defaults"]

    text = source.read_text(encoding="utf-8")

    with console.status("Anonymizing..."):
        result = anonymize_text(text)

    if print_stdout:
        print(result)
        return

    save_dir = Path(d["output_dir"]).expanduser() if d["output_dir"] else Path.cwd()
    stem = sanitize_filename(source.stem) + d["output_suffix"]
    out_path = output or save_dir / f"{stem}.{d['output_extension']}"
    out_path = unique_path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result, encoding="utf-8")
    console.print(f"[green]Saved to[/green] {out_path}")


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
