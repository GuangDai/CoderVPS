"""Render the Coder devbox Terraform template.

The publishable template is emitted as native HCL (`main.tf`) because Coder's
Dynamic Parameters UX is documented and exercised around normal Terraform
syntax with `option {}` blocks and `count` expressions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from codervps.languages import LANGUAGE_IDS, LANGUAGE_LABELS

HOME_DIR = "/home/coder"
PROJECT_DIR = f"{HOME_DIR}/workspace"
CDEV_RUNTIME_ROOT = f"{HOME_DIR}/.cdev"
CODER_PROVIDER_VERSION = ">= 2.5.3"


def _make_node_options(catalog: dict) -> list[dict]:
    """Build Node.js dropdown options from catalog node majors."""
    majors = catalog.get("node", {}).get("majors", {})
    if not majors:
        return [{"name": "Node 24", "value": "24"}]
    sorted_keys = sorted(majors.keys(), key=lambda k: int(k), reverse=True)
    return [{"name": f"Node {major}", "value": major} for major in sorted_keys]


def _make_language_options() -> list[dict]:
    """Build canonical language options for compatibility callers."""
    return [{"name": LANGUAGE_LABELS[language], "value": language} for language in LANGUAGE_IDS]


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
        return []


def _version_options(prefix: str, versions: list[dict], fallback: str) -> list[dict]:
    """Build Terraform parameter options from catalog version entries."""
    if versions:
        options = []
        for version in versions:
            value = version.get("request", version.get("version", version.get("value", "")))
            name = version.get("label", f"{prefix} {version.get('version', value)}")
            options.append({"name": str(name), "value": str(value)})
        return options
    if fallback:
        return [{"name": f"{prefix} {fallback}", "value": fallback}]
    return []


def _language_parameter_specs(catalog: dict) -> dict[str, dict[str, Any]]:
    """Build language-specific parameters controlled by per-language enables."""
    params: dict[str, dict[str, Any]] = {}
    plugins = catalog.get("plugins", {})

    if "python" in plugins:
        plugin_catalog = plugins["python"]
        defaults = plugin_catalog.get("defaults", {})
        version_default = defaults.get("version", "cpython@3.13")
        params["python_version"] = {
            "name": "python_version",
            "display_name": "Python Runtime",
            "type": "string",
            "form_type": "dropdown",
            "mutable": False,
            "default": version_default,
            "order": 11,
            "count": "data.coder_parameter.enable_python.value ? 1 : 0",
            "option": _version_options(
                "Python", plugin_catalog.get("versions", []), version_default
            ),
        }
        params["python_tools"] = {
            "name": "python_tools",
            "display_name": "Python Tools",
            "type": "list(string)",
            "form_type": "multi-select",
            "mutable": False,
            "default": ["ruff", "debugpy"],
            "order": 12,
            "count": "data.coder_parameter.enable_python.value ? 1 : 0",
            "option": [
                {"name": "ruff", "value": "ruff"},
                {"name": "debugpy", "value": "debugpy"},
                {"name": "IPython", "value": "ipython"},
                {"name": "Jupyter", "value": "jupyter"},
            ],
        }

    if "go" in plugins:
        plugin_catalog = plugins["go"]
        defaults = plugin_catalog.get("defaults", {})
        version_default = defaults.get("version", "1.24.9")
        params["go_version"] = {
            "name": "go_version",
            "display_name": "Go Version",
            "type": "string",
            "form_type": "dropdown",
            "mutable": False,
            "default": version_default,
            "order": 21,
            "count": "data.coder_parameter.enable_go.value ? 1 : 0",
            "option": _version_options("Go", plugin_catalog.get("versions", []), version_default),
        }
        params["go_tools"] = {
            "name": "go_tools",
            "display_name": "Go Tools",
            "type": "list(string)",
            "form_type": "multi-select",
            "mutable": False,
            "default": ["gopls"],
            "order": 22,
            "count": "data.coder_parameter.enable_go.value ? 1 : 0",
            "option": [
                {"name": "gopls", "value": "gopls"},
                {"name": "dlv (Delve debugger)", "value": "dlv"},
            ],
        }

    if "rust" in plugins:
        plugin_catalog = plugins["rust"]
        defaults = plugin_catalog.get("defaults", {})
        toolchain_default = defaults.get("toolchain", "stable")
        versions = plugin_catalog.get("versions", [])
        options = [
            {
                "name": str(v.get("version", v.get("value", ""))).title()
                if str(v.get("version", v.get("value", ""))).isalpha()
                else f"Rust {v.get('version', v.get('value', ''))}",
                "value": str(v.get("version", v.get("value", ""))),
            }
            for v in versions
        ] or [{"name": "Stable", "value": toolchain_default}]
        params["rust_toolchain"] = {
            "name": "rust_toolchain",
            "display_name": "Rust Toolchain",
            "type": "string",
            "form_type": "dropdown",
            "mutable": False,
            "default": toolchain_default,
            "order": 31,
            "count": "data.coder_parameter.enable_rust.value ? 1 : 0",
            "option": options,
        }

    if "cpp" in plugins:
        plugin_catalog = plugins["cpp"]
        defaults = plugin_catalog.get("defaults", {})
        llvm_default = defaults.get("llvm", "22")
        params["cpp_llvm"] = {
            "name": "cpp_llvm",
            "display_name": "C/C++ LLVM Version",
            "type": "string",
            "form_type": "dropdown",
            "mutable": False,
            "default": llvm_default,
            "order": 41,
            "count": "data.coder_parameter.enable_cpp.value ? 1 : 0",
            "option": _version_options("LLVM", plugin_catalog.get("versions", []), llvm_default),
        }

    return params


def _all_parameter_specs(catalog: dict) -> dict[str, dict[str, Any]]:
    """Build all Coder parameters in display order."""
    extra_options = _make_extra_packs_options()
    plugins = catalog.get("plugins", {})
    params: dict[str, dict[str, Any]] = {
        "node_major": {
            "name": "node_major",
            "display_name": "Node.js",
            "type": "string",
            "form_type": "dropdown",
            "mutable": False,
            "default": _make_default_node_major(catalog),
            "order": 1,
            "option": _make_node_options(catalog),
        },
        "extra_extension_packs": {
            "name": "extra_extension_packs",
            "display_name": "Extra Extension Packs",
            "type": "list(string)",
            "form_type": "multi-select" if extra_options else "tag-select",
            "mutable": False,
            "default": [],
            "order": 50,
            "option": extra_options,
        },
    }
    enable_orders = {"python": 10, "go": 20, "rust": 30, "cpp": 40}
    descriptions = {
        "python": "Enable Python runtime and tools.",
        "go": "Enable Go runtime and tools.",
        "rust": "Enable Rust toolchain.",
        "cpp": "Enable C/C++ LLVM toolchain.",
    }
    for language in LANGUAGE_IDS:
        if language not in plugins:
            continue
        params[f"enable_{language}"] = {
            "name": f"enable_{language}",
            "display_name": f"Enable {LANGUAGE_LABELS[language]}",
            "description": descriptions[language],
            "type": "bool",
            "form_type": "checkbox",
            "mutable": False,
            "default": language == "python",
            "order": enable_orders[language],
        }
    params.update(_language_parameter_specs(catalog))
    return dict(sorted(params.items(), key=lambda item: int(item[1].get("order", 999))))


def _hcl_string(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _hcl_bool(value: object) -> str:
    return "true" if bool(value) else "false"


def _hcl_default(param: dict[str, Any]) -> str:
    value = param["default"]
    if param["type"] == "list(string)":
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = [value]
        else:
            parsed = value
        return f"jsonencode({json.dumps(parsed, ensure_ascii=False)})"
    if param["type"] == "bool":
        return _hcl_bool(value)
    return _hcl_string(value)


def _render_options(options: list[dict], indent: str = "  ") -> str:
    blocks = []
    for option in options:
        lines = [
            f"{indent}option {{",
            f"{indent}  name  = {_hcl_string(option.get('name', option.get('value', '')))}",
            f"{indent}  value = {_hcl_string(option.get('value', option.get('name', '')))}",
        ]
        if option.get("description"):
            lines.append(f"{indent}  description = {_hcl_string(option['description'])}")
        if option.get("icon"):
            lines.append(f"{indent}  icon = {_hcl_string(option['icon'])}")
        lines.append(f"{indent}}}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _render_parameter_hcl(block_name: str, param: dict[str, Any]) -> str:
    lines = [f'data "coder_parameter" "{block_name}" {{']
    if param.get("count"):
        lines.append(f"  count        = {param['count']}")
    lines.extend(
        [
            f"  name         = {_hcl_string(param['name'])}",
            f"  display_name = {_hcl_string(param['display_name'])}",
            f"  type         = {_hcl_string(param['type'])}",
            f"  form_type    = {_hcl_string(param['form_type'])}",
            f"  mutable      = {_hcl_bool(param['mutable'])}",
            f"  default      = {_hcl_default(param)}",
            f"  order        = {int(param['order'])}",
        ]
    )
    if param.get("description"):
        lines.append(f"  description  = {_hcl_string(param['description'])}")
    options = list(param.get("option", []))
    if options:
        lines.append("")
        lines.append(_render_options(options))
    lines.append("}")
    return "\n".join(lines)


def _render_parameters_hcl(params: dict[str, dict[str, Any]]) -> str:
    return "\n\n".join(_render_parameter_hcl(name, param) for name, param in params.items())


def _json_heredoc(name: str, value: object) -> str:
    payload = json.dumps(value, indent=2, sort_keys=True)
    return f"""  {name} = jsondecode(<<-JSON
{payload}
JSON
  )"""


def _startup_script_hcl() -> str:
    return f"""  startup_script_behavior = "blocking"

  startup_script = <<-EOT
    #!/usr/bin/env bash
    set -Eeuo pipefail

    log() {{
      printf '[codervps-startup] %s\\n' "$*"
    }}

    exec > >(tee -a /tmp/codervps-startup-debug.log) 2>&1

    export HOME="{HOME_DIR}"
    export CDEV_RUNTIME_ROOT="{CDEV_RUNTIME_ROOT}"
    export RUNTIME_LIB_DIR="/opt/cde/runtime/lib"
    export CDEV_SELECTION_JSON='${{jsonencode(local.cdev_selection)}}'

    mkdir -p "{PROJECT_DIR}" "$HOME/.config/code-server" "$CDEV_RUNTIME_ROOT"

    printf '%s\\n' \\
      'bind-addr: 0.0.0.0:13337' \\
      'auth: none' \\
      'cert: false' \\
      > "$HOME/.config/code-server/config.yaml"

    if command -v code-server >/dev/null 2>&1; then
      log "Starting code-server"
      code-server --version || true
      pkill -f 'code-server.*13337' >/dev/null 2>&1 || true
      nohup code-server \\
        --auth none \\
        --disable-telemetry \\
        --disable-update-check \\
        --bind-addr 0.0.0.0:13337 \\
        "{PROJECT_DIR}" \\
        > /tmp/code-server.log 2>&1 &
      for _ in $(seq 1 60); do
        if curl -fsS http://0.0.0.0:13337/healthz >/dev/null 2>&1; then
          log "code-server is healthy"
          break
        fi
        sleep 0.5
      done
      if ! curl -fsS http://0.0.0.0:13337/healthz >/dev/null 2>&1; then
        log "code-server did not become healthy"
        tail -n 80 /tmp/code-server.log >&2 || true
        exit 1
      fi
    else
      echo "code-server not found in PATH" >&2
      exit 1
    fi

    if [ -f /opt/cde/runtime/startup.sh ]; then
      log "Running CoderVPS runtime startup"
      bash /opt/cde/runtime/startup.sh
    fi
  EOT"""


def _render_enable_locals(catalog: dict) -> str:
    plugins = catalog.get("plugins", {})
    lines = []
    for language in LANGUAGE_IDS:
        if language in plugins:
            lines.append(
                f"  enable_{language}{' ' * (6 - len(language))}= "
                f"data.coder_parameter.enable_{language}.value"
            )
        else:
            lines.append(f"  enable_{language}{' ' * (6 - len(language))}= false")
    return "\n".join(lines)


def _render_selection_entries(catalog: dict) -> str:
    plugins = catalog.get("plugins", {})
    entries = []
    if "python" in plugins:
        entries.append(
            """    python = local.enable_python ? {
      version = data.coder_parameter.python_version[0].value
      tools   = jsondecode(data.coder_parameter.python_tools[0].value)
    } : null"""
        )
    else:
        entries.append("    python = null")
    if "go" in plugins:
        entries.append(
            """    go = local.enable_go ? {
      version = data.coder_parameter.go_version[0].value
      tools   = jsondecode(data.coder_parameter.go_tools[0].value)
    } : null"""
        )
    else:
        entries.append("    go = null")
    if "rust" in plugins:
        entries.append(
            """    rust = local.enable_rust ? {
      toolchain = data.coder_parameter.rust_toolchain[0].value
    } : null"""
        )
    else:
        entries.append("    rust = null")
    if "cpp" in plugins:
        entries.append(
            """    cpp = local.enable_cpp ? {
      llvm = data.coder_parameter.cpp_llvm[0].value
    } : null"""
        )
    else:
        entries.append("    cpp = null")
    return "\n".join(entries)


def render_main_tf_hcl(images: dict, catalog: dict) -> str:
    """Render a complete Coder `main.tf` HCL document."""
    params = _all_parameter_specs(catalog)
    images_list = images.get("images", [])

    return f"""terraform {{
  required_providers {{
    coder = {{
      source  = "coder/coder"
      version = "{CODER_PROVIDER_VERSION}"
    }}
    docker = {{
      source = "kreuzwerker/docker"
    }}
  }}
}}

