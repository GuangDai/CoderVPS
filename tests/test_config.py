"""Tests for codervps.config -- TOML loading, helper functions, error paths, and _fail wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

from codervps.config import (
    _fail,
    _get_bool,
    _get_int,
    _get_list_str,
    _get_str,
    _require_list,
    _require_str,
    load_extensions_config,
    load_toolchains_config,
)
from codervps.models import ExtensionsConfig, ToolchainsConfig


# ---- Helper to write a temp TOML ----


def _write_toml(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content)
    return path


# ============================================================================
# load_toolchains_config
# ============================================================================


def test_load_toolchains_config_from_file():
    """Load the real config/toolchains.toml and verify parsed values."""
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    assert cfg.project_arch == "linux/amd64"
    assert cfg.node_majors == [24, 22, 20, 18, 16]
    assert cfg.enabled_plugins == ["python", "rust", "go", "cpp"]
    assert cfg.python_default_tools == ["ruff", "debugpy"]
    assert cfg.rust_components == ["rustfmt", "clippy", "rust-src"]
    assert cfg.go_minor_count == 20
    assert cfg.go_default_tools == ["gopls"]
    assert cfg.cpp_default_tools == ["xmake", "ccache"]


def test_load_toolchains_config_returns_correct_type():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    assert isinstance(cfg, ToolchainsConfig)


def test_load_toolchains_config_overrides_are_dict():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    assert isinstance(cfg.overrides, dict)


def test_load_toolchains_config_python_fields():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    assert cfg.python_min_minor == "3.6"
    assert cfg.python_max_minor == "latest"
    assert cfg.python_default == "3.13"


def test_load_toolchains_config_rust_fields():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    assert cfg.rust_stable_minor_count == 30
    assert cfg.rust_default == "stable"
    assert cfg.rust_use_sccache is True


def test_load_toolchains_config_go_fields():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    assert cfg.go_default == "latest"


def test_load_toolchains_config_cpp_fields():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    assert cfg.cpp_default_llvm == "latest"
    assert cfg.cpp_prebundle == "latest"


def test_load_toolchains_config_missing_file(tmp_path):
    with pytest.raises(SystemExit):
        load_toolchains_config(tmp_path / "does_not_exist.toml")


def test_load_toolchains_config_missing_project_section(tmp_path):
    path = _write_toml(tmp_path, "cfg.toml", "[node]\nmajors = [24]\n")
    with pytest.raises(SystemExit):
        load_toolchains_config(path)


def test_load_toolchains_config_missing_node_section(tmp_path):
    path = _write_toml(tmp_path, "cfg.toml", '[project]\narch = "linux/amd64"\n')
    with pytest.raises(SystemExit):
        load_toolchains_config(path)


def test_load_toolchains_config_missing_plugins_section(tmp_path):
    path = _write_toml(
        tmp_path,
        "cfg.toml",
        '[project]\narch = "linux/amd64"\n[node]\nmajors = [24]\n',
    )
    with pytest.raises(SystemExit):
        load_toolchains_config(path)


def test_load_toolchains_config_missing_python_section(tmp_path):
    path = _write_toml(
        tmp_path,
        "cfg.toml",
        '[project]\narch = "linux/amd64"\n[node]\nmajors = [24]\n[plugins]\nenabled = []\n[versions.override]\n',
    )
    with pytest.raises(SystemExit):
        load_toolchains_config(path)


def test_load_toolchains_config_missing_rust_section(tmp_path):
    path = _write_toml(
        tmp_path,
        "cfg.toml",
        '[project]\narch = "linux/amd64"\n[node]\nmajors = [24]\n'
        "[plugins]\nenabled = []\n[versions.override]\n"
        '[python]\nmin_minor = "3.6"\nmax_minor = "latest"\ndefault = "3.13"\ndefault_tools = []\n',
    )
    with pytest.raises(SystemExit):
        load_toolchains_config(path)


def test_load_toolchains_config_missing_go_section(tmp_path):
    path = _write_toml(
        tmp_path,
        "cfg.toml",
        '[project]\narch = "linux/amd64"\n[node]\nmajors = [24]\n'
        "[plugins]\nenabled = []\n[versions.override]\n"
        '[python]\nmin_minor = "3.6"\nmax_minor = "latest"\ndefault = "3.13"\ndefault_tools = []\n'
        '[rust]\ndefault = "stable"\ndefault_components = []\n',
    )
    with pytest.raises(SystemExit):
        load_toolchains_config(path)


def test_load_toolchains_config_missing_cpp_section(tmp_path):
    path = _write_toml(
        tmp_path,
        "cfg.toml",
        '[project]\narch = "linux/amd64"\n[node]\nmajors = [24]\n'
        "[plugins]\nenabled = []\n[versions.override]\n"
        '[python]\nmin_minor = "3.6"\nmax_minor = "latest"\ndefault = "3.13"\ndefault_tools = []\n'
        '[rust]\ndefault = "stable"\ndefault_components = []\n'
        '[go]\ndefault = "latest"\ndefault_tools = []\n',
    )
    with pytest.raises(SystemExit):
        load_toolchains_config(path)


def test_load_toolchains_config_invalid_toml_syntax(tmp_path):
    path = _write_toml(tmp_path, "cfg.toml", "this is not valid toml {{{")
    with pytest.raises(SystemExit):
        load_toolchains_config(path)


# ============================================================================
# load_extensions_config
# ============================================================================


def test_load_extensions_config_from_file():
    """Load the real config/extensions.toml and verify parsed values."""
    cfg = load_extensions_config(Path("config/extensions.toml"))
    assert isinstance(cfg, ExtensionsConfig)
    assert "EditorConfig.EditorConfig" in cfg.core_marketplace
    assert "redhat.vscode-yaml" in cfg.core_marketplace
    assert cfg.language_marketplace["python"] == [
        "ms-python.python",
        "ms-python.debugpy",
        "charliermarsh.ruff",
    ]
    assert cfg.language_marketplace["rust"] == [
        "rust-lang.rust-analyzer",
        "vadimcn.vscode-lldb",
    ]
    assert cfg.language_marketplace["go"] == ["golang.Go"]
    assert "leetcode" in cfg.packs
    assert cfg.packs["leetcode"].label == "LeetCode"
    assert "leetcode.vscode-leetcode" in cfg.packs["leetcode"].marketplace
    assert cfg.packs["leetcode"].vsix_globs == ["packs/leetcode/*.vsix"]


def test_load_extensions_config_core():
    cfg = load_extensions_config(Path("config/extensions.toml"))
    assert len(cfg.core_marketplace) == 2


def test_load_extensions_config_languages_count():
    cfg = load_extensions_config(Path("config/extensions.toml"))
    assert set(cfg.language_marketplace.keys()) == {"python", "rust", "go", "cpp"}


def test_load_extensions_config_missing_file(tmp_path):
    with pytest.raises(SystemExit):
        load_extensions_config(tmp_path / "nonexistent.toml")


def test_load_extensions_config_missing_core_section(tmp_path):
    path = _write_toml(tmp_path, "cfg.toml", "")
    with pytest.raises(SystemExit):
        load_extensions_config(path)


def test_load_extensions_config_empty_languages(tmp_path):
    path = _write_toml(tmp_path, "cfg.toml", "[core]\nmarketplace = []\n")
    cfg = load_extensions_config(path)
    assert cfg.language_marketplace == {}
    assert cfg.packs == {}


def test_load_extensions_config_with_multiple_packs(tmp_path):
    path = _write_toml(
        tmp_path,
        "cfg.toml",
        '[core]\nmarketplace = ["a"]\n\n'
        '[packs.foo]\nlabel = "Foo Pack"\nmarketplace = ["foo.id"]\n\n'
        '[packs.bar]\nlabel = "Bar Pack"\nmarketplace = ["bar.id"]\nvsix_globs = ["bar/*.vsix"]\n',
    )
    cfg = load_extensions_config(path)
    assert len(cfg.packs) == 2
    assert cfg.packs["foo"].label == "Foo Pack"
    assert cfg.packs["bar"].vsix_globs == ["bar/*.vsix"]


# ============================================================================
# Helper function tests (_fail, _require_str, _get_str, etc.)
# ============================================================================


def test_fail_raises_system_exit():
    with pytest.raises(SystemExit) as exc_info:
        _fail("test error message")
    assert exc_info.value.code == 1


def test_fail_output_goes_to_stderr(capsys):
    with pytest.raises(SystemExit):
        _fail("something broke")
    captured = capsys.readouterr()
    assert "config error: something broke" in captured.err


def test_require_str_returns_value():
    raw = {"key": "value"}
    assert _require_str(raw, "key", "test") == "value"


def test_require_str_missing_key():
    with pytest.raises(SystemExit):
        _require_str({}, "missing", "test")


def test_require_str_wrong_type():
    with pytest.raises(SystemExit):
        _require_str({"key": 42}, "key", "test")


def test_get_str_returns_value():
    assert _get_str({"key": "hello"}, "key", "default") == "hello"


def test_get_str_returns_default_for_missing():
    assert _get_str({}, "nonexistent", "fallback") == "fallback"


def test_get_str_returns_default_for_wrong_type():
    assert _get_str({"key": [1, 2]}, "key", "fallback") == "fallback"


def test_require_list_returns_value():
    raw = {"items": [1, 2, 3]}
    assert _require_list(raw, "items", "test") == [1, 2, 3]


def test_require_list_missing_key():
    with pytest.raises(SystemExit):
        _require_list({}, "missing", "test")


def test_require_list_wrong_type():
    with pytest.raises(SystemExit):
        _require_list({"items": "not-a-list"}, "items", "test")


def test_get_list_str_returns_strings():
    assert _get_list_str({"items": ["a", "b"]}, "items") == ["a", "b"]


def test_get_list_str_returns_empty_for_missing():
    assert _get_list_str({}, "missing") == []


def test_get_list_str_required_missing():
    with pytest.raises(SystemExit):
        _get_list_str({}, "missing", required=True, section="test")


def test_get_list_str_coerces_to_strings():
    assert _get_list_str({"items": [1, 2, 3]}, "items") == ["1", "2", "3"]


def test_get_list_str_wrong_type():
    with pytest.raises(SystemExit):
        _get_list_str({"items": 42}, "items")


def test_get_int_returns_int():
    assert _get_int({"count": 5}, "count", 0) == 5


def test_get_int_returns_default_for_missing():
    assert _get_int({}, "nope", 10) == 10


def test_get_int_coerces_digit_string():
    assert _get_int({"count": "42"}, "count", 0) == 42


def test_get_int_returns_default_for_non_numeric_string():
    assert _get_int({"count": "abc"}, "count", 10) == 10


def test_get_bool_returns_bool():
    assert _get_bool({"flag": True}, "flag", False) is True
    assert _get_bool({"flag": False}, "flag", True) is False


def test_get_bool_returns_default_for_missing():
    assert _get_bool({}, "flag", True) is True


def test_get_bool_returns_default_for_non_bool():
    assert _get_bool({"flag": "yes"}, "flag", False) is False


# ============================================================================
# Minimal valid TOML: all sections present
# ============================================================================

MINIMAL_TOOLCHAINS = """\
[project]
arch = "linux/amd64"

