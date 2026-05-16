from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen


def load_json(path: Path) -> object:
    return json.loads(path.read_text())


def fetch_json(url: str) -> object:
    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def node_index(fixture_dir: Path | None = None) -> list[dict]:
    if fixture_dir:
        return list(load_json(fixture_dir / "node-index.json"))
    return list(fetch_json("https://nodejs.org/dist/index.json"))


def go_downloads(fixture_dir: Path | None = None) -> list[dict]:
    if fixture_dir:
        return list(load_json(fixture_dir / "go-dl.json"))
    return list(fetch_json("https://go.dev/dl/?mode=json&include=all"))


def python_versions(fixture_dir: Path | None = None) -> list[dict]:
    """Return list of available Python versions from uv python install --list or fixtures.

    # TODO: implement by querying uv python install --list
    # or github.com/astral-sh/python-build-standalone releases
    # Blocked by: need to parse uv python output format
    # Will be implemented: Task D (T13 Full Validation)
    """
    if fixture_dir and (fixture_dir / "python-versions.json").exists():
        return list(load_json(fixture_dir / "python-versions.json"))
    return []  # Will be populated when uv discovery is implemented


def rust_channels(fixture_dir: Path | None = None) -> list[dict]:
    """Return list of Rust channels from rustup or fixtures.

    # TODO: implement by querying https://static.rust-lang.org/dist/channel-rust-stable.toml
    # Blocked by: need to parse rustup channel manifest format
    # Will be implemented: Task D (T13 Full Validation)
    """
    if fixture_dir and (fixture_dir / "rust-channels.json").exists():
        return list(load_json(fixture_dir / "rust-channels.json"))
    # Return statically defined channels that are always valid
    return [
        {"version": "stable", "status": "active"},
        {"version": "beta", "status": "prerelease"},
        {"version": "nightly", "status": "prerelease"},
    ]


def cpp_llvm_versions(fixture_dir: Path | None = None) -> list[dict]:
    """Return list of LLVM versions from apt.llvm.org or fixtures.

    # TODO: implement by scraping apt.llvm.org for available versions
    # Blocked by: no apt repository metadata parser yet
    # Will be implemented: Task D (T13 Full Validation)
    """
    if fixture_dir and (fixture_dir / "llvm-versions.json").exists():
        return list(load_json(fixture_dir / "llvm-versions.json"))
    return []  # Will be populated when apt.llvm.org discovery is implemented


def uv_version(fixture_dir: Path | None = None) -> str:
    """Return the latest uv version or from fixtures.

    # TODO: implement by querying github.com/astral-sh/uv/releases API
    # Blocked by: GitHub API implementation not done
    # Will be implemented: Task D (T13 Full Validation)
    """
    if fixture_dir and (fixture_dir / "uv-version.json").exists():
        data = load_json(fixture_dir / "uv-version.json")
        return str(data.get("version", ""))
    return ""


def code_server_version(fixture_dir: Path | None = None) -> str:
    """Return the latest code-server version or from fixtures.

    # TODO: implement by querying github.com/coder/code-server/releases API
    # Blocked by: GitHub API implementation not done
    # Will be implemented: Task D (T13 Full Validation)
    """
    if fixture_dir and (fixture_dir / "code-server-version.json").exists():
        data = load_json(fixture_dir / "code-server-version.json")
        return str(data.get("version", ""))
    return ""


def sccache_version_and_sha256(fixture_dir: Path | None = None) -> dict[str, str]:
    """Return latest sccache version and sha256, or from fixtures.

    # TODO: implement by querying github.com/rust-lang/sccache/releases
    # Blocked by: GitHub API implementation not done
    # Will be implemented: Task D (T13 Full Validation)
    """
    if fixture_dir and (fixture_dir / "sccache-release.json").exists():
        data = load_json(fixture_dir / "sccache-release.json")
        return {"version": str(data.get("version", "")), "sha256": str(data.get("sha256", ""))}
    return {"version": "", "sha256": ""}
