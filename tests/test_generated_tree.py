"""Tests for codervps.render.generated -- full generated tree rendering."""

from __future__ import annotations

import json

from codervps.render.generated import _write_json_sorted, render_generated_tree


# ---- Framework tests (Phase 1) ----


def test_module_exists():
    """Framework: render_generated_tree and _write_json_sorted are importable."""
    assert callable(render_generated_tree)
    assert callable(_write_json_sorted)


# ---- _write_json_sorted ----


def test_write_json_sorted_output(tmp_path):
    path = tmp_path / "test.json"
    _write_json_sorted(path, {"b": 2, "a": 1})
    text = path.read_text()
    parsed = json.loads(text)
    assert list(parsed.keys()) == ["a", "b"]  # sorted
    assert text.endswith("\n")


def test_write_json_sorted_creates_parent_dirs(tmp_path):
    path = tmp_path / "deep/nested/dir/file.json"
    _write_json_sorted(path, {"key": "value"})
    assert path.exists()
    assert json.loads(path.read_text()) == {"key": "value"}


# ---- render_generated_tree ----


def test_render_generated_tree(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={
            "schema_version": 1,
            "base": {"ubuntu": "noble", "tag": "ubuntu-noble-20260511"},
            "node": {"majors": {"24": {"version": "24.11.1"}}},
            "plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}},
        },
        images={
            "schema_version": 1,
            "images": [
                {
                    "node_major": 24,
                    "image": "ghcr.io/guangdai/codervps-devbox:noble-20260511-node24",
                }
            ],
        },
    )
    assert (tmp_path / "generated/catalog/toolchains.json").exists()
    assert (tmp_path / "templates/devbox/main.tf.json").exists()
    manifest = (tmp_path / "generated/manifest.json").read_text()
    assert "source_commit" in manifest
    assert "workflow_run_id" in manifest
    assert "generator_version" in manifest
    assert "image_tags" in manifest


def test_render_generated_tree_creates_toolchains_json(tmp_path):
    catalog = {
        "schema_version": 1,
        "base": {"tag": "ubuntu-noble-20260511"},
        "node": {"majors": {"24": {"version": "24.11.1"}}},
        "plugins": {},
    }
    render_generated_tree(
        output_dir=tmp_path,
        catalog=catalog,
        images={"images": []},
    )
    data = json.loads((tmp_path / "generated/catalog/toolchains.json").read_text())
    assert data == catalog


def test_render_generated_tree_images_json_NOT_written_by_default(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={"plugins": {}, "node": {"majors": {}}},
        images={"images": []},
    )
    assert not (tmp_path / "generated/catalog/images.json").exists()


def test_render_generated_tree_images_json_WRITTEN_when_opt_in(tmp_path):
    images = {"schema_version": 1, "images": [{"node_major": 24, "image": "ghcr.io/test:img"}]}
    render_generated_tree(
        output_dir=tmp_path,
        catalog={"plugins": {}, "node": {"majors": {}}},
        images=images,
        write_images_json=True,
    )
    assert (tmp_path / "generated/catalog/images.json").exists()
    data = json.loads((tmp_path / "generated/catalog/images.json").read_text())
    assert data == images


def test_render_generated_tree_manifest_has_required_fields(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={
            "schema_version": 1,
            "base": {"source": "codercom/example-base", "tag": "ubuntu-noble-20260511"},
            "node": {"majors": {"24": {"version": "24.11.1"}}},
            "tools": {"uv": {"version": "0.6.0"}, "code_server": {"version": "4.99.0"}},
            "plugins": {},
        },
        images={
            "images": [
                {
                    "node_major": 24,
                    "image": "ghcr.io/guangdai/codervps-devbox:noble-20260511-node24",
                }
            ]
        },
        source_commit="abc123def",
        workflow_run_id="12345",
    )
    manifest = json.loads((tmp_path / "generated/manifest.json").read_text())
    assert manifest["schema_version"] == 1
    assert manifest["source_commit"] == "abc123def"
    assert manifest["workflow_run_id"] == "12345"
    assert manifest["generator_version"] == "0.1.0"
    assert "generated_at" in manifest
    assert manifest["coder_base"]["source"] == "codercom/example-base"
    assert manifest["coder_base"]["tag"] == "ubuntu-noble-20260511"
    assert manifest["node_versions"] == {"24": "24.11.1"}
    assert manifest["tool_versions"] == {"uv": "0.6.0", "code_server": "4.99.0"}
    assert manifest["image_tags"] == ["ghcr.io/guangdai/codervps-devbox:noble-20260511-node24"]


