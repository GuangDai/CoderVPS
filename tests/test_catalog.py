"""Tests for codervps.catalog -- refresh_catalog and upstream metadata resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from codervps.catalog import _latest_node_patch, _node_status, _resolve_go_versions, refresh_catalog
from codervps.config import load_toolchains_config
from codervps.discovery import go_downloads, node_index


# ============================================================================
# Helper: _latest_node_patch
# ============================================================================


def test_latest_node_patch_finds_correct_version():
    index = [
        {"version": "v24.11.1"},
        {"version": "v24.10.0"},
        {"version": "v22.21.0"},
    ]
    assert _latest_node_patch(index, 24) == "24.11.1"
    assert _latest_node_patch(index, 22) == "22.21.0"


def test_latest_node_patch_missing_major():
    index = [{"version": "v22.21.0"}]
    with pytest.raises(ValueError, match="no Node version found"):
        _latest_node_patch(index, 24)


def test_latest_node_patch_skips_prerelease():
    index = [
        {"version": "v24.11.1"},
        {"version": "v24.12.0-rc1"},
    ]
    assert _latest_node_patch(index, 24) == "24.11.1"


# ============================================================================
# Helper: _node_status
# ============================================================================


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


# ============================================================================
# Helper: _resolve_go_versions
# ============================================================================


def test_resolve_go_versions_from_fixtures():
    dl = go_downloads(Path("tests/fixtures"))
    resolved = _resolve_go_versions(dl, 20)
    assert len(resolved) >= 4
    for entry in resolved:
        assert "version" in entry
        assert "sha256" in entry
        assert "series" in entry
        # sha256 must not be empty for linux-amd64 entries
        assert entry["sha256"] != ""


def test_resolve_go_versions_uses_linux_amd64_sha():
    dl = go_downloads(Path("tests/fixtures"))
    resolved = _resolve_go_versions(dl, 20)
    for entry in resolved:
        assert entry["sha256"].startswith("sha-go-linux-amd64-")


def test_resolve_go_versions_limited_count():
    dl = go_downloads(Path("tests/fixtures"))
    resolved = _resolve_go_versions(dl, 2)
    assert len(resolved) == 2


def test_resolve_go_versions_sorted_by_latest():
    dl = go_downloads(Path("tests/fixtures"))
    resolved = _resolve_go_versions(dl, 20)
    # First entry should be the highest stable minor
    first = resolved[0]["series"]
    all_series = [r["series"] for r in resolved]
    assert first == max(all_series, key=lambda s: tuple(int(x) for x in s.split(".")))


def test_resolve_go_versions_skips_duplicate_series():
    """When two patch releases exist for the same minor, only the first (latest) is kept."""
    dl = [
        {
            "version": "go1.22.14",
            "stable": True,
            "files": [{"filename": "go1.22.14.linux-amd64.tar.gz", "sha256": "aa"}],
        },
        {
            "version": "go1.22.12",
            "stable": True,
            "files": [{"filename": "go1.22.12.linux-amd64.tar.gz", "sha256": "bb"}],
        },
    ]
    resolved = _resolve_go_versions(dl, 20)
    assert len(resolved) == 1
    assert resolved[0]["version"] == "1.22.14"
    assert resolved[0]["sha256"] == "aa"


def test_resolve_go_versions_excludes_unstable():
    dl = [
        {
            "version": "go1.25.3",
            "stable": True,
            "files": [{"filename": "go1.25.3.linux-amd64.tar.gz", "sha256": "aa"}],
        },
        {
            "version": "go1.26.0-rc1",
            "stable": False,
            "files": [{"filename": "go1.26.0-rc1.linux-amd64.tar.gz", "sha256": "bb"}],
        },
    ]
    resolved = _resolve_go_versions(dl, 20)
    assert all(r["series"] != "1.26" for r in resolved)


# ============================================================================
# refresh_catalog integration tests
# ============================================================================


def test_refresh_catalog_from_fixtures():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    assert catalog["schema_version"] == 1
    assert catalog["arch"] == "linux/amd64"
    assert "generated_at" in catalog


def test_refresh_catalog_node_majors_from_fixtures():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    majors = catalog["node"]["majors"]
    assert sorted(majors.keys(), key=int) == ["16", "18", "20", "22", "24"]


def test_refresh_catalog_node_versions_resolved():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    node_24 = catalog["node"]["majors"]["24"]
    assert node_24["version"] == "24.11.1"
    assert node_24["status"] == "active_lts"


def test_refresh_catalog_go_versions_resolved():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    go_plugins = catalog["plugins"]["go"]
    assert len(go_plugins["versions"]) > 0
    assert go_plugins["defaults"]["version"] == "latest"


def test_refresh_catalog_plugins_present():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    for pid in ["python", "rust", "go", "cpp"]:
        assert pid in catalog["plugins"], f"missing plugin: {pid}"


def test_refresh_catalog_tools_present():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    for tool in ["uv", "code_server", "sccache", "llvm_prebundle"]:
        assert tool in catalog["tools"], f"missing tool: {tool}"


def test_refresh_catalog_base_info():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    assert catalog["base"]["source"] == "codercom/example-base"
    assert catalog["base"]["ubuntu"] == "noble"


def test_refresh_catalog_go_versions_include_sha256():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    for v in catalog["plugins"]["go"]["versions"]:
        assert "sha256" in v.get("metadata", {}), f"missing sha256 for {v['value']}"
        assert v["metadata"]["sha256"] != ""


# ============================================================================
# node_index and go_downloads fixtures
# ============================================================================


def test_node_index_fixture_loads():
    data = node_index(Path("tests/fixtures"))
    assert len(data) >= 5
    assert isinstance(data, list)
    assert all(isinstance(e, dict) for e in data)


def test_node_index_fixture_has_versions():
    data = node_index(Path("tests/fixtures"))
    versions = [e["version"] for e in data]
    assert "v24.11.1" in versions
    assert "v22.21.0" in versions


def test_go_downloads_fixture_loads():
    data = go_downloads(Path("tests/fixtures"))
    assert len(data) >= 4
    assert isinstance(data, list)
    assert all(isinstance(e, dict) for e in data)


def test_go_downloads_fixture_has_supported_versions():
    data = go_downloads(Path("tests/fixtures"))
    versions = [e["version"] for e in data]
    assert "go1.22.12" in versions
    assert all(e.get("stable") for e in data[:4])


# ============================================================================
# Edge cases
# ============================================================================


def test_refresh_catalog_empty_enabled_plugins(tmp_path):
    """Catalog should work even with empty enabled plugins list."""
    from codervps.catalog import refresh_catalog as rc
    from codervps.models import ToolchainsConfig

    cfg = ToolchainsConfig(
        project_arch="linux/amd64",
        node_majors=[24],
        enabled_plugins=[],
        overrides={},
        python_min_minor="3.6",
        python_max_minor="latest",
        python_default="3.13",
        python_default_tools=["ruff"],
        rust_stable_minor_count=30,
        rust_default="stable",
        rust_components=["rustfmt"],
        rust_use_sccache=True,
        go_minor_count=20,
        go_default="latest",
        go_default_tools=["gopls"],
        cpp_default_llvm="latest",
        cpp_prebundle="latest",
        cpp_default_tools=["xmake"],
    )
    catalog = rc(cfg, fixture_dir=Path("tests/fixtures"))
    assert catalog["schema_version"] == 1


def test_refresh_catalog_overrides_flow_to_tools():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    # overrides default to empty strings => "auto"
    assert catalog["tools"]["uv"]["version"] == "auto"
    assert catalog["tools"]["code_server"]["version"] == "auto"
