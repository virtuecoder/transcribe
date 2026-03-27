"""Shared config helpers used by each tool's own config module."""

import tomllib
from pathlib import Path
from typing import Any


def load_toml(path: Path, defaults: dict[str, Any]) -> dict[str, Any]:
    """Load a TOML config file, merging over defaults. Returns merged dict."""
    if not path.exists():
        return _deep_copy(defaults)
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise SystemExit(f"Error: config file is not valid TOML ({path})\n{e}") from None
    return _merge(_deep_copy(defaults), data)


def init_config(path: Path, default_toml: str) -> Path:
    """Create default config file if it doesn't exist. Returns the path."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(default_toml)
    return path


def _deep_copy(d: dict) -> dict:
    return {k: dict(v) if isinstance(v, dict) else v for k, v in d.items()}


def _merge(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base
