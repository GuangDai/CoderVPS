"""Static tests for .github/workflows/generate.yml."""

from __future__ import annotations

import re
from pathlib import Path


def test_generate_workflow_uses_uv_and_buildx():
    text = Path(".github/workflows/generate.yml").read_text()
    assert "astral-sh/setup-uv" in text
    assert "docker/setup-buildx-action" in text
    assert "docker/build-push-action" in text
    assert "actions/upload-artifact" in text
    assert "actions/download-artifact" in text
    assert "linux/amd64" in text
    assert "workflow_dispatch" in text
    assert "schedule" in text
    assert "concurrency:" in text
    assert "allow_rebuild_date_tag" in text
    assert "docker buildx imagetools inspect" in text
    assert "--force-with-lease" in text
    assert "--force\n" not in text
    assert "! -name .git" in text
    assert "codervps-devbox:test" not in text


def test_workflow_has_permissions():
    text = Path(".github/workflows/generate.yml").read_text()
    assert "contents:" in text
    assert "packages:" in text


def test_workflow_has_concurrency_group():
    text = Path(".github/workflows/generate.yml").read_text()
    assert "concurrency:" in text
    assert "cancel-in-progress:" in text


def test_workflow_uploads_matrix_artifact():
    text = Path(".github/workflows/generate.yml").read_text()
    assert "upload-artifact" in text
    assert "download-artifact" in text


def test_workflow_passes_images_flag_to_render_generated():
    """The publish-generated job MUST pass --images to render-generated."""
    text = Path(".github/workflows/generate.yml").read_text()
    # Find the publish-generated job section
    # Look for --images flag in the render-generated call
    publish_section_match = re.search(r"publish-generated:.*?(?=\n  \w|\Z)", text, re.DOTALL)
    assert publish_section_match is not None, "publish-generated job not found"
    publish_section = publish_section_match.group(0)
    assert "--images" in publish_section, "publish-generated must pass --images to render-generated"


def test_workflow_passes_write_images_json():
    text = Path(".github/workflows/generate.yml").read_text()
    assert "--write-images-json" in text


def test_workflow_fail_fast_false():
    text = Path(".github/workflows/generate.yml").read_text()
    assert "fail-fast" in text


def test_workflow_build_args_match_matrix_keys():
    """Dockerfile build-args in workflow should include all 7 ARGs."""
    text = Path(".github/workflows/generate.yml").read_text()
    expected_args = [
        "BASE_IMAGE",
        "NODE_VERSION",
        "UV_VERSION",
        "CODE_SERVER_VERSION",
        "SCCACHE_VERSION",
        "SCCACHE_ASSET",
        "SCCACHE_SHA256",
        "LLVM_VERSION",
    ]
    for arg in expected_args:
        assert arg in text, f"Missing build-arg: {arg}"


def test_workflow_has_matrix_json_for_strategy():
    text = Path(".github/workflows/generate.yml").read_text()
    assert "matrix:" in text
    # Should use fromJson to parse matrix output
    assert "fromJson" in text
    assert "needs.prepare.outputs.matrix" in text


def test_workflow_does_not_have_stray_nephew():
    """The word 'nephew' (typo of 'needs') should not appear."""
    text = Path(".github/workflows/generate.yml").read_text()
    assert "nephew" not in text


def test_workflow_has_tag_immutability_check():
    text = Path(".github/workflows/generate.yml").read_text()
    assert "allow_rebuild_date_tag" in text


def test_workflow_checks_image_not_exists():
    text = Path(".github/workflows/generate.yml").read_text()
    assert "imagetools inspect" in text