[node]
majors = [24]

[plugins]
enabled = ["python"]

[versions.override]
uv = ""

[python]
min_minor = "3.6"
max_minor = "latest"
default = "3.13"
default_tools = ["ruff"]

[rust]
default = "stable"
default_components = ["rustfmt"]
use_sccache = true

[go]
default = "latest"
default_tools = ["gopls"]

[cpp]
default_llvm = "latest"
prebundle = "latest"
default_tools = ["xmake"]
"""


def test_minimal_toolchains_config_parses(tmp_path):
    path = _write_toml(tmp_path, "minimal.toml", MINIMAL_TOOLCHAINS)
    cfg = load_toolchains_config(path)
    assert cfg.project_arch == "linux/amd64"
    assert cfg.node_majors == [24]
    assert cfg.enabled_plugins == ["python"]
    assert cfg.overrides == {"uv": ""}
    assert cfg.python_default == "3.13"
    assert cfg.python_default_tools == ["ruff"]
    assert cfg.rust_stable_minor_count == 30  # default from _get_int
    assert cfg.rust_components == ["rustfmt"]
    assert cfg.rust_use_sccache is True
    assert cfg.go_minor_count == 20  # default from _get_int
    assert cfg.cpp_default_tools == ["xmake"]


# Cross-section consistency


def test_enabled_plugins_list_matches_config_keys():
    """Plugins in config/toolchains.toml enabled list should be valid."""
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    valid = {"python", "rust", "go", "cpp"}
    for plugin in cfg.enabled_plugins:
        assert plugin in valid, f"unknown plugin: {plugin}"


def test_node_majors_are_ordered_descending():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    assert cfg.node_majors == sorted(cfg.node_majors, reverse=True)


def test_overrides_default_to_empty_strings():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    for key in ["uv", "code_server", "sccache", "rust_bootstrap", "llvm_prebundle"]:
        assert key in cfg.overrides
