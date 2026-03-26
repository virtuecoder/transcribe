"""
Config loaded from ~/.config/yt-transcribe/config.toml.
CLI flags always override config values.
"""

import tomllib
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

CONFIG_PATH = Path(user_config_dir("yt-transcribe")) / "config.toml"

# Written on first run if the file doesn't exist yet.
_DEFAULT_TOML = """\
[defaults]
model = "turbo"         # tiny | base | small | medium | turbo | large-v3
language = ""           # empty = auto-detect per video
output_dir = "~/Downloads"  # transcripts are auto-saved here (uses video title as filename)
output_extension = "txt"

[whisper]
device = "cpu"          # cpu | cuda (use cuda if you have a GPU)
compute_type = "int8"   # int8 (fast CPU) | float16 (GPU) | float32 (precise)
beam_size = 5           # higher = more accurate, slower (1–10)
vad_filter = true       # skip silent segments (recommended)
"""

_DEFAULTS: dict[str, Any] = {
    "defaults": {
        "model": "turbo",
        "language": "",
        "output_dir": "~/Downloads",
        "output_extension": "txt",
    },
    "whisper": {
        "device": "cpu",
        "compute_type": "int8",
        "beam_size": 5,
        "vad_filter": True,
    },
}


def load() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return _deep_copy(_DEFAULTS)
    try:
        with open(CONFIG_PATH, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise SystemExit(f"Error: config file is not valid TOML ({CONFIG_PATH})\n{e}") from None
    return _merge(_deep_copy(_DEFAULTS), data)


def init() -> Path:
    """Create default config file if it doesn't exist. Returns the path."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(_DEFAULT_TOML)
    return CONFIG_PATH


def _deep_copy(d: dict) -> dict:
    return {k: dict(v) if isinstance(v, dict) else v for k, v in d.items()}


def _merge(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base
