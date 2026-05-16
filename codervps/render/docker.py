"""Render Docker build matrix and image tag metadata.

Generates one matrix entry per Node.js major version, with deterministic GHCR
tags and Docker build arguments mapped from the toolchain catalog.
"""

from __future__ import annotations

import json
import re


def _validated_optional(value: object, field_name: str) -> str:
    """Return an optional build arg value, rejecting placeholder strings."""
    if value is None:
        return ""
    text = str(value)
    if text in {"auto", "placeholder", "TBD"} or text.startswith("resolved-"):
        raise ValueError(f"{field_name} contains forbidden placeholder value: {text}")
    return text


def _tag_from_base(base_tag: str) -> str:
    match = re.fullmatch(r"ubuntu-([a-z]+)-(\d{8})", base_tag)
    if not match:
        raise ValueError(f"base tag must be date-pinned ubuntu-<codename>-YYYYMMDD: {base_tag}")
    codename, date = match.groups()
    return f"{codename}-{date}"


def build_matrix(catalog: dict, image_repo: str) -> list[dict]:
    """Build the Docker image build matrix from a catalog.

    Each entry contains all build-args needed by docker/Dockerfile:
    tag, image, base_image, node_major, node_version, uv_version,
    code_server_version, sccache_version, sccache_sha256, llvm_version.

    Node majors are sorted descending (24, 22, 20, 18, 16). Tags follow
    the pattern noble-YYYYMMDD-nodeMAJOR.
    """
    base = catalog.get("base", {})
    base_tag = base.get("tag", "")
    base_source = base.get("source", "codercom/example-base")
    node_majors = catalog.get("node", {}).get("majors", {})
    tools = catalog.get("tools", {})

    # Sort node majors descending
    sorted_majors = sorted(node_majors.keys(), key=lambda k: int(k), reverse=True)

    matrix: list[dict] = []
    for major_str in sorted_majors:
        major_int = int(major_str)
        node_info = node_majors[major_str]
        node_version = node_info.get("version", "")

        tag = f"{_tag_from_base(base_tag)}-node{major_str}"

        entry: dict = {
            "tag": tag,
            "image": f"{image_repo}:{tag}",
            "base_image": f"{base_source}:{base_tag}",
            "node_major": major_int,
            "node_version": node_version,
            "uv_version": _validated_optional(tools.get("uv", {}).get("version", ""), "uv.version"),
            "code_server_version": _validated_optional(
                tools.get("code_server", {}).get("version", ""),
                "code_server.version",
            ),
            "sccache_version": _validated_optional(
                tools.get("sccache", {}).get("version", ""),
                "sccache.version",
            ),
            "sccache_asset": _validated_optional(
                tools.get("sccache", {}).get("asset", ""),
                "sccache.asset",
            ),
            "sccache_sha256": _validated_optional(
                tools.get("sccache", {}).get("sha256", ""),
                "sccache.sha256",
            ),
            "llvm_version": _validated_optional(
                tools.get("llvm_prebundle", {}).get("version", ""),
                "llvm_prebundle.version",
            ),
        }
        matrix.append(entry)

    return matrix


def format_matrix_output(matrix: list[dict], fmt: str = "json") -> str:
    """Format the build matrix for output.

    Args:
        matrix: List of matrix entries from build_matrix().
        fmt: "json" for plain JSON list, or "github-output" for GITHUB_OUTPUT format
             (matrix=<json>).

    Returns:
        String ready for stdout or GITHUB_OUTPUT redirect.
    """
    json_str = json.dumps(matrix, sort_keys=True) + "\n"
    if fmt == "github-output":
        return f"matrix={json_str}"
    return json_str
