"""Tests for codervps.render.template -- Terraform JSON renderer."""

from __future__ import annotations

import json

from codervps.render.template import render_main_tf_json


# ============================================================================
# Workspace volume tests
# ============================================================================


def test_main_tf_json_contains_isolated_workspace_volume():
    doc = render_main_tf_json(
        images={
            "images": [
                {
                    "node_major": 24,
                    "image": "ghcr.io/guangdai/codervps-devbox:noble-20260511-node24",
                }
            ]
        },
        catalog={"plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}}},
    )
    resources = doc["resource"]
    volume = resources["docker_volume"]["workspace"]
    assert volume["name"] == "coder-${data.coder_workspace.me.id}-workspace"
    assert volume["lifecycle"]["ignore_changes"] == "all"


def test_volume_has_workspace_id_label():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    volume = doc["resource"]["docker_volume"]["workspace"]
    labels = {lab["label"]: lab["value"] for lab in volume["labels"]}
    assert "coder.workspace_id" in labels
    assert "${data.coder_workspace.me.id}" in labels["coder.workspace_id"]


def test_volume_has_owner_label():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    volume = doc["resource"]["docker_volume"]["workspace"]
    labels = {lab["label"]: lab["value"] for lab in volume["labels"]}
    assert "coder.owner" in labels


# ============================================================================
# Parameter tests
# ============================================================================


def test_parameters_are_immutable():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    params = doc["data"]["coder_parameter"]
    assert params["node_major"]["mutable"] is False
    assert params["languages"]["mutable"] is False


def test_node_major_parameter_options():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    params = doc["data"]["coder_parameter"]
    node_opts = params["node_major"]["option"]
    values = [o["value"] for o in node_opts]
    assert values == ["24", "22", "20", "18", "16"]


def test_languages_multi_select_options():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    params = doc["data"]["coder_parameter"]
    lang = params["languages"]
    assert lang["type"] == "list(string)"
    options = {o["value"] for o in lang["option"]}
    assert options == {"python", "rust", "go", "cpp"}


def test_per_language_parameters_have_conditions():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    params = doc["data"]["coder_parameter"]
    assert "condition" in params["python_version"]
    assert "condition" in params["rust_toolchain"]
    assert "condition" in params["go_version"]
    assert "condition" in params["cpp_llvm"]


# ============================================================================
# Container and agent tests
# ============================================================================


def test_container_mounts_workspace_volume():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    container = doc["resource"]["docker_container"]["workspace"]
    workspace_vol = [v for v in container["volumes"] if v["container_path"] == "/workspace"]
    assert len(workspace_vol) == 1
    assert workspace_vol[0]["read_only"] is False
    assert "docker_volume.workspace.name" in workspace_vol[0]["volume_name"]


def test_container_mounts_extensions_read_only():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    container = doc["resource"]["docker_container"]["workspace"]
    ext_vol = [v for v in container["volumes"] if v["container_path"] == "/opt/cde/extensions"]
    assert len(ext_vol) == 1
    assert ext_vol[0]["read_only"] is True


def test_container_mounts_vsix_read_only():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    container = doc["resource"]["docker_container"]["workspace"]
    vsix_vol = [v for v in container["volumes"] if v["container_path"] == "/opt/cde/vsix"]
    assert len(vsix_vol) == 1
    assert vsix_vol[0]["read_only"] is True


def test_container_uses_start_count():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    container = doc["resource"]["docker_container"]["workspace"]
    assert "start_count" in container["count"]


def test_coder_agent_main_dir_is_workspace():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    agent = doc["resource"]["coder_agent"]["main"]
    assert agent["dir"] == "/workspace"
    assert agent["os"] == "linux"


def test_code_server_app():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    app = doc["resource"]["coder_app"]["code_server"]
    assert app["slug"] == "code-server"
    assert "13337" in app["url"]


# ============================================================================
# Safety constraints
# ============================================================================


def test_template_does_not_mount_host_docker_socket():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    text = json.dumps(doc, sort_keys=True)
    assert "/var/run/docker.sock" not in text
    assert "docker.sock" not in text


def test_template_does_not_use_prevent_destroy():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    text = json.dumps(doc, sort_keys=True)
    assert "prevent_destroy" not in text


# ============================================================================
# Locals / image selection
# ============================================================================


def test_selected_image_local():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    assert "selected_image" in doc["locals"]
    assert "image.image" in doc["locals"]["selected_image"]


def test_images_passed_through_locals():
    images = {
        "images": [
            {
                "node_major": 24,
                "image": "ghcr.io/guangdai/codervps-devbox:noble-20260511-node24",
            }
        ]
    }
    doc = render_main_tf_json(images=images, catalog={"plugins": {}})
    assert doc["locals"]["images"] == images["images"]


# ============================================================================
# Terraform provider requirements
# ============================================================================


def test_terraform_block_has_required_providers():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    providers = doc["terraform"]["required_providers"]
    assert providers["coder"]["source"] == "coder/coder"
    assert providers["docker"]["source"] == "kreuzwerker/docker"


def test_provider_block_exists():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    assert "coder" in doc["provider"]
    assert "docker" in doc["provider"]


# ============================================================================
# Catalog-driven parameter defaults
# ============================================================================


def test_python_default_from_catalog():
    catalog = {"plugins": {"python": {"defaults": {"version": "3.12"}}}}
    doc = render_main_tf_json(images={"images": []}, catalog=catalog)
    assert doc["data"]["coder_parameter"]["python_version"]["default"] == "3.12"


def test_go_default_from_catalog():
    catalog = {"plugins": {"go": {"defaults": {"version": "1.21"}}}}
    doc = render_main_tf_json(images={"images": []}, catalog=catalog)
    assert doc["data"]["coder_parameter"]["go_version"]["default"] == "1.21"


def test_rust_default_from_catalog():
    catalog = {"plugins": {"rust": {"defaults": {"toolchain": "nightly"}}}}
    doc = render_main_tf_json(images={"images": []}, catalog=catalog)
    assert doc["data"]["coder_parameter"]["rust_toolchain"]["default"] == "nightly"


def test_cpp_default_from_catalog():
    catalog = {"plugins": {"cpp": {"defaults": {"llvm": "19"}}}}
    doc = render_main_tf_json(images={"images": []}, catalog=catalog)
    assert doc["data"]["coder_parameter"]["cpp_llvm"]["default"] == "19"


# ============================================================================
# JSON roundtrip
# ============================================================================


def test_render_main_tf_json_is_valid_json():
    doc = render_main_tf_json(
        images={"images": []},
        catalog={"plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}}},
    )
    serialized = json.dumps(doc, sort_keys=True)
    re_parsed = json.loads(serialized)
    assert re_parsed == doc


def test_required_top_level_keys():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    for key in ["terraform", "provider", "data", "resource", "locals"]:
        assert key in doc, f"missing top-level key: {key}"
