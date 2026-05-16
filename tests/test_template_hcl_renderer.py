"""Tests for the Coder-native HCL template renderer."""

from __future__ import annotations

from codervps.render.template import render_main_tf_hcl


def _catalog() -> dict:
    return {
        "node": {
            "majors": {
                "24": {"version": "24.11.1"},
                "22": {"version": "22.21.0"},
            }
        },
        "plugins": {
            "python": {
                "defaults": {"version": "cpython@3.13.13"},
                "versions": [
                    {
                        "label": "CPython 3.13.13",
                        "request": "cpython@3.13.13",
                        "status": "active",
                    },
                    {
                        "label": "CPython 3.13.13 free-threaded",
                        "request": "cpython@3.13.13+freethreaded",
                        "status": "supported",
                    },
                ],
            },
            "rust": {
                "defaults": {"toolchain": "stable"},
                "versions": [{"version": "stable", "status": "active"}],
            },
            "go": {
                "defaults": {"version": "1.24.9"},
                "versions": [
                    {
                        "version": "1.24.9",
                        "status": "active",
                        "sha256": "a" * 64,
                    }
                ],
            },
            "cpp": {
                "defaults": {"llvm": "22"},
                "versions": [{"version": "22", "status": "active"}],
            },
        },
    }


def test_hcl_uses_supported_dynamic_parameter_shape():
    text = render_main_tf_hcl(images={"images": []}, catalog=_catalog())

    assert 'version = ">= 2.5.3"' in text
    assert 'data "coder_parameter" "languages"' not in text
    assert '"condition"' not in text
    assert "condition =" not in text
    assert "contains(data.coder_parameter.languages.value" not in text
    assert 'data "coder_parameter" "enable_python"' in text
    assert 'type         = "bool"' in text
    assert 'form_type    = "checkbox"' in text
    assert "count        = data.coder_parameter.enable_python.value ? 1 : 0" in text


def test_hcl_dropdowns_and_multiselects_have_option_blocks():
    text = render_main_tf_hcl(images={"images": []}, catalog=_catalog())

    assert 'form_type    = "dropdown"' in text
    assert 'form_type    = "multi-select"' in text
    assert "option {" in text
    assert 'value = "cpython@3.13.13+freethreaded"' in text
    assert 'value = "gopls"' in text


def test_hcl_uses_coder_native_home_persistence_and_agent_startup():
    text = render_main_tf_hcl(
        images={"images": [{"node_major": 24, "image": "ghcr.io/example/devbox:node24"}]},
        catalog=_catalog(),
    )

    assert 'resource "docker_volume" "home"' in text
    assert 'container_path = "/home/coder"' in text
    assert 'dir = "/workspace"' not in text
    assert 'entrypoint = ["sh", "-c", replace(coder_agent.main.init_script' in text
    assert "CODER_AGENT_TOKEN=${coder_agent.main.token}" in text
    assert "display_apps {" in text
    assert "web_terminal           = true" in text
    assert "ssh_helper             = true" in text


def test_hcl_code_server_app_opens_tab_without_command_conflict():
    text = render_main_tf_hcl(images={"images": []}, catalog=_catalog())

    app_start = text.index('resource "coder_app" "code_server"')
    app_end = text.index('resource "docker_container" "workspace"')
    app = text[app_start:app_end]
    assert 'open_in   = "tab"' in app
    assert 'url       = "http://127.0.0.1:13337/?folder=/home/coder/workspace"' in app
    assert "command =" not in app
    assert "healthcheck {" in app


def test_hcl_startup_script_starts_code_server_from_agent():
    text = render_main_tf_hcl(images={"images": []}, catalog=_catalog())

    assert "code-server \\" in text
    assert "--auth none" in text
    assert "--bind-addr 127.0.0.1:13337" in text
    assert '"/home/coder/workspace"' in text
    assert 'export CDEV_RUNTIME_ROOT="/home/coder/.cdev"' in text


def test_hcl_starts_code_server_before_runtime_bootstrap():
    text = render_main_tf_hcl(images={"images": []}, catalog=_catalog())

    code_server_start = text.index("Starting code-server")
    runtime_start = text.index("Running CoderVPS runtime startup")
    assert code_server_start < runtime_start


def test_hcl_code_server_startup_has_health_diagnostics():
    text = render_main_tf_hcl(images={"images": []}, catalog=_catalog())

    assert "code-server did not become healthy" in text
    assert "tail -n 80 /tmp/code-server.log" in text
    assert "curl -fsS http://127.0.0.1:13337/healthz" in text


def test_hcl_code_server_config_does_not_use_nested_shell_heredoc():
    text = render_main_tf_hcl(images={"images": []}, catalog=_catalog())

    assert "<<'YAML'" not in text
    assert "printf '%s\\n'" in text
    assert "bind-addr: 127.0.0.1:13337" in text