provider "coder" {{}}
provider "docker" {{}}

data "coder_workspace" "me" {{}}
data "coder_workspace_owner" "me" {{}}
data "coder_provisioner" "me" {{}}

{_render_parameters_hcl(params)}

locals {{
{_json_heredoc("images", images_list)}

{_json_heredoc("catalog", catalog)}

  selected_image = one([
    for image in local.images :
    image.image
    if tostring(image.node_major) == data.coder_parameter.node_major.value
  ])

{_render_enable_locals(catalog)}

  selected_languages = compact([
    local.enable_python ? "python" : "",
    local.enable_go ? "go" : "",
    local.enable_rust ? "rust" : "",
    local.enable_cpp ? "cpp" : "",
  ])

  cdev_selection = {{
    node_major            = data.coder_parameter.node_major.value
    languages             = local.selected_languages
    extra_extension_packs = jsondecode(data.coder_parameter.extra_extension_packs.value)
{_render_selection_entries(catalog)}
  }}
}}

resource "docker_volume" "home" {{
  name = "coder-${{data.coder_workspace.me.id}}-home"

  lifecycle {{
    ignore_changes = all
  }}

  labels {{
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }}

  labels {{
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }}

  labels {{
    label = "coder.owner_id"
    value = data.coder_workspace_owner.me.id
  }}

  labels {{
    label = "coder.workspace_name_at_creation"
    value = data.coder_workspace.me.name
  }}
}}

