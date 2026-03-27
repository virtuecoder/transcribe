"""
Config loaded from ~/.config/yt-transcribe/config.toml.
CLI flags always override config values.
"""

from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

from shared.config import init_config, load_toml

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
    return load_toml(CONFIG_PATH, _DEFAULTS)


def init() -> Path:
    return init_config(CONFIG_PATH, _DEFAULT_TOML)
