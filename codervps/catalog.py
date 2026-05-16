from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .config import load_toolchains_config
from .discovery import (
    code_server_version,
    cpp_llvm_versions,
    go_downloads,
    go_linux_amd64_sha256,
    latest_coder_base_tag,
    node_index,
    python_versions,
    rust_channels,
    sccache_release,
    uv_version,
)
from .models import ToolchainsConfig


def _latest_node_patch(index: list[dict], major: int) -> str:
    prefix = f"v{major}."
    for entry in index:
        version = str(entry["version"])
        if version.startswith(prefix):
            return version.removeprefix("v")
    raise ValueError(f"missing Node major {major}")


def _node_status(major: int) -> str:
    if major >= 24:
        return "active_lts"
    if major >= 22:
        return "maintenance_lts"
    return "eol"


def refresh_catalog(cfg: ToolchainsConfig, fixture_dir: Path | None = None) -> dict:
    nodes = node_index(fixture_dir)
    go_data = go_downloads(fixture_dir)
    go_versions = []
    for item in go_data:
        ver = item["version"]
        v = ver.removeprefix("go")
        stable = item.get("stable", False)
        sha256 = go_linux_amd64_sha256(item)
        if not sha256:
            continue
        go_versions.append(
            {
                "version": v,
                "status": "active" if stable else "prerelease",
                "sha256": sha256,
            }
        )

    base_tag = latest_coder_base_tag("noble", fixture_dir)
    python_vers = python_versions(
        fixture_dir,
        min_minor=cfg.python_min_minor,
        max_minor=cfg.python_max_minor,
        default_minor=cfg.python_default,
    )
    rust_vers = rust_channels(
        fixture_dir,
        stable_minor_count=cfg.rust_stable_minor_count,
    )
    cpp_vers = cpp_llvm_versions(fixture_dir)

    selected_uv = cfg.overrides.get("uv") or uv_version(fixture_dir)
    selected_code_server = cfg.overrides.get("code_server") or code_server_version(fixture_dir)
    sccache_info = sccache_release(fixture_dir, arch=cfg.project_arch)
    selected_sccache = cfg.overrides.get("sccache") or sccache_info["version"]
    sccache_sha256 = sccache_info["sha256"]
    explicit_llvm = cfg.overrides.get("llvm_prebundle")
    selected_llvm = explicit_llvm or _default_llvm_prebundle(cpp_vers)
    default_go = _default_go_version(go_versions, cfg.go_default)
    default_cpp_llvm = selected_llvm if cfg.cpp_default_llvm == "latest" else cfg.cpp_default_llvm

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "arch": cfg.project_arch,
        "base": {
            "source": "codercom/example-base",
            "ubuntu": "noble",
            "tag": base_tag,
        },
        "node": {
            "majors": {
                str(major): {
                    "version": _latest_node_patch(nodes, major),
                    "status": _node_status(major),
                }
                for major in cfg.node_majors
            }
        },
        "plugins": {
            "python": {"versions": python_vers, "defaults": {"version": cfg.python_default}},
            "rust": {"versions": rust_vers, "defaults": {"toolchain": cfg.rust_default}},
            "go": {"versions": go_versions, "defaults": {"version": default_go}},
            "cpp": {"versions": cpp_vers, "defaults": {"llvm": default_cpp_llvm}},
        },
        "tools": {
            "uv": {"version": selected_uv},
            "code_server": {"version": selected_code_server},
            "sccache": {
                "version": selected_sccache,
                "asset": sccache_info["asset"],
                "target": sccache_info["target"],
                "sha256": sccache_sha256,
            },
            "llvm_prebundle": {"version": selected_llvm},
        },
    }


def refresh_catalog_from_path(config_path: str, fixture_dir: str | None = None) -> dict:
    cfg = load_toolchains_config(Path(config_path))
    fd = Path(fixture_dir) if fixture_dir else None
    return refresh_catalog(cfg, fixture_dir=fd)


def _default_llvm_prebundle(versions: list[dict]) -> str:
    for version in versions:
        if version.get("status") != "snapshot":
            return str(version["version"])
    if versions:
        return str(versions[0]["version"])
    raise ValueError("cannot choose LLVM prebundle version from empty discovery result")


def _default_go_version(versions: list[dict], configured_default: str) -> str:
    if configured_default != "latest":
        return configured_default
    for version in versions:
        if version.get("status") == "active":
            return str(version["version"])
    if versions:
        return str(versions[0]["version"])
    raise ValueError("cannot choose Go default version from empty discovery result")
