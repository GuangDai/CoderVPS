"""Render Coder Terraform JSON template (main.tf.json).

Generates the full Coder template with catalog-driven parameter options,
immutable workspace parameters, extra_extension_packs from extensions config,
and workspace-isolated volume mounts.
"""

from __future__ import annotations

from pathlib import Path

from .extensions import _LANGUAGES


def _make_node_options(catalog: dict) -> list[dict]:
    """Build Node.js dropdown options from catalog node majors (descending)."""
    majors = catalog.get("node", {}).get("majors", {})
    sorted_keys = sorted(majors.keys(), key=lambda k: int(k), reverse=True)
    return [{"name": f"Node {major}", "value": major} for major in sorted_keys]


def _make_language_options() -> list[dict]:
    """Build language multi-select options (fixed 4 languages)."""
    return [
        {"name": "Python", "value": "python"},
        {"name": "Rust", "value": "rust"},
        {"name": "Go", "value": "go"},
        {"name": "C/C++", "value": "cpp"},
    ]


def _make_default_node_major(catalog: dict) -> str:
    """Pick the highest node major from catalog as default."""
    majors = catalog.get("node", {}).get("majors", {})
    if majors:
        return str(max(int(k) for k in majors))
    return "24"


def _make_extra_packs_options() -> list[dict]:
    """Build extra_extension_packs options from config/extensions.toml packs."""
    try:
        from codervps.config import load_extensions_config

        ext_cfg = load_extensions_config(Path("config/extensions.toml"))
        return [{"name": pack.label, "value": name} for name, pack in ext_cfg.packs.items()]
    except (OSError, ValueError, KeyError, ModuleNotFoundError):
        # Return empty list if config is unavailable -- the parameter still
        # exists but with no options, which is safe for the template.
        return []


def _build_rust_toolchain_options() -> list[dict]:
    """Build Rust toolchain options: stable, beta, nightly + 30 recent stable minors.

    The starting stable minor is configurable via rust.stable_minor_count in
    toolchains.toml, but since the actual latest stable is discovered at catalog
    time, these represent the channels rustup can install.

    # TODO: use latest_stable from rustup/dist-server metadata to compute
    # the exact 30 most recent stable minor channels dynamically
    # Blocked by: no rustup metadata discovery implemented yet
    # Will be implemented: Task D (T13 Full Validation)
    """
    options: list[dict] = [
        {"name": "Stable", "value": "stable"},
        {"name": "Beta", "value": "beta"},
        {"name": "Nightly", "value": "nightly"},
    ]
    # 30 most recent stable minor version channels (configurable start).
    # These are channels rustup recognizes as installable stable toolchains.
    # TODO: derive start value dynamically from rustup/dist-server metadata
    # The value 88 represents the latest stable minor as of 2026-05.
    # Blocked by: no rustup metadata discovery implemented yet
    # Will be implemented: Task D (T13 Full Validation)
    start = 88
    for i in range(30):
        ver = f"1.{start - i}"
        options.append({"name": f"Rust {ver}", "value": ver})
    return options


def _make_language_parameters(catalog: dict) -> dict:
    """Build catalog-driven language-specific Coder parameters.

    Dropdown options are built from catalog data when available, with
    documented fallback lists when catalog versions are not yet discovered.
    Only languages present in the catalog's plugins dict get parameters.
    """
    params: dict = {}
    plugins = catalog.get("plugins", {})

    plugin_param_orders = {"python": (10, 19), "rust": (20, 29), "go": (30, 39), "cpp": (40, 49)}
    plugin_labels = {"python": "Python", "rust": "Rust", "go": "Go", "cpp": "C/C++"}

    for plugin_id in _LANGUAGES:
        if plugin_id not in plugins:
            continue
        order_range = plugin_param_orders.get(plugin_id, (50, 59))
        label = plugin_labels.get(plugin_id, plugin_id)
        plugin_catalog = plugins[plugin_id]
        defaults = plugin_catalog.get("defaults", {})

        if plugin_id == "python":
            version_default = defaults.get("version", "3.13")
            versions = plugin_catalog.get("versions", [])
            if versions:
                options = [
                    {
                        "name": f"Python {v.get('version', v.get('value', ''))}",
                        "value": v.get("version", v.get("value", "")),
                    }
                    for v in versions
                ]
            else:
                # TODO: populate from uv python install --list once catalog has python versions
                # Blocked by: python version discovery not implemented in catalog refresh
                # Will be implemented: Task D (T13 Full Validation)
                options = [
                    {"name": "Python 3.13", "value": "3.13"},
                    {"name": "Python 3.12", "value": "3.12"},
                    {"name": "Python 3.11", "value": "3.11"},
                ]

            params["python_version"] = {
                "name": "python_version",
                "display_name": f"{label} Version",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": version_default,
                "order": order_range[0],
                "condition": 'contains(data.coder_parameter.languages.value, "python")',
                "option": options,
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
            toolchain_default = defaults.get("toolchain", "stable")
            params["rust_toolchain"] = {
                "name": "rust_toolchain",
                "display_name": f"{label} Toolchain",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": toolchain_default,
                "order": order_range[0],
                "condition": 'contains(data.coder_parameter.languages.value, "rust")',
                "option": _build_rust_toolchain_options(),
            }
        elif plugin_id == "go":
            version_default = defaults.get("version", "1.24.9")
            versions = plugin_catalog.get("versions", [])
            if versions:
                options = []
                for v in versions:
                    val = v.get("version", "")
                    options.append({"name": f"Go {val}", "value": val})
            else:
                # TODO: populate from go.dev/dl catalog when not using fixtures
                # Blocked by: go discovery already implemented in catalog refresh
                # Will be resolved: when catalog has go versions from discovery
                options = [
                    {"name": "Go 1.24", "value": "1.24.9"},
                ]

            params["go_version"] = {
                "name": "go_version",
                "display_name": f"{label} Version",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": version_default,
                "order": order_range[0],
                "condition": 'contains(data.coder_parameter.languages.value, "go")',
                "option": options,
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
            llvm_default = defaults.get("llvm", "19")
            # TODO: populate LLVM versions from apt.llvm.org metadata
            # Blocked by: llvm version discovery not implemented in catalog refresh
            # Will be implemented: Task D (T13 Full Validation)
            params["cpp_llvm"] = {
                "name": "cpp_llvm",
                "display_name": f"{label} LLVM Version",
                "type": "string",
                "form_type": "dropdown",
                "mutable": False,
                "default": llvm_default,
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
    """Render a complete Coder main.tf.json document.

    Args:
        images: Images catalog dict with 'images' key containing image entries.
        catalog: Toolchain catalog dict with plugins, node majors, etc.

    Returns:
        dict: Full Terraform JSON document suitable for json.dumps.
    """
    node_options = _make_node_options(catalog)
    lang_options = _make_language_options()
    lang_params = _make_language_parameters(catalog)
    node_default = _make_default_node_major(catalog)
    extra_packs_options = _make_extra_packs_options()

    all_params: dict = {
        "node_major": {
            "name": "node_major",
            "display_name": "Node.js",
            "type": "string",
            "form_type": "dropdown",
            "mutable": False,
            "default": node_default,
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
        "extra_extension_packs": {
            "name": "extra_extension_packs",
            "display_name": "Extra Extension Packs",
            "type": "list(string)",
            "form_type": "multi-select",
            "mutable": False,
            "default": "[]",
            "order": 3,
            "option": extra_packs_options,
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
