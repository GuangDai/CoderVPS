"""Tests for codervps.catalog and codervps.discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from codervps.catalog import (
    _latest_node_patch,
    _node_status,
    refresh_catalog,
    refresh_catalog_from_path,
)
from codervps.config import load_toolchains_config
from codervps.discovery import go_downloads, load_json, node_index


# ---- Discovery helpers ----


def test_load_json_reads_file(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('{"key": "value"}')
    result = load_json(path)
    assert result == {"key": "value"}


def test_load_json_reads_array(tmp_path):
    path = tmp_path / "test.json"
    path.write_text("[1, 2, 3]")
    result = load_json(path)
    assert result == [1, 2, 3]


def test_node_index_with_fixtures():
    result = node_index(fixture_dir=Path("tests/fixtures"))
    assert isinstance(result, list)
    assert len(result) > 0
    assert any("v24" in str(e["version"]) for e in result)


def test_node_index_without_fixtures_no_error():
    result = node_index()
    assert isinstance(result, list)


def test_go_downloads_with_fixtures():
    result = go_downloads(fixture_dir=Path("tests/fixtures"))
    assert isinstance(result, list)
    assert len(result) > 0
    assert any("go1.24.9" in str(e.get("version", "")) for e in result)


def test_go_downloads_without_fixtures_no_error():
    result = go_downloads()
    assert isinstance(result, list)


# ---- Node status helper ----


def test_node_status_active_lts():
    assert _node_status(24) == "active_lts"
    assert _node_status(25) == "active_lts"


def test_node_status_maintenance_lts():
    assert _node_status(22) == "maintenance_lts"
    assert _node_status(23) == "maintenance_lts"


def test_node_status_eol():
    assert _node_status(20) == "eol"
    assert _node_status(18) == "eol"
    assert _node_status(16) == "eol"
    assert _node_status(14) == "eol"


# ---- Node patch lookup ----


def test_latest_node_patch_returns_version():
    index = [{"version": "v24.11.1"}, {"version": "v24.10.0"}, {"version": "v22.21.0"}]
    assert _latest_node_patch(index, 24) == "24.11.1"
    assert _latest_node_patch(index, 22) == "22.21.0"


def test_latest_node_patch_missing_raises():
    index = [{"version": "v24.11.1"}]
    with pytest.raises(ValueError, match="missing Node major 22"):
        _latest_node_patch(index, 22)


def test_latest_node_patch_skips_non_matching():
    index = [
        {"version": "v24.11.1"},
        {"version": "v23.0.0"},
        {"version": "v22.21.0"},
    ]
    assert _latest_node_patch(index, 22) == "22.21.0"


# ---- Catalog refresh ----


def test_refresh_catalog_from_fixtures():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    assert catalog["schema_version"] == 1
    assert catalog["arch"] == "linux/amd64"
    assert sorted(catalog["node"]["majors"]) == ["16", "18", "20", "22", "24"]
    assert "python" in catalog["plugins"]
    assert "rust" in catalog["plugins"]
    assert "go" in catalog["plugins"]
    assert "cpp" in catalog["plugins"]


def test_refresh_catalog_node_versions():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    assert catalog["node"]["majors"]["24"]["version"] == "24.11.1"
    assert catalog["node"]["majors"]["24"]["status"] == "active_lts"
    assert catalog["node"]["majors"]["22"]["version"] == "22.21.0"
    assert catalog["node"]["majors"]["22"]["status"] == "maintenance_lts"
    assert catalog["node"]["majors"]["16"]["version"] == "16.20.2"
    assert catalog["node"]["majors"]["16"]["status"] == "eol"


def test_refresh_catalog_base_info():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    assert catalog["base"]["source"] == "codercom/example-base"
    assert catalog["base"]["ubuntu"] == "noble"
    assert catalog["base"]["tag"] == "ubuntu-noble-20260511"


def test_refresh_catalog_has_generated_at():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    assert "T" in catalog["generated_at"]


def test_refresh_catalog_plugin_defaults():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    assert catalog["plugins"]["python"]["defaults"]["version"] == "3.13"
    assert catalog["plugins"]["rust"]["defaults"]["toolchain"] == "stable"
    assert catalog["plugins"]["go"]["defaults"]["version"] == "latest"
    assert catalog["plugins"]["cpp"]["defaults"]["llvm"] == "latest"


def test_refresh_catalog_tools():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    assert "uv" in catalog["tools"]
    assert "code_server" in catalog["tools"]
    assert "sccache" in catalog["tools"]
    assert "llvm_prebundle" in catalog["tools"]


def test_refresh_catalog_go_versions_from_fixtures():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    go_versions = catalog["plugins"]["go"]["versions"]
    assert len(go_versions) >= 4
    version_values = [v["version"] for v in go_versions]
    assert "1.24.9" in version_values
    assert "1.23.12" in version_values


def test_refresh_catalog_go_versions_have_sha256():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    go_versions = catalog["plugins"]["go"]["versions"]
    for v in go_versions:
        if v["status"] == "active":
            assert v["sha256"], f"Missing SHA256 for Go {v['version']}"


def test_refresh_catalog_from_path():
    catalog = refresh_catalog_from_path("config/toolchains.toml", fixture_dir="tests/fixtures")
    assert catalog["schema_version"] == 1


def test_refresh_catalog_with_overrides(tmp_path):
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    cfg_with_overrides = type(cfg)(
        project_arch=cfg.project_arch,
        node_majors=[24],
        enabled_plugins=["python"],
        overrides={"uv": "0.99.0", "code_server": "5.0.0"},
        python_min_minor=cfg.python_min_minor,
        python_max_minor=cfg.python_max_minor,
        python_default=cfg.python_default,
        python_default_tools=cfg.python_default_tools,
        rust_stable_minor_count=cfg.rust_stable_minor_count,
        rust_default=cfg.rust_default,
        rust_components=cfg.rust_components,
        rust_use_sccache=cfg.rust_use_sccache,
        go_minor_count=cfg.go_minor_count,
        go_default=cfg.go_default,
        go_default_tools=cfg.go_default_tools,
        cpp_default_llvm=cfg.cpp_default_llvm,
        cpp_prebundle=cfg.cpp_prebundle,
        cpp_default_tools=cfg.cpp_default_tools,
    )
    catalog = refresh_catalog(cfg_with_overrides, fixture_dir=Path("tests/fixtures"))
    assert catalog["tools"]["uv"]["version"] == "0.99.0"
    assert catalog["tools"]["code_server"]["version"] == "5.0.0"


def test_refresh_catalog_without_override_defaults():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    cfg_empty = type(cfg)(
        project_arch=cfg.project_arch,
        node_majors=[24],
        enabled_plugins=["python"],
        overrides={},
        python_min_minor=cfg.python_min_minor,
        python_max_minor=cfg.python_max_minor,
        python_default=cfg.python_default,
        python_default_tools=cfg.python_default_tools,
        rust_stable_minor_count=cfg.rust_stable_minor_count,
        rust_default=cfg.rust_default,
        rust_components=cfg.rust_components,
        rust_use_sccache=cfg.rust_use_sccache,
        go_minor_count=cfg.go_minor_count,
        go_default=cfg.go_default,
        go_default_tools=cfg.go_default_tools,
        cpp_default_llvm=cfg.cpp_default_llvm,
        cpp_prebundle=cfg.cpp_prebundle,
        cpp_default_tools=cfg.cpp_default_tools,
    )
    catalog = refresh_catalog(cfg_empty, fixture_dir=Path("tests/fixtures"))
    assert catalog["tools"]["uv"]["version"] == "auto"
    assert catalog["tools"]["sccache"]["version"] == "auto"


def test_refresh_catalog_schema_version_is_int():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    assert isinstance(catalog["schema_version"], int)


# ---- Node index from real file verifies structure ----


def test_node_index_fixture_has_all_node_majors():
    index = node_index(fixture_dir=Path("tests/fixtures"))
    for major in [24, 22, 20, 18, 16]:
        version = _latest_node_patch(index, major)
        assert version, f"Node major {major} not found in fixture"
