"""Tests for codervps.render.template -- main.tf.json rendering."""

from __future__ import annotations

import json

from codervps.render.template import _make_language_options, _make_node_options, render_main_tf_json


# ---- Option helpers ----


def test_make_node_options():
    catalog = {
        "node": {
            "majors": {
                "24": {"version": "24.11.1"},
                "22": {"version": "22.21.0"},
                "20": {"version": "20.19.5"},
                "18": {"version": "18.20.8"},
                "16": {"version": "16.20.2"},
            }
        }
    }
    options = _make_node_options(catalog)
    assert len(options) == 5
    values = [o["value"] for o in options]
    assert values == ["24", "22", "20", "18", "16"]


def test_make_language_options():
    options = _make_language_options()
    assert len(options) == 4
    values = [o["value"] for o in options]
    assert values == ["python", "rust", "go", "cpp"]


# ---- Top-level structure ----


def test_render_has_terraform_block():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    assert "terraform" in doc
    assert "coder/coder" in doc["terraform"]["required_providers"]["coder"]["source"]


def test_render_has_provider_blocks():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    assert "provider" in doc
    assert "coder" in doc["provider"]
    assert "docker" in doc["provider"]


def test_render_has_data_blocks():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    assert "data" in doc
    assert "coder_workspace" in doc["data"]
    assert "coder_parameter" in doc["data"]


def test_render_has_resource_blocks():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    assert "resource" in doc
    assert "docker_volume" in doc["resource"]
    assert "docker_container" in doc["resource"]
    assert "coder_agent" in doc["resource"]
    assert "coder_app" in doc["resource"]


# ---- Volume isolation ----


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
    container = resources["docker_container"]["workspace"]
    assert container["volumes"][0]["container_path"] == "/workspace"
    assert container["volumes"][0]["volume_name"] == "${docker_volume.workspace.name}"


def test_volume_has_coder_labels():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    volume = doc["resource"]["docker_volume"]["workspace"]
    labels = volume["labels"]
    label_keys = [lbl["label"] for lbl in labels]
    assert "coder.workspace_id" in label_keys
    assert "coder.owner" in label_keys


# ---- Parameter immutability ----


def test_parameters_are_immutable():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    params = doc["data"]["coder_parameter"]
    assert params["node_major"]["mutable"] is False
    assert params["languages"]["mutable"] is False
    # Language-specific params also immutable
    for key, param in params.items():
        if key not in ("node_major", "languages"):
            assert param["mutable"] is False, f"{key} should be immutable"


# ---- No host docker socket or prevent_destroy ----


def test_template_does_not_mount_host_docker_socket_or_block_destroy():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    text = json.dumps(doc, sort_keys=True)
    assert "/var/run/docker.sock" not in text
    assert "docker.sock" not in text
    assert "prevent_destroy" not in text


# ---- Node major parameter ----


def test_node_major_parameter():
    doc = render_main_tf_json(
        images={"images": []},
        catalog={
            "plugins": {},
            "node": {
                "majors": {
                    "24": {"version": "24.11.1"},
                    "22": {"version": "22.21.0"},
                    "20": {"version": "20.19.5"},
                    "18": {"version": "18.20.8"},
                    "16": {"version": "16.20.2"},
                }
            },
        },
    )
    param = doc["data"]["coder_parameter"]["node_major"]
    assert param["name"] == "node_major"
    assert param["display_name"] == "Node.js"
    assert param["type"] == "string"
    assert param["default"] == "24"
    assert len(param["option"]) == 5


# ---- Languages parameter ----


def test_languages_parameter():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    param = doc["data"]["coder_parameter"]["languages"]
    assert param["name"] == "languages"
    assert param["type"] == "list(string)"
    assert param["default"] == '["python"]'
    assert len(param["option"]) == 4


# ---- Language-specific parameters ----


