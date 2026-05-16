from __future__ import annotations

import gzip
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # pragma: no cover


class DiscoveryError(RuntimeError):
    """Raised when upstream metadata cannot be discovered or parsed."""


def load_json(path: Path) -> object:
    return json.loads(path.read_text())


def _load_json_fixture(fixture_dir: Path | None, name: str) -> object | None:
    if not fixture_dir:
        return None
    path = fixture_dir / name
    if not path.exists():
        return None
    return load_json(path)


def fetch_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": "codervps-catalog/0.1"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(_decode_response_bytes(response.read(), response.headers))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise DiscoveryError(f"failed to fetch JSON metadata from {url}: {exc}") from exc


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "codervps-catalog/0.1"})
    try:
        with urlopen(request, timeout=30) as response:
            return _decode_response_bytes(response.read(), response.headers)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise DiscoveryError(f"failed to fetch metadata from {url}: {exc}") from exc


def _decode_response_bytes(data: bytes, headers: object) -> str:
    encoding = ""
    if hasattr(headers, "get"):
        encoding = str(headers.get("Content-Encoding", ""))
    if encoding.lower() == "gzip" or data.startswith(b"\x1f\x8b"):
        data = gzip.decompress(data)
    return data.decode("utf-8")


def node_index(fixture_dir: Path | None = None) -> list[dict]:
    fixture = _load_json_fixture(fixture_dir, "node-index.json")
    if fixture is not None:
        return list(fixture)
    return list(fetch_json("https://nodejs.org/dist/index.json"))


def go_downloads(fixture_dir: Path | None = None) -> list[dict]:
    fixture = _load_json_fixture(fixture_dir, "go-dl.json")
    if fixture is not None:
        return list(fixture)
    return list(fetch_json("https://go.dev/dl/?mode=json&include=all"))


def go_linux_amd64_sha256(item: dict) -> str | None:
    version = str(item.get("version", "")).removeprefix("go")
    archive = f"go{version}.linux-amd64.tar.gz"
    for file_info in item.get("files", []):
        if file_info.get("filename") != archive:
            continue
        sha256 = str(file_info.get("sha256", ""))
        if re.fullmatch(r"[0-9a-f]{64}", sha256):
            return sha256
        return None
    return None


def latest_coder_base_tag(ubuntu: str, fixture_dir: Path | None = None) -> str:
    fixture = _load_json_fixture(fixture_dir, "base-tags.json")
    if fixture is None:
        fixture = fetch_json(
            "https://hub.docker.com/v2/repositories/"
            f"codercom/example-base/tags?page_size=100&name=ubuntu-{ubuntu}"
        )
    pattern = re.compile(rf"^ubuntu-{re.escape(ubuntu)}-(\d{{8}})$")
    tags = []
    for item in dict(fixture).get("results", []):
        name = str(item.get("name", ""))
        match = pattern.match(name)
        if match:
            tags.append((match.group(1), name))
    if not tags:
        raise DiscoveryError(f"no date-pinned codercom/example-base tag found for {ubuntu}")
    return max(tags)[1]


def _version_minor(version: str) -> str:
    match = re.match(r"^(\d+\.\d+)", version)
    if not match:
        raise DiscoveryError(f"cannot parse Python version: {version}")
    return match.group(1)


def _minor_tuple(value: str) -> tuple[int, int]:
    major, minor = value.split(".", 1)
    return int(major), int(minor)