resource "coder_agent" "main" {{
  arch = data.coder_provisioner.me.arch
  os   = "linux"

  display_apps {{
    vscode                 = true
    web_terminal           = true
    ssh_helper             = true
    port_forwarding_helper = true
  }}

  env = {{
    GIT_AUTHOR_NAME     = coalesce(data.coder_workspace_owner.me.full_name, data.coder_workspace_owner.me.name)
    GIT_AUTHOR_EMAIL    = data.coder_workspace_owner.me.email
    GIT_COMMITTER_NAME  = coalesce(data.coder_workspace_owner.me.full_name, data.coder_workspace_owner.me.name)
    GIT_COMMITTER_EMAIL = data.coder_workspace_owner.me.email
  }}

{_startup_script_hcl()}

  metadata {{
    display_name = "CPU Usage"
    key          = "0_cpu_usage"
    script       = "coder stat cpu"
    interval     = 10
    timeout      = 1
  }}

  metadata {{
    display_name = "RAM Usage"
    key          = "1_ram_usage"
    script       = "coder stat mem"
    interval     = 10
    timeout      = 1
  }}

  metadata {{
    display_name = "Home Disk"
    key          = "2_home_disk"
    script       = "coder stat disk --path {HOME_DIR}"
    interval     = 60
    timeout      = 1
  }}
}}