def test_python_parameters_present():
    doc = render_main_tf_json(
        images={"images": []}, catalog={"plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}}}
    )
    params = doc["data"]["coder_parameter"]
    assert "python_version" in params
    assert "python_tools" in params
    assert params["python_version"]["condition"]


def test_rust_parameters_present():
    doc = render_main_tf_json(
        images={"images": []}, catalog={"plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}}}
    )
    params = doc["data"]["coder_parameter"]
    assert "rust_toolchain" in params
    assert params["rust_toolchain"]["condition"]


def test_go_parameters_present():
    doc = render_main_tf_json(
        images={"images": []}, catalog={"plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}}}
    )
    params = doc["data"]["coder_parameter"]
    assert "go_version" in params
    assert "go_tools" in params
    assert params["go_version"]["condition"]


def test_cpp_parameters_present():
    doc = render_main_tf_json(
        images={"images": []}, catalog={"plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}}}
    )
    params = doc["data"]["coder_parameter"]
    assert "cpp_llvm" in params
    assert params["cpp_llvm"]["condition"]


def test_condition_contains_language_reference():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {"python": {}}})
    params = doc["data"]["coder_parameter"]
    assert "python_version" in params
    condition = params["python_version"]["condition"]
    assert "data.coder_parameter.languages.value" in condition
    assert '"python"' in condition


# ---- Container configuration ----


def test_container_uses_start_count():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    container = doc["resource"]["docker_container"]["workspace"]
    assert container["count"] == "${data.coder_workspace.me.start_count}"


def test_container_has_coder_labels():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    container = doc["resource"]["docker_container"]["workspace"]
    labels = container["labels"]
    label_keys = [lbl["label"] for lbl in labels]
    assert "coder.workspace_id" in label_keys
    assert "coder.owner" in label_keys


def test_container_mounts_opt_cde_readonly():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    container = doc["resource"]["docker_container"]["workspace"]
    volumes = container["volumes"]
    opt_mounts = [v for v in volumes if "/opt/cde" in v.get("container_path", "")]
    for mount in opt_mounts:
        assert mount["read_only"] is True


def test_workspace_volume_read_write():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    container = doc["resource"]["docker_container"]["workspace"]
    ws_mount = [v for v in container["volumes"] if v["container_path"] == "/workspace"][0]
    assert ws_mount["read_only"] is False


# ---- Coder agent ----


def test_agent_configuration():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    agent = doc["resource"]["coder_agent"]["main"]
    assert agent["os"] == "linux"
    assert agent["dir"] == "/workspace"
    assert "startup_script" in agent


# ---- Coder app ----


def test_code_server_app():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    app = doc["resource"]["coder_app"]["code_server"]
    assert app["slug"] == "code-server"
    assert app["display_name"] == "VS Code Web"
    assert app["share"] == "owner"
    assert app["subdomain"] is False
    assert "13337" in app["url"]


# ---- Locals ----


def test_locals_has_images_and_catalog():
    doc = render_main_tf_json(
        images={"images": [{"node_major": 24, "image": "ghcr.io/test:image"}]},
        catalog={"plugins": {}},
    )
    locals_block = doc["locals"]
    assert "images" in locals_block
    assert "catalog" in locals_block
    assert "selected_image" in locals_block


def test_selected_image_uses_for_expression():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    selected = doc["locals"]["selected_image"]
    assert "one(" in selected
    assert "data.coder_parameter.node_major.value" in selected


# ---- Empty catalog still produces valid structure ----


def test_render_with_empty_catalog():
    doc = render_main_tf_json(images={"images": []}, catalog={})
    assert "terraform" in doc
    assert "resource" in doc


def test_render_with_no_images():
    doc = render_main_tf_json(images={}, catalog={"plugins": {}})
    assert doc["locals"]["images"] == []


# ---- JSON can be serialized ----


def test_output_is_valid_json():
    doc = render_main_tf_json(
        images={"images": []}, catalog={"plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}}}
    )
    serialized = json.dumps(doc, sort_keys=True)
    assert len(serialized) > 0
    roundtripped = json.loads(serialized)
    assert roundtripped == doc


# ---- Order of volume parameters ----


def test_node_major_is_first_parameter():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    params = doc["data"]["coder_parameter"]
    assert params["node_major"]["order"] == 1


def test_languages_is_second_parameter():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    params = doc["data"]["coder_parameter"]
    assert params["languages"]["order"] == 2


def test_language_parameters_have_higher_order():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {"python": {}}})
    params = doc["data"]["coder_parameter"]
    assert params["python_version"]["order"] > params["languages"]["order"]


# ---- Missing plugins skip parameters ----


def test_missing_plugin_no_parameters():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {"python": {}}})
    params = doc["data"]["coder_parameter"]
    assert "rust_toolchain" not in params
    assert "go_version" not in params
    assert "cpp_llvm" not in params
