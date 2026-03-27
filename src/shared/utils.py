import re
from pathlib import Path


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
