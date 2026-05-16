"""Tests for codervps.render.docker -- build matrix and format output."""

from __future__ import annotations

import json

import pytest

from codervps.render.docker import build_matrix, format_matrix_output


# ---- Framework tests (Phase 1) ----


def test_module_exists():
    """Framework: build_matrix and format_matrix_output are importable."""
    assert callable(build_matrix)
    assert callable(format_matrix_output)


# ---- Detailed tests (Phase 3) ----


def test_build_matrix_has_five_node_images():
    catalog = {
        "base": {"ubuntu": "noble", "tag": "ubuntu-noble-20260511"},
        "node": {
            "majors": {
                "24": {"version": "24.11.1"},
                "22": {"version": "22.21.0"},
                "20": {"version": "20.19.5"},
                "18": {"version": "18.20.8"},
                "16": {"version": "16.20.2"},
            }
        },
    }
    matrix = build_matrix(catalog, "ghcr.io/guangdai/codervps-devbox")
    assert [item["node_major"] for item in matrix] == [24, 22, 20, 18, 16]
    assert matrix[0]["tag"] == "noble-20260511-node24"
    assert matrix[0]["image"] == "ghcr.io/guangdai/codervps-devbox:noble-20260511-node24"
    assert matrix[0]["base_image"].endswith(":ubuntu-noble-20260511")
    assert "sccache_sha256" in matrix[0]


def test_build_matrix_all_keys_present():
    catalog = {
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"24": {"version": "24.11.1"}}},
    }
    matrix = build_matrix(catalog, "ghcr.io/test/image")
    entry = matrix[0]
    required_keys = {
        "tag",
        "image",
        "base_image",
        "node_major",
        "node_version",
        "uv_version",
        "code_server_version",
        "sccache_version",
        "sccache_asset",
        "sccache_sha256",
        "llvm_version",
    }
    assert set(entry.keys()) == required_keys, f"Missing keys: {required_keys - set(entry.keys())}"


def test_build_matrix_node_major_is_int():
    catalog = {
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"24": {"version": "24.11.1"}}},
    }
    matrix = build_matrix(catalog, "ghcr.io/test/image")
    assert isinstance(matrix[0]["node_major"], int)
    assert matrix[0]["node_major"] == 24


def test_build_matrix_sorted_descending():
    catalog = {
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {
            "majors": {
                "18": {"version": "18.0.0"},
                "24": {"version": "24.0.0"},
                "22": {"version": "22.0.0"},
            }
        },
    }
    matrix = build_matrix(catalog, "ghcr.io/test/image")
    majors = [e["node_major"] for e in matrix]
    assert majors == [24, 22, 18]


def test_build_matrix_empty_majors():
    catalog = {"base": {"tag": "ubuntu-noble-20260511"}, "node": {"majors": {}}}
    matrix = build_matrix(catalog, "ghcr.io/test/image")
    assert matrix == []


def test_build_matrix_no_node_key():
    matrix = build_matrix({"base": {"tag": "ubuntu-noble-20260511"}}, "ghcr.io/test/image")
    assert matrix == []


def test_build_matrix_tool_values_from_catalog():
    catalog = {
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"24": {"version": "24.11.1"}}},
        "tools": {
            "uv": {"version": "0.6.0"},
            "code_server": {"version": "4.99.0"},
            "sccache": {
                "version": "0.15.0",
                "asset": "sccache-v0.15.0-x86_64-unknown-linux-musl.tar.gz",
                "sha256": "a" * 64,
            },
            "llvm_prebundle": {"version": "19"},
        },
    }
    matrix = build_matrix(catalog, "ghcr.io/test/image")
    entry = matrix[0]
    assert entry["uv_version"] == "0.6.0"
    assert entry["code_server_version"] == "4.99.0"
    assert entry["sccache_version"] == "0.15.0"
    assert entry["sccache_asset"] == "sccache-v0.15.0-x86_64-unknown-linux-musl.tar.gz"
    assert entry["sccache_sha256"] == "a" * 64
    assert entry["llvm_version"] == "19"


def test_build_matrix_defaults_empty_strings():
    """When tools are missing from catalog, values default to empty string."""
    catalog = {
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"24": {"version": "24.11.1"}}},
    }
    matrix = build_matrix(catalog, "ghcr.io/test/image")
    entry = matrix[0]
    assert entry["uv_version"] == ""
    assert entry["sccache_asset"] == ""
    assert entry["sccache_sha256"] == ""


def test_build_matrix_no_auto_strings():
    """Placeholder strings fail validation instead of being emitted."""
    catalog = {
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"24": {"version": "24.11.1"}}},
        "tools": {"uv": {"version": "auto"}, "sccache": {"sha256": "auto"}},
    }
    with pytest.raises(ValueError, match="placeholder"):
        build_matrix(catalog, "ghcr.io/test/image")


def test_build_matrix_no_resolved_placeholders():
    """No 'resolved-' prefix strings anywhere."""
    catalog = {
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"24": {"version": "24.11.1"}}},
    }
    matrix = build_matrix(catalog, "ghcr.io/test/image")
    text = json.dumps(matrix, sort_keys=True)
    assert "resolved-" not in text