def _python_download_rows(fixture_dir: Path | None) -> list[dict]:
    fixture = _load_json_fixture(fixture_dir, "python-downloads.json")
    if fixture is not None:
        return list(fixture)
    env = os.environ.copy()
    env.setdefault("UV_CACHE_DIR", ".uv-cache")
    try:
        result = subprocess.run(
            [
                "uv",
                "python",
                "list",
                "--only-downloads",
                "--all-versions",
                "--output-format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise DiscoveryError(f"failed to discover Python downloads with uv: {exc}") from exc
    return list(json.loads(result.stdout))


def python_versions(
    fixture_dir: Path | None = None,
    *,
    min_minor: str = "3.6",
    max_minor: str = "latest",
    default_minor: str = "3.13",
) -> list[dict]:
    rows = _python_download_rows(fixture_dir)
    minimum = _minor_tuple(min_minor)
    maximum = None if max_minor == "latest" else _minor_tuple(max_minor)
    newest_by_minor: dict[str, str] = {}
    for row in rows:
        if row.get("implementation") != "cpython":
            continue
        if row.get("os") != "linux" or row.get("arch") != "x86_64":
            continue
        if row.get("variant") != "default":
            continue
        version = str(row.get("version", ""))
        if re.search(r"[a-zA-Z]", version):
            continue
        minor = _version_minor(version)
        minor_key = _minor_tuple(minor)
        if minor_key < minimum:
            continue
        if maximum is not None and minor_key > maximum:
            continue
        if minor not in newest_by_minor:
            newest_by_minor[minor] = version

    discovered = []
    for minor in sorted(newest_by_minor, key=_minor_tuple, reverse=True):
        if minor == default_minor:
            status = "active"
        elif _minor_tuple(minor) >= (3, 11):
            status = "supported"
        else:
            status = "legacy"
        discovered.append({"version": minor, "status": status})
    return discovered


def _stable_rust_version(fixture_dir: Path | None) -> str:
    if fixture_dir and (fixture_dir / "rust-channel-stable.toml").exists():
        raw = (fixture_dir / "rust-channel-stable.toml").read_text()
    else:
        raw = _fetch_text("https://static.rust-lang.org/dist/channel-rust-stable.toml")
    parsed = tomllib.loads(raw)
    version = str(parsed.get("pkg", {}).get("rust", {}).get("version", ""))
    match = re.match(r"^1\.(\d+)\.\d+", version)
    if not match:
        raise DiscoveryError("failed to parse Rust stable channel version")
    return match.group(0)


def rust_channels(
    fixture_dir: Path | None = None,
    *,
    stable_minor_count: int = 30,
) -> list[dict]:
    stable_version = _stable_rust_version(fixture_dir)
    latest_minor = int(stable_version.split(".")[1])
    versions = [
        {"version": "stable", "status": "active"},
        {"version": "beta", "status": "prerelease"},
        {"version": "nightly", "status": "prerelease"},
    ]
    for minor in range(latest_minor, max(latest_minor - stable_minor_count, 0), -1):
        versions.append(
            {
                "version": f"1.{minor}",
                "status": "active" if minor == latest_minor else "supported",
            }
        )
    return versions


def _apt_llvm_html(fixture_dir: Path | None) -> str:
    if fixture_dir and (fixture_dir / "apt-llvm.html").exists():
        return (fixture_dir / "apt-llvm.html").read_text()
    return _fetch_text("https://apt.llvm.org/")


def cpp_llvm_versions(fixture_dir: Path | None = None, *, ubuntu: str = "noble") -> list[dict]:
    html = _apt_llvm_html(fixture_dir)
    suffix_versions = {int(value) for value in re.findall(rf"llvm-toolchain-{ubuntu}-(\d+)", html)}
    default_match = re.search(r"currently version (\d+)", html)
    snapshot = int(default_match.group(1)) if default_match else None
    all_versions = set(suffix_versions)
    if snapshot:
        all_versions.add(snapshot)
    if not all_versions:
        raise DiscoveryError(f"no LLVM versions found for Ubuntu {ubuntu}")

    highest_suffix = max(suffix_versions) if suffix_versions else None
    result = []
    for version in sorted(all_versions, reverse=True):
        if snapshot and version == snapshot and version not in suffix_versions:
            status = "snapshot"
        elif highest_suffix and version == highest_suffix:
            status = "active"
        else:
            status = "supported"
        result.append({"version": str(version), "status": status})
    return result


def _github_release(repo: str, fixture_dir: Path | None, fixture_name: str) -> dict:
    fixture = _load_json_fixture(fixture_dir, fixture_name)
    if fixture is not None:
        return dict(fixture)
    return dict(fetch_json(f"https://api.github.com/repos/{repo}/releases/latest"))


def _strip_v(value: str) -> str:
    return value[1:] if value.startswith("v") else value


def uv_version(fixture_dir: Path | None = None) -> str:
    release = _github_release("astral-sh/uv", fixture_dir, "uv-release.json")
    version = _strip_v(str(release.get("tag_name", "")))
    if not version:
        raise DiscoveryError("uv release metadata did not include tag_name")
    return version


def code_server_version(fixture_dir: Path | None = None) -> str:
    release = _github_release("coder/code-server", fixture_dir, "code-server-release.json")
    version = _strip_v(str(release.get("tag_name", "")))
    if not version:
        raise DiscoveryError("code-server release metadata did not include tag_name")
    return version


def _sccache_target_preferences(arch: str) -> tuple[str, ...]:
    if arch == "linux/amd64":
        return ("x86_64-unknown-linux-gnu", "x86_64-unknown-linux-musl")
    if arch == "linux/arm64":
        return ("aarch64-unknown-linux-gnu", "aarch64-unknown-linux-musl")
    raise DiscoveryError(f"unsupported sccache architecture: {arch}")


def sccache_release(
    fixture_dir: Path | None = None, *, arch: str = "linux/amd64"
) -> dict[str, str]:
    release = _github_release("mozilla/sccache", fixture_dir, "sccache-release.json")
    version = _strip_v(str(release.get("tag_name", "")))
    if not version:
        raise DiscoveryError("sccache release metadata did not include tag_name")

    assets_by_target: dict[str, dict] = {}
    pattern = re.compile(rf"^sccache-v{re.escape(version)}-(.+)\.tar\.gz$")
    for asset in release.get("assets", []):
        name = str(asset.get("name", ""))
        match = pattern.match(name)
        if not match:
            continue
        assets_by_target[match.group(1)] = asset

    for target in _sccache_target_preferences(arch):
        asset = assets_by_target.get(target)
        if not asset:
            continue
        digest = str(asset.get("digest", ""))
        sha256 = digest.removeprefix("sha256:")
        if not re.fullmatch(r"[0-9a-f]{64}", sha256):
            raise DiscoveryError(f"sccache asset {asset['name']} has no SHA256 digest")
        return {
            "version": version,
            "asset": str(asset["name"]),
            "sha256": sha256,
            "target": target,
        }

    raise DiscoveryError(f"no supported sccache Linux asset found for {arch}")


def sccache_version_and_sha256(
    fixture_dir: Path | None = None,
    *,
    arch: str = "linux/amd64",
) -> dict[str, str]:
    return sccache_release(fixture_dir, arch=arch)