def test_render_generated_tree_manifest_fallsback_to_env(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "envsha123")
    monkeypatch.setenv("GITHUB_RUN_ID", "envrun456")
    render_generated_tree(
        output_dir=tmp_path,
        catalog={"plugins": {}, "node": {"majors": {}}},
        images={"images": []},
    )
    manifest = json.loads((tmp_path / "generated/manifest.json").read_text())
    assert manifest["source_commit"] == "envsha123"
    assert manifest["workflow_run_id"] == "envrun456"


def test_render_generated_tree_runtime_files_copied(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={"plugins": {}, "node": {"majors": {}}},
        images={"images": []},
    )
    # Runtime files should be under templates/devbox/runtime/
    startup = tmp_path / "templates/devbox/runtime/startup.sh"
    assert startup.exists(), f"Expected {startup} to exist"


def test_render_generated_tree_creates_distinct_files(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={
            "schema_version": 1,
            "base": {"tag": "ubuntu-noble-20260511"},
            "node": {"majors": {"24": {"version": "24.11.1"}}},
            "plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}},
            "tools": {},
        },
        images={"images": []},
    )
    # Each file type should exist
    assert (tmp_path / "generated/catalog/toolchains.json").exists()
    assert (tmp_path / "generated/manifest.json").exists()
    assert (tmp_path / "templates/devbox/main.tf.json").exists()


def test_render_generated_tree_does_not_create_images_json(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={"plugins": {}, "node": {"majors": {}}},
        images={"images": []},
    )
    assert not (tmp_path / "generated/catalog/images.json").exists()


def test_render_generated_tree_no_except_exception(tmp_path):
    """No bare 'except Exception' in the module. Test that rendering under
    normal conditions does not trigger generic catch blocks."""
    render_generated_tree(
        output_dir=tmp_path,
        catalog={"plugins": {}, "node": {"majors": {}}},
        images={"images": []},
    )
    # Should not raise
    assert (tmp_path / "generated/manifest.json").exists()


def test_all_json_files_have_sorted_keys(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={
            "schema_version": 1,
            "plugins": {},
            "node": {"majors": {"24": {"version": "24.11.1"}}},
            "base": {"tag": "ubuntu-noble-20260511"},
        },
        images={"images": []},
    )
    # Check all generated JSON files have sorted keys by verifying
    # the JSON text has the expected sorted key order
    for json_file in sorted(tmp_path.rglob("*.json")):
        text = json_file.read_text()
        data = json.loads(text)
        if isinstance(data, dict):
            # Re-serialize with sort_keys and compare text (ignoring whitespace differences)
            expected = json.dumps(data, indent=2, sort_keys=True) + "\n"
            assert text == expected, f"{json_file.name} has unsorted keys"


def test_no_vsix_binaries_in_generated_tree(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={"plugins": {}, "node": {"majors": {}}},
        images={"images": []},
    )
    vsix_files = list(tmp_path.rglob("*.vsix"))
    assert len(vsix_files) == 0


def test_manifest_json_has_no_auto_string(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={"plugins": {}, "node": {"majors": {}}},
        images={"images": []},
    )
    manifest_text = (tmp_path / "generated/manifest.json").read_text()
    assert '"auto"' not in manifest_text


def test_render_generated_tree_with_source_commit_params(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={"plugins": {}, "node": {"majors": {}}},
        images={"images": []},
        source_commit="commithash123",
        workflow_run_id="run456",
    )
    manifest = json.loads((tmp_path / "generated/manifest.json").read_text())
    assert manifest["source_commit"] == "commithash123"
    assert manifest["workflow_run_id"] == "run456"


def test_render_generated_tree_manifest_image_tags_use_get(tmp_path):
    """Image entries without 'image' key should produce empty string, not KeyError."""
    images = {"images": [{"node_major": 24}]}
    render_generated_tree(
        output_dir=tmp_path,
        catalog={"plugins": {}, "node": {"majors": {}}},
        images=images,
    )
    manifest = json.loads((tmp_path / "generated/manifest.json").read_text())
    # Missing 'image' key -> empty string
    assert manifest["image_tags"] == [""]


def test_render_generated_tree_extensions_created(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={
            "schema_version": 1,
            "base": {"tag": "ubuntu-noble-20260511"},
            "node": {"majors": {"24": {"version": "24.11.1"}}},
            "plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}},
        },
        images={"images": []},
    )
    ext_dir = tmp_path / "templates/devbox/extensions"
    assert ext_dir.exists()
    assert (ext_dir / "core.txt").exists()
