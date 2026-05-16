"""Render the full generated branch tree.

Orchestrates: catalog JSON, manifest.json, Terraform HCL template,
runtime shell files, extension lists, and VSIX README markers.

images.json is intentionally NOT written by default -- it must be written
separately after all Docker image builds succeed (via write_images_json=True
or by the GitHub Actions publish job).
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from codervps import __version__
from codervps.config import load_extensions_config
from codervps.render.extensions import render_extensions
from codervps.render.template import render_main_tf_hcl


def _write_json_sorted(path: Path, data: object) -> None:
    """Write JSON with sorted keys and trailing newline for deterministic output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _copy_runtime_files(dest: Path) -> None:
    """Copy runtime shell files from source tree to generated tree.

    The Coder template uses ${file("${path.module}/startup.sh")} as the
    agent startup script, so startup.sh must exist at the template root.

    The rest of runtime/ is copied under templates/devbox/runtime/ and mounted
    read-only into workspaces at /opt/cde/runtime.
    """
    src_root = Path("runtime")
    if not src_root.exists():
        return

    template_dir = dest / "templates/devbox"
    runtime_dir = template_dir / "runtime"

    for src_file in src_root.rglob("*"):
        if src_file.is_dir():
            continue
        rel = src_file.relative_to(src_root)
        dst_file = runtime_dir / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)

    startup = src_root / "startup.sh"
    if startup.exists():
        template_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(startup, template_dir / "startup.sh")


def render_generated_tree(
    output_dir: Path,
    catalog: dict,
    images: dict,
    *,
    write_images_json: bool = False,
    source_commit: str = "",
    workflow_run_id: str = "",
) -> None:
    """Render the full generated branch tree.

    Args:
        output_dir: Root output directory (e.g. build/generated).
        catalog: Toolchain catalog dict (from refresh_catalog).
        images: Images catalog dict (build matrix output).
        write_images_json: If True, write images.json. Default False --
            images.json is written separately after all image builds succeed.
        source_commit: Git SHA of the source commit (for manifest).
        workflow_run_id: GitHub Actions run ID (for manifest).
    """
    # --- Catalog JSON files ---
    catalog_dir = output_dir / "generated/catalog"
    _write_json_sorted(catalog_dir / "toolchains.json", catalog)

    # images.json is written ONLY when explicitly requested (after builds succeed)
    if write_images_json:
        _write_json_sorted(catalog_dir / "images.json", images)

    # --- Manifest ---
    image_tags = [img.get("image", "") for img in images.get("images", [])]

    node_versions = {}
    for major_str, info in catalog.get("node", {}).get("majors", {}).items():
        node_versions[major_str] = info.get("version", "")

    tool_versions = {}
    for tool_name, tool_info in catalog.get("tools", {}).items():
        if isinstance(tool_info, dict):
            tool_versions[tool_name] = tool_info.get("version", "")

    manifest = {
        "schema_version": 1,
        "source_commit": source_commit or os.environ.get("GITHUB_SHA", ""),
        "workflow_run_id": workflow_run_id or os.environ.get("GITHUB_RUN_ID", ""),
        "generator_version": __version__,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "coder_base": {
            "source": catalog.get("base", {}).get("source", "codercom/example-base"),
            "tag": catalog.get("base", {}).get("tag", ""),
        },
        "node_versions": node_versions,
        "tool_versions": tool_versions,
        "image_tags": image_tags,
    }
    _write_json_sorted(output_dir / "generated/manifest.json", manifest)

    # --- Terraform template ---
    template_dir = output_dir / "templates/devbox"
    template_dir.mkdir(parents=True, exist_ok=True)
    legacy_json_template = template_dir / "main.tf.json"
    if legacy_json_template.exists():
        legacy_json_template.unlink()
    (template_dir / "main.tf").write_text(render_main_tf_hcl(images, catalog))

    # --- Runtime shell files ---
    _copy_runtime_files(output_dir)

    # --- Extensions ---
    try:
        ext_cfg = load_extensions_config(Path("config/extensions.toml"))
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"failed to load extensions config: {exc}") from exc
    else:
        render_extensions(ext_cfg, template_dir)
