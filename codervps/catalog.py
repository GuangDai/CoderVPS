from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .config import load_toolchains_config
from .discovery import go_downloads, node_index
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
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "arch": cfg.project_arch,
        "base": {
            "source": "codercom/example-base",
            "ubuntu": "noble",
            "tag": "ubuntu-noble-20260511",
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
            "python": {"versions": [], "defaults": {"version": cfg.python_default}},
            "rust": {"versions": [], "defaults": {"toolchain": cfg.rust_default}},
            "go": {"versions": go_versions, "defaults": {"version": cfg.go_default}},
            "cpp": {"versions": [], "defaults": {"llvm": cfg.cpp_default_llvm}},
        },
        "tools": {
            "uv": {"version": cfg.overrides.get("uv") or "auto"},
            "code_server": {"version": cfg.overrides.get("code_server") or "auto"},
            "sccache": {
                "version": cfg.overrides.get("sccache") or "auto",
                "sha256": "resolved-sccache-release-sha256",
            },
            "llvm_prebundle": {"version": cfg.overrides.get("llvm_prebundle") or "auto"},
        },
    }


def refresh_catalog_from_path(config_path: str, fixture_dir: str | None = None) -> dict:
    cfg = load_toolchains_config(Path(config_path))
    fd = Path(fixture_dir) if fixture_dir else None
    return refresh_catalog(cfg, fixture_dir=fd)
