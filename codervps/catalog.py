from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .discovery import go_downloads, node_index
from .models import ToolchainsConfig


def _latest_node_patch(index: list[dict], major: int) -> str:
    """Find the latest patch version for a given Node.js major from the index."""
    prefix = f"v{major}."
    for entry in index:
        version = str(entry.get("version", ""))
        if version.startswith(prefix):
            return version.removeprefix("v")
    raise ValueError(f"no Node version found for major {major}")


def _node_status(major: int) -> str:
    """Return a simplified status label for a Node.js major."""
    if major >= 24:
        return "active_lts"
    if major >= 22:
        return "maintenance_lts"
    return "eol"


def _resolve_go_versions(downloads: list[dict], minor_count: int) -> list[dict[str, str]]:
    """Extract the latest N stable Go minor versions from download metadata."""
    seen_series: set[str] = set()
    resolved: list[dict[str, str]] = []

    for entry in downloads:
        if not entry.get("stable", False):
            continue
        version = str(entry.get("version", ""))
        if not version.startswith("go"):
            continue
        # version looks like "go1.22.12"
        core = version[2:]  # "1.22.12"
        parts = core.split(".")
        if len(parts) < 3:
            continue
        series = f"{parts[0]}.{parts[1]}"  # "1.22"
        if series in seen_series:
            continue
        seen_series.add(series)

        # Extract sha256 from the linux-amd64 file
        sha256 = ""
        for f in entry.get("files", []):
            if "linux-amd64" in str(f.get("filename", "")):
                sha256 = str(f.get("sha256", ""))
                break

        resolved.append({"version": core, "sha256": sha256, "series": series})

        if len(resolved) >= minor_count:
            break

    return resolved


def refresh_catalog(
    cfg: ToolchainsConfig,
    *,
    fixture_dir: Path | None = None,
) -> dict:
    """Build a full toolchain catalog from upstream metadata.

    When *fixture_dir* is supplied, upstream HTTP calls are replaced with
    local fixture reads so tests are deterministic.
    """
    nodes = node_index(fixture_dir)
    go_dl = go_downloads(fixture_dir)

    go_resolved = _resolve_go_versions(go_dl, cfg.go_minor_count)

    node_majors_catalog: dict[str, dict[str, str]] = {}
    for major in cfg.node_majors:
        try:
            patch = _latest_node_patch(nodes, major)
        except ValueError:
            continue
        node_majors_catalog[str(major)] = {
            "version": patch,
            "status": _node_status(major),
        }

    go_versions: list[dict[str, object]] = []
    for g in go_resolved:
        go_versions.append(
            {
                "value": g["series"],
                "label": f"Go {g['series']} ({g['version']})",
                "status": "supported",
                "metadata": {"patch": g["version"], "sha256": g["sha256"]},
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
        "node": {"majors": node_majors_catalog},
        "plugins": {
            "python": {
                "versions": [],
                "defaults": {"version": cfg.python_default},
            },
            "rust": {
                "versions": [],
                "defaults": {"toolchain": cfg.rust_default},
            },
            "go": {
                "versions": go_versions,
                "defaults": {
                    "version": cfg.go_default,
                    "tools": cfg.go_default_tools,
                },
            },
            "cpp": {
                "versions": [],
                "defaults": {"llvm": cfg.cpp_default_llvm},
            },
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


__all__ = ["refresh_catalog"]