def test_build_matrix_sccache_sha256_64_hex_chars():
    """When populated, sccache_sha256 should be 64 hex chars."""
    catalog = {
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"24": {"version": "24.11.1"}}},
        "tools": {"sccache": {"sha256": "a" * 64}},
    }
    matrix = build_matrix(catalog, "ghcr.io/test/image")
    sha = matrix[0]["sccache_sha256"]
    assert len(sha) == 64
    assert all(c in "0123456789abcdef" for c in sha)


def test_format_matrix_output_json():
    matrix = [
        {
            "tag": "noble-20260511-node24",
            "image": "ghcr.io/test:noble-20260511-node24",
            "base_image": "codercom/example-base:ubuntu-noble-20260511",
            "node_major": 24,
            "node_version": "24.11.1",
            "uv_version": "",
            "code_server_version": "",
            "sccache_version": "",
            "sccache_asset": "",
            "sccache_sha256": "",
            "llvm_version": "",
        }
    ]
    output = format_matrix_output(matrix, fmt="json")
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["node_major"] == 24


def test_format_matrix_output_github():
    matrix = [
        {
            "tag": "noble-20260511-node24",
            "image": "ghcr.io/test:noble-20260511-node24",
            "base_image": "codercom/example-base:ubuntu-noble-20260511",
            "node_major": 24,
            "node_version": "24.11.1",
            "uv_version": "",
            "code_server_version": "",
            "sccache_version": "",
            "sccache_asset": "",
            "sccache_sha256": "",
            "llvm_version": "",
        }
    ]
    output = format_matrix_output(matrix, fmt="github-output")
    assert output.startswith("matrix=")
    # The value after "matrix=" must be valid JSON
    json_str = output.removeprefix("matrix=")
    parsed = json.loads(json_str)
    assert isinstance(parsed, list)


def test_format_matrix_output_github_multiple():
    matrix = [
        {"node_major": 24, "image": "ghcr.io/test:24"},
        {"node_major": 22, "image": "ghcr.io/test:22"},
    ]
    output = format_matrix_output(matrix, fmt="github-output")
    assert output.startswith("matrix=")
    json_str = output.removeprefix("matrix=")
    parsed = json.loads(json_str)
    assert len(parsed) == 2


def test_format_matrix_output_defaults_to_json():
    matrix = [{"node_major": 24}]
    output = format_matrix_output(matrix)
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert parsed[0]["node_major"] == 24


def test_format_matrix_empty():
    output = format_matrix_output([])
    assert json.loads(output) == []


def test_build_matrix_tag_format():
    """Tag should be noble-YYYYMMDD-nodeMAJOR."""
    catalog = {
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"22": {"version": "22.21.0"}}},
    }
    matrix = build_matrix(catalog, "ghcr.io/test")
    assert matrix[0]["tag"] == "noble-20260511-node22"


def test_format_matrix_output_trailing_newline_json():
    matrix = [{"node_major": 24}]
    output = format_matrix_output(matrix)
    assert output.endswith("\n")


def test_format_matrix_output_trailing_newline_github():
    matrix = [{"node_major": 24}]
    output = format_matrix_output(matrix, fmt="github-output")
    assert output.endswith("\n")


def test_build_matrix_rejects_placeholder_tool_values():
    catalog = {
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"24": {"version": "24.11.1"}}},
        "tools": {"uv": {"version": "auto"}},
    }
    try:
        build_matrix(catalog, "ghcr.io/test/image")
    except ValueError as exc:
        assert "placeholder" in str(exc)
    else:
        raise AssertionError("placeholder tool values must fail validation")


def test_dockerfile_uses_discovered_sccache_asset_arg():
    from pathlib import Path

    text = Path("docker/Dockerfile").read_text()
    assert "ARG SCCACHE_ASSET" in text
    assert 'file="${SCCACHE_ASSET}"' in text
    assert "x86_64-unknown-linux-musl" not in text


def test_dockerfile_uses_coder_home_as_default_workspace_root():
    from pathlib import Path

    text = Path("docker/Dockerfile").read_text()
    assert "/home/coder/workspace" in text
    assert "WORKDIR /home/coder" in text
    assert "mkdir -p /workspace" not in text
    assert "WORKDIR /workspace" not in text


def test_build_matrix_uses_configured_image_repo():
    catalog = {
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"24": {"version": "24.11.1"}}},
    }
    matrix = build_matrix(catalog, "ghcr.io/my-org/my-repo")
    assert matrix[0]["image"].startswith("ghcr.io/my-org/my-repo:")


def test_build_matrix_base_image_uses_source():
    catalog = {
        "base": {"source": "docker.io/library/ubuntu", "tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"24": {"version": "24.0.0"}}},
    }
    matrix = build_matrix(catalog, "ghcr.io/test/image")
    assert matrix[0]["base_image"] == "docker.io/library/ubuntu:ubuntu-noble-20260511"
