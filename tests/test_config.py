import tomllib
import pytest
from pathlib import Path
from unittest.mock import patch

from transcribe import config as cfg_module
from shared import config as shared_cfg


class TestDeepCopy:
    def test_mutating_copy_does_not_affect_original(self):
        original = {"a": {"x": 1}, "b": 2}
        copy = shared_cfg._deep_copy(original)
        copy["a"]["x"] = 99
        assert original["a"]["x"] == 1

    def test_top_level_scalar_copied(self):
        original = {"a": {"x": 1}, "b": 2}
        copy = shared_cfg._deep_copy(original)
        assert copy == original


class TestMerge:
    def test_override_replaces_leaf(self):
        base = {"defaults": {"model": "turbo", "language": ""}}
        result = shared_cfg._merge(base, {"defaults": {"model": "large-v3"}})
        assert result["defaults"]["model"] == "large-v3"
        assert result["defaults"]["language"] == ""  # untouched

    def test_unknown_key_in_override_is_added(self):
        base = {"defaults": {"model": "turbo"}}
        result = shared_cfg._merge(base, {"new_section": {"foo": "bar"}})
        assert result["new_section"] == {"foo": "bar"}

    def test_nested_dicts_merged_not_replaced(self):
        base = {"whisper": {"device": "cpu", "beam_size": 5}}
        result = shared_cfg._merge(base, {"whisper": {"device": "cuda"}})
        assert result["whisper"]["beam_size"] == 5  # preserved
        assert result["whisper"]["device"] == "cuda"

    def test_scalar_override_replaces_dict(self):
        # Non-dict override should win even if base has a dict
        base = {"key": {"nested": 1}}
        result = shared_cfg._merge(base, {"key": "flat"})
        assert result["key"] == "flat"


class TestLoad:
    def test_missing_config_returns_defaults(self, tmp_path):
        missing = tmp_path / "nonexistent.toml"
        with patch.object(cfg_module, "CONFIG_PATH", missing):
            cfg = cfg_module.load()
        assert cfg["defaults"]["model"] == "turbo"
        assert cfg["whisper"]["device"] == "cpu"

    def test_partial_toml_merged_with_defaults(self, tmp_path):
        toml_file = tmp_path / "config.toml"
        toml_file.write_text('[defaults]\nmodel = "large-v3"\n')
        with patch.object(cfg_module, "CONFIG_PATH", toml_file):
            cfg = cfg_module.load()
        assert cfg["defaults"]["model"] == "large-v3"
        assert cfg["defaults"]["output_extension"] == "txt"  # from defaults

    def test_invalid_toml_raises_system_exit(self, tmp_path):
        bad = tmp_path / "config.toml"
        bad.write_text("this is not valid toml ][")
        with patch.object(cfg_module, "CONFIG_PATH", bad):
            with pytest.raises(SystemExit, match="not valid TOML"):
                cfg_module.load()
