from __future__ import annotations

from typing import Any

_NODE_MAJORS = [24, 22, 20, 18, 16]


def _terraform_block() -> dict[str, Any]:
    return {
        "required_providers": {
            "coder": {"source": "coder/coder", "version": ">= 2.25.0"},
            "docker": {"source": "kreuzwerker/docker"},
        },
    }


def _provider_block() -> dict[str, Any]:
    return {"coder": [{}], "docker": [{}]}


def _coder_workspace_data() -> dict[str, Any]:
    return {
        "coder_workspace": {"me": {}},
        "coder_workspace_owner": {"me": {}},
        "coder_provisioner": {"me": {}},
    }


def _node_major_parameter() -> dict[str, Any]:
    return {
        "name": "node_major",
        "display_name": "Node.js",
        "type": "string",
        "form_type": "dropdown",
        "mutable": False,
        "default": "24",
        "order": 1,
        "option": [{"name": f"Node {m}", "value": str(m)} for m in _NODE_MAJORS],
    }


def _languages_parameter() -> dict[str, Any]:
    return {
        "name": "languages",
        "display_name": "Languages",
        "type": "list(string)",
        "form_type": "multi-select",
        "mutable": False,
        "default": '["python"]',
        "order": 2,
        "option": [
            {"name": "Python", "value": "python"},
            {"name": "Rust", "value": "rust"},
            {"name": "Go", "value": "go"},
            {"name": "C/C++", "value": "cpp"},
        ],
    }


def _build_coder_parameters(catalog: dict) -> dict[str, Any]:
    """Build the coder_parameter data block from catalog plugin declarations."""
    params: dict[str, Any] = {
        "node_major": _node_major_parameter(),
        "languages": _languages_parameter(),
    }

    # Add per-language parameters from catalog
    plugin_defaults = catalog.get("plugins", {})
    for pid in ["python", "rust", "go", "cpp"]:
        plugin_info = plugin_defaults.get(pid, {})
        defaults = plugin_info.get("defaults", {})
        if pid == "python":
            params["python_version"] = {
                "name": "python_version",
                "display_name": "Python Version",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": defaults.get("version", "3.13"),
                "order": 100,
                "condition": "contains(data.coder_parameter.languages.value, 'python')",
            }
            params["python_tools"] = {
                "name": "python_tools",
                "display_name": "Python Tools",
                "type": "list(string)",
                "form_type": "multi-select",
                "mutable": False,
                "default": '["ruff","debugpy"]',
                "order": 101,
                "condition": "contains(data.coder_parameter.languages.value, 'python')",
            }
        elif pid == "rust":
            params["rust_toolchain"] = {
                "name": "rust_toolchain",
                "display_name": "Rust Toolchain",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": defaults.get("toolchain", "stable"),
                "order": 200,
                "condition": "contains(data.coder_parameter.languages.value, 'rust')",
            }
        elif pid == "go":
            params["go_version"] = {
                "name": "go_version",
                "display_name": "Go Version",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": defaults.get("version", "latest"),
                "order": 300,
                "condition": "contains(data.coder_parameter.languages.value, 'go')",
            }
            params["go_tools"] = {
                "name": "go_tools",
                "display_name": "Go Tools",
                "type": "list(string)",
                "form_type": "multi-select",
                "mutable": False,
                "default": '["gopls"]',
                "order": 301,
                "condition": "contains(data.coder_parameter.languages.value, 'go')",
            }
        elif pid == "cpp":
            params["cpp_llvm"] = {
                "name": "cpp_llvm",
                "display_name": "LLVM/Clangd Version",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": defaults.get("llvm", "latest"),
                "order": 400,
                "condition": "contains(data.coder_parameter.languages.value, 'cpp')",
            }

    return params


def _docker_volume_workspace() -> dict[str, Any]:
    return {
        "name": "coder-${data.coder_workspace.me.id}-workspace",
        "lifecycle": {"ignore_changes": "all"},
        "labels": [
            {"label": "coder.workspace_id", "value": "${data.coder_workspace.me.id}"},
            {"label": "coder.owner", "value": "${data.coder_workspace_owner.me.name}"},
        ],
    }


def _coder_agent_main() -> dict[str, Any]:
    return {
        "arch": "${data.coder_provisioner.me.arch}",
        "os": "linux",
        "dir": "/workspace",
        "startup_script": '${file("${path.module}/startup.sh")}',
    }


def _coder_app_code_server() -> dict[str, Any]:
    return {
        "agent_id": "${coder_agent.main.id}",
        "slug": "code-server",
        "display_name": "VS Code Web",
        "url": "http://127.0.0.1:13337/?folder=/workspace",
        "share": "owner",
        "subdomain": False,
    }


def _docker_container_workspace() -> dict[str, Any]:
    return {
        "count": "${data.coder_workspace.me.start_count}",
        "image": "${local.selected_image}",
        "name": "coder-${data.coder_workspace.me.id}",
        "volumes": [
            {
                "container_path": "/workspace",
                "volume_name": "${docker_volume.workspace.name}",
                "read_only": False,
            },
            {
                "host_path": "/opt/coder-cde/extensions",
                "container_path": "/opt/cde/extensions",
                "read_only": True,
            },
            {
                "host_path": "/opt/coder-cde/vsix",
                "container_path": "/opt/cde/vsix",
                "read_only": True,
            },
        ],
        "labels": [
            {"label": "coder.workspace_id", "value": "${data.coder_workspace.me.id}"},
            {"label": "coder.owner", "value": "${data.coder_workspace_owner.me.name}"},
        ],
    }


def render_main_tf_json(images: dict, catalog: dict) -> dict[str, Any]:
    """Render a complete ``main.tf.json`` document.

    Parameters
    ----------
    images:
        The ``images.json``-shaped catalog (must contain an ``"images"`` array).
    catalog:
        The ``toolchains.json``-shaped catalog used for parameter defaults.
    """
    coder_params = _build_coder_parameters(catalog)
    data_block = {
        **_coder_workspace_data(),
        "coder_parameter": coder_params,
    }

    return {
        "terraform": _terraform_block(),
        "provider": _provider_block(),
        "data": data_block,
        "resource": {
            "docker_volume": {"workspace": _docker_volume_workspace()},
            "coder_agent": {"main": _coder_agent_main()},
            "coder_app": {"code_server": _coder_app_code_server()},
            "docker_container": {"workspace": _docker_container_workspace()},
        },
        "locals": {
            "images": images.get("images", []),
            "catalog": catalog,
            "selected_image": "${one([for image in local.images : image.image if tostring(image.node_major) == data.coder_parameter.node_major.value])}",
        },
    }


__all__ = ["render_main_tf_json"]
