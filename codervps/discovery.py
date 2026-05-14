from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

_USER_AGENT = "codervps/0.1.0"


def load_json(path: Path) -> object:
    """Read and parse a JSON file."""
    return json.loads(path.read_text())


def fetch_json(url: str) -> object:
    """Fetch JSON from a URL with a user-agent header."""
    req = Request(url, headers={"User-Agent": _USER_AGENT})
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def node_index(fixture_dir: Path | None = None) -> list[dict]:
    """Return Node.js version index.

    When *fixture_dir* is given, reads ``node-index.json`` from that
    directory instead of fetching from nodejs.org.
    """
    if fixture_dir is not None:
        raw = load_json(fixture_dir / "node-index.json")
        if not isinstance(raw, list):
            raise ValueError("node-index.json must be a JSON array")
        return list(raw)
    raw = fetch_json("https://nodejs.org/dist/index.json")
    if not isinstance(raw, list):
        raise ValueError("unexpected nodejs.org response: expected array")
    return list(raw)


def go_downloads(fixture_dir: Path | None = None) -> list[dict]:
    """Return Go download metadata.

    When *fixture_dir* is given, reads ``go-dl.json`` from that directory
    instead of fetching from go.dev.
    """
    if fixture_dir is not None:
        raw = load_json(fixture_dir / "go-dl.json")
        if not isinstance(raw, list):
            raise ValueError("go-dl.json must be a JSON array")
        return list(raw)
    raw = fetch_json("https://go.dev/dl/?mode=json&include=all")
    if not isinstance(raw, list):
        raise ValueError("unexpected go.dev response: expected array")
    return list(raw)


__all__ = ["fetch_json", "go_downloads", "load_json", "node_index"]
