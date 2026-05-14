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
