from __future__ import annotations


def _make_node_options() -> list[dict]:
    return [
        {"name": "Node 24", "value": "24"},
        {"name": "Node 22", "value": "22"},
        {"name": "Node 20", "value": "20"},
        {"name": "Node 18", "value": "18"},
        {"name": "Node 16", "value": "16"},
    ]


def _make_language_options() -> list[dict]:
    return [
        {"name": "Python", "value": "python"},
        {"name": "Rust", "value": "rust"},
        {"name": "Go", "value": "go"},
        {"name": "C/C++", "value": "cpp"},
    ]


def _make_language_parameters(catalog: dict) -> dict:
    params: dict = {}
    plugins = catalog.get("plugins", {})

    plugin_param_orders = {"python": (10, 19), "rust": (20, 29), "go": (30, 39), "cpp": (40, 49)}
    plugin_labels = {"python": "Python", "rust": "Rust", "go": "Go", "cpp": "C/C++"}
    plugin_defaults_map = {
        "python": "3.13",
        "rust": "stable",
        "go": "1.24.9",
        "cpp": "19",
    }

    for plugin_id in ["python", "rust", "go", "cpp"]:
        if plugin_id not in plugins:
            continue
        order_range = plugin_param_orders.get(plugin_id, (50, 59))
        label = plugin_labels.get(plugin_id, plugin_id)
        defaults = plugins[plugin_id].get("defaults", {})
        version_default = (
            defaults.get("version")
            or defaults.get("toolchain")
            or defaults.get("llvm")
            or plugin_defaults_map.get(plugin_id, "")
        )

        if plugin_id == "python":
            params["python_version"] = {
                "name": "python_version",
                "display_name": f"{label} Version",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": version_default,
                "order": order_range[0],
                "condition": 'contains(data.coder_parameter.languages.value, "python")',
                "option": [
                    {"name": "3.13", "value": "3.13"},
                    {"name": "3.12", "value": "3.12"},
                    {"name": "3.11", "value": "3.11"},
                ],
            }
            params["python_tools"] = {
                "name": "python_tools",
                "display_name": f"{label} Tools",
                "type": "list(string)",
                "form_type": "multi-select",
                "mutable": False,
                "default": '["ruff", "debugpy"]',
                "order": order_range[0] + 1,
                "condition": 'contains(data.coder_parameter.languages.value, "python")',
                "option": [
                    {"name": "ruff", "value": "ruff"},
                    {"name": "debugpy", "value": "debugpy"},
                    {"name": "IPython", "value": "ipython"},
                    {"name": "Jupyter", "value": "jupyter"},
                ],
            }
        elif plugin_id == "rust":
            params["rust_toolchain"] = {
                "name": "rust_toolchain",
                "display_name": f"{label} Toolchain",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": version_default,
                "order": order_range[0],
                "condition": 'contains(data.coder_parameter.languages.value, "rust")',
                "option": [
                    {"name": "Stable", "value": "stable"},
                    {"name": "Beta", "value": "beta"},
                    {"name": "Nightly", "value": "nightly"},
                ],
            }
        elif plugin_id == "go":
            params["go_version"] = {
                "name": "go_version",
                "display_name": f"{label} Version",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": version_default,
                "order": order_range[0],
                "condition": 'contains(data.coder_parameter.languages.value, "go")',
                "option": [
                    {"name": "Go 1.24", "value": "1.24.9"},
                    {"name": "Go 1.23", "value": "1.23.12"},
                    {"name": "Go 1.22", "value": "1.22.12"},
                ],
            }
            params["go_tools"] = {
                "name": "go_tools",
                "display_name": f"{label} Tools",
                "type": "list(string)",
                "form_type": "multi-select",
                "mutable": False,
                "default": '["gopls"]',
                "order": order_range[0] + 1,
                "condition": 'contains(data.coder_parameter.languages.value, "go")',
                "option": [
                    {"name": "gopls", "value": "gopls"},
                    {"name": "dlv (Delve)", "value": "dlv"},
                ],
            }
        elif plugin_id == "cpp":
            params["cpp_llvm"] = {
                "name": "cpp_llvm",
                "display_name": f"{label} LLVM Version",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": version_default,
                "order": order_range[0],
                "condition": 'contains(data.coder_parameter.languages.value, "cpp")',
                "option": [
                    {"name": "LLVM 19", "value": "19"},
                    {"name": "LLVM 18", "value": "18"},
                    {"name": "LLVM 17", "value": "17"},
                ],
            }
    return params


def render_main_tf_json(images: dict, catalog: dict) -> dict:
    node_options = _make_node_options()
    lang_options = _make_language_options()
    lang_params = _make_language_parameters(catalog)

    all_params: dict = {
        "node_major": {
            "name": "node_major",
            "display_name": "Node.js",
            "type": "string",
            "form_type": "dropdown",
            "mutable": False,
            "default": "24",
            "order": 1,
            "option": node_options,
        },
        "languages": {
            "name": "languages",
            "display_name": "Languages",
            "type": "list(string)",
            "form_type": "multi-select",
            "mutable": False,
            "default": '["python"]',
            "order": 2,
            "option": lang_options,
        },
    }
    all_params.update(lang_params)

    return {
        "terraform": {
            "required_providers": {
                "coder": {"source": "coder/coder", "version": ">= 2.25.0"},
                "docker": {"source": "kreuzwerker/docker"},
            }
        },
        "provider": {
            "coder": [{}],
            "docker": [{}],
        },
        "data": {
            "coder_workspace": {"me": {}},
            "coder_workspace_owner": {"me": {}},
            "coder_provisioner": {"me": {}},
            "coder_parameter": all_params,
        },
        "resource": {
            "docker_volume": {
                "workspace": {
                    "name": "coder-${data.coder_workspace.me.id}-workspace",
                    "lifecycle": {"ignore_changes": "all"},
                    "labels": [
                        {
                            "label": "coder.workspace_id",
                            "value": "${data.coder_workspace.me.id}",
                        },
                        {
                            "label": "coder.owner",
                            "value": "${data.coder_workspace_owner.me.name}",
                        },
                    ],
                }
            },
            "coder_agent": {
                "main": {
                    "arch": "${data.coder_provisioner.me.arch}",
                    "os": "linux",
                    "dir": "/workspace",
                    "startup_script": '${file("${path.module}/startup.sh")}',
                }
            },
            "coder_app": {
                "code_server": {
                    "agent_id": "${coder_agent.main.id}",
                    "slug": "code-server",
                    "display_name": "VS Code Web",
                    "url": "http://127.0.0.1:13337/?folder=/workspace",
                    "share": "owner",
                    "subdomain": False,
                }
            },
            "docker_container": {
                "workspace": {
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
                        {
                            "label": "coder.workspace_id",
                            "value": "${data.coder_workspace.me.id}",
                        },
                        {
                            "label": "coder.owner",
                            "value": "${data.coder_workspace_owner.me.name}",
                        },
                    ],
                }
            },
        },
        "locals": {
            "images": images.get("images", []),
            "catalog": catalog,
            "selected_image": "${one([for image in local.images : image.image if tostring(image.node_major) == data.coder_parameter.node_major.value])}",
        },
    }
