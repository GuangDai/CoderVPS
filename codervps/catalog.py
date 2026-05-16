from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .config import load_toolchains_config
from .discovery import (
    code_server_version,
    cpp_llvm_versions,
    go_downloads,
    node_index,
    python_versions,
    rust_channels,
    sccache_version_and_sha256,
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
        files = item.get("files", [])
        sha256 = ""
        for f in files:
            if "linux-amd64.tar.gz" in f.get("filename", ""):
                sha256 = f.get("sha256", "")
                break
        go_versions.append(
            {
                "version": v,
                "status": "active" if stable else "prerelease",
                "sha256": sha256,
            }
        )

    # Discovered or fixture-backed values (empty until real discovery is implemented)
    # TODO: resolve base tag from Docker Hub API (codercom/example-base tags endpoint)
    # The date tag "ubuntu-noble-20260511" is a hardcoded example that must be
    # dynamically resolved in production.
    # Blocked by: no Docker Hub registry client implemented yet
    # Will be implemented: Task D (T13 Full Validation)
    base_tag = "ubuntu-noble-20260511"

    # Python versions from uv python install --list discovery
    python_vers = python_versions(fixture_dir)
    # TODO: populate python versions from uv python install --list
    # Blocked by: uv python output parser not yet implemented
    # Will be implemented: Task D (T13 Full Validation)

    # Rust channels from rustup/dist-server metadata
    rust_vers = rust_channels(fixture_dir)
    # TODO: populate stable minor versions from rustup channel manifest
    # Blocked by: rustup metadata parser not yet implemented
    # Will be implemented: Task D (T13 Full Validation)

    # C++ LLVM versions from apt.llvm.org
    cpp_vers = cpp_llvm_versions(fixture_dir)
    # TODO: populate LLVM versions from apt.llvm.org repo metadata
    # Blocked by: apt repository metadata parser not yet implemented
    # Will be implemented: Task D (T13 Full Validation)

    # Tool versions from discovery (empty until real APIs are implemented)
    resolved_uv = cfg.overrides.get("uv") or uv_version(fixture_dir)
    # TODO: resolve uv version from github.com/astral-sh/uv/releases
    # Blocked by: GitHub API client not yet implemented
    # Will be implemented: Task D (T13 Full Validation)

    resolved_code_server = cfg.overrides.get("code_server") or code_server_version(fixture_dir)
    # TODO: resolve code-server version from github.com/coder/code-server/releases
    # Blocked by: GitHub API client not yet implemented
    # Will be implemented: Task D (T13 Full Validation)

    sccache_info = sccache_version_and_sha256(fixture_dir)
    resolved_sccache = cfg.overrides.get("sccache") or sccache_info["version"]
    resolved_sccache_sha256 = sccache_info["sha256"]
    # TODO: resolve sccache version and SHA256 from github.com/rust-lang/sccache/releases
    # Blocked by: GitHub API client not yet implemented
    # Will be implemented: Task D (T13 Full Validation)

    resolved_llvm = cfg.overrides.get("llvm_prebundle") or ""
    # TODO: resolve LLVM prebundle version from apt.llvm.org
    # Blocked by: apt repo metadata parser not yet implemented
    # Will be implemented: Task D (T13 Full Validation)

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
            "go": {"versions": go_versions, "defaults": {"version": cfg.go_default}},
            "cpp": {"versions": cpp_vers, "defaults": {"llvm": cfg.cpp_default_llvm}},
        },
        "tools": {
            "uv": {"version": resolved_uv},
            "code_server": {"version": resolved_code_server},
            "sccache": {
                "version": resolved_sccache,
                "sha256": resolved_sccache_sha256,
            },
            "llvm_prebundle": {"version": resolved_llvm},
        },
    }


def refresh_catalog_from_path(config_path: str, fixture_dir: str | None = None) -> dict:
    cfg = load_toolchains_config(Path(config_path))
    fd = Path(fixture_dir) if fixture_dir else None
    return refresh_catalog(cfg, fixture_dir=fd)
