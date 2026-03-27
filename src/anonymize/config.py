"""
Config loaded from ~/.config/anonymize/config.toml.
CLI flags always override config values.
"""

from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

from shared.config import init_config, load_toml

CONFIG_PATH = Path(user_config_dir("anonymize")) / "config.toml"

_DEFAULT_TOML = """\
[defaults]
output_dir = "~/Downloads"  # anonymized files are saved here
output_extension = "txt"
output_suffix = "_anonymized"  # appended to the source filename
"""

_DEFAULTS: dict[str, Any] = {
    "defaults": {
        "output_dir": "~/Downloads",
        "output_extension": "txt",
        "output_suffix": "_anonymized",
    },
}


def load() -> dict[str, Any]:
    return load_toml(CONFIG_PATH, _DEFAULTS)


def init() -> Path:
    return init_config(CONFIG_PATH, _DEFAULT_TOML)