resource "coder_app" "code_server" {{
  count = data.coder_workspace.me.start_count

  agent_id     = coder_agent.main.id
  slug         = "code-server"
  display_name = "VS Code Web"
  icon         = "/icon/code.svg"

  url       = "http://127.0.0.1:13337/?folder={PROJECT_DIR}"
  share     = "owner"
  subdomain = false
  open_in   = "tab"
  order     = 1

  healthcheck {{
    url       = "http://127.0.0.1:13337/healthz"
    interval  = 3
    threshold = 20
  }}
}}

resource "docker_container" "workspace" {{
  count = data.coder_workspace.me.start_count

  image    = local.selected_image
  name     = "coder-${{data.coder_workspace.me.id}}"
  hostname = lower(data.coder_workspace.me.name)

  entrypoint = ["sh", "-c", replace(coder_agent.main.init_script, "/localhost|127\\\\.0\\\\.0\\\\.1/", "host.docker.internal")]
  env        = ["CODER_AGENT_TOKEN=${{coder_agent.main.token}}"]

  host {{
    host = "host.docker.internal"
    ip   = "host-gateway"
  }}

  volumes {{
    volume_name    = docker_volume.home.name
    container_path = "{HOME_DIR}"
    read_only      = false
  }}

  volumes {{
    host_path      = "/opt/coder-cde/templates/devbox/runtime"
    container_path = "/opt/cde/runtime"
    read_only      = true
  }}

  volumes {{
    host_path      = "/opt/coder-cde/extensions"
    container_path = "/opt/cde/extensions"
    read_only      = true
  }}

  volumes {{
    host_path      = "/opt/coder-cde/vsix"
    container_path = "/opt/cde/vsix"
    read_only      = true
  }}

  labels {{
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }}

  labels {{
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }}

  labels {{
    label = "coder.owner_id"
    value = data.coder_workspace_owner.me.id
  }}

  labels {{
    label = "coder.workspace_name"
    value = data.coder_workspace.me.name
  }}
}}
"""


def render_main_tf_json(images: dict, catalog: dict) -> dict:
    """Return a compatibility structure matching the HCL template semantics.

    New generated branches use `render_main_tf_hcl()`. This function remains so
    older unit tests and callers can inspect the same high-level template data
    without parsing HCL.
    """
    params = _all_parameter_specs(catalog)
    return {
        "terraform": {
            "required_providers": {
                "coder": {"source": "coder/coder", "version": CODER_PROVIDER_VERSION},
                "docker": {"source": "kreuzwerker/docker"},
            }
        },
        "provider": {"coder": [{}], "docker": [{}]},
        "data": {
            "coder_workspace": {"me": {}},
            "coder_workspace_owner": {"me": {}},
            "coder_provisioner": {"me": {}},
            "coder_parameter": params,
        },
        "resource": {
            "docker_volume": {
                "home": {
                    "name": "coder-${data.coder_workspace.me.id}-home",
                    "lifecycle": {"ignore_changes": "all"},
                    "labels": [
                        {"label": "coder.workspace_id", "value": "${data.coder_workspace.me.id}"},
                        {"label": "coder.owner", "value": "${data.coder_workspace_owner.me.name}"},
                        {
                            "label": "coder.owner_id",
                            "value": "${data.coder_workspace_owner.me.id}",
                        },
                    ],
                }
            },
            "coder_agent": {
                "main": {
                    "arch": "${data.coder_provisioner.me.arch}",
                    "os": "linux",
                    "display_apps": {
                        "vscode": True,
                        "web_terminal": True,
                        "ssh_helper": True,
                        "port_forwarding_helper": True,
                    },
                    "startup_script": "starts /opt/cde/runtime/startup.sh and code-server",
                }
            },
            "coder_app": {
                "code_server": {
                    "count": "${data.coder_workspace.me.start_count}",
                    "agent_id": "${coder_agent.main.id}",
                    "slug": "code-server",
                    "display_name": "VS Code Web",
                    "url": f"http://127.0.0.1:13337/?folder={PROJECT_DIR}",
                    "share": "owner",
                    "subdomain": False,
                    "open_in": "tab",
                }
            },
            "docker_container": {
                "workspace": {
                    "count": "${data.coder_workspace.me.start_count}",
                    "image": "${local.selected_image}",
                    "name": "coder-${data.coder_workspace.me.id}",
                    "entrypoint": [
                        "sh",
                        "-c",
                        '${replace(coder_agent.main.init_script, "/localhost|127\\\\.0\\\\.0\\\\.1/", "host.docker.internal")}',
                    ],
                    "env": ["CODER_AGENT_TOKEN=${coder_agent.main.token}"],
                    "host": [{"host": "host.docker.internal", "ip": "host-gateway"}],
                    "volumes": [
                        {
                            "container_path": HOME_DIR,
                            "volume_name": "${docker_volume.home.name}",
                            "read_only": False,
                        },
                        {
                            "host_path": "/opt/coder-cde/templates/devbox/runtime",
                            "container_path": "/opt/cde/runtime",
                            "read_only": True,
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
                        {
                            "label": "coder.owner_id",
                            "value": "${data.coder_workspace_owner.me.id}",
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
