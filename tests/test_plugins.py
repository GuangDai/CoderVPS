"""Tests for codervps.plugins -- registry, runtime plans, and parameter generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from codervps.config import load_toolchains_config
from codervps.models import RuntimePlan
from codervps.plugins import get_plugin, load_plugins
from codervps.plugins.cpp import CppPlugin
from codervps.plugins.go import GoPlugin
from codervps.plugins.python import PythonPlugin
from codervps.plugins.rust import RustPlugin


# ============================================================================
# Registry tests
# ============================================================================


def test_enabled_plugins_load_in_config_order():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    plugins = load_plugins(cfg.enabled_plugins)
    assert [p.id for p in plugins] == ["python", "rust", "go", "cpp"]


def test_load_single_plugin():
    plugin = load_plugins(["python"])
    assert len(plugin) == 1
    assert plugin[0].id == "python"
    assert plugin[0].label == "Python"


def test_load_plugins_unknown_raises_value_error():
    with pytest.raises(ValueError, match="unknown plugins"):
        load_plugins(["python", "ruby"])


def test_get_plugin_returns_instance():
    p = get_plugin("rust")
    assert p.id == "rust"
    assert p.label == "Rust"


def test_get_plugin_unknown_raises_value_error():
    with pytest.raises(ValueError, match="unknown plugin"):
        get_plugin("fortran")


def test_get_plugin_each_is_independent():
    a = get_plugin("python")
    b = get_plugin("python")
    assert a is not b  # separate instances


def test_load_plugins_preserves_order():
    plugins = load_plugins(["rust", "go", "python", "cpp"])
    assert [p.id for p in plugins] == ["rust", "go", "python", "cpp"]


# ============================================================================
# Python plugin runtime plans
# ============================================================================


def test_python_runtime_plan_uses_workspace_paths():
    plugin = PythonPlugin()
    plan = plugin.runtime_plan({"version": "3.13", "tools": ["ruff", "debugpy"]})
    assert isinstance(plan, RuntimePlan)
    assert plan.plugin == "python"
    # All paths in env vars are under /workspace/.cdev
    for val in plan.env.values():
        assert val.startswith("/workspace/.cdev")
    # ensure_dir actions use workspace paths
    for action in plan.actions:
        if action.type == "ensure_dir":
            path = str(action.values.get("path", ""))
            assert path.startswith("/workspace/.cdev")


def test_python_tools_are_individually_selectable():
    plugin = PythonPlugin()
    plan = plugin.runtime_plan({"version": "3.13", "tools": ["debugpy"]})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("uv tool install debugpy" in cmd for cmd in commands)
    assert not any("uv tool install ruff" in cmd for cmd in commands)


def test_python_ruff_only():
    plugin = PythonPlugin()
    plan = plugin.runtime_plan({"version": "3.12", "tools": ["ruff"]})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("uv tool install ruff" in cmd for cmd in commands)
    assert not any("debugpy" in cmd for cmd in commands)


def test_python_no_optional_tools():
    plugin = PythonPlugin()
    plan = plugin.runtime_plan({"version": "3.13", "tools": []})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert not any("uv tool install" in cmd for cmd in commands)


def test_python_all_tools():
    plugin = PythonPlugin()
    plan = plugin.runtime_plan(
        {"version": "3.13", "tools": ["ruff", "debugpy", "ipython", "jupyter"]}
    )
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("uv tool install ruff" in cmd for cmd in commands)
    assert any("uv tool install debugpy" in cmd for cmd in commands)
    assert any("uv tool install ipython" in cmd for cmd in commands)
    assert any("uv tool install jupyter" in cmd for cmd in commands)


def test_python_verify_action_exists():
    plugin = PythonPlugin()
    plan = plugin.runtime_plan({"version": "3.13"})
    verify = [a for a in plan.actions if a.type == "verify_command"]
    assert len(verify) >= 1
    assert verify[0].command[0] == "uv"


def test_python_tools_string_is_expanded():
    plugin = PythonPlugin()
    plan = plugin.runtime_plan({"version": "3.13", "tools": "ruff"})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("uv tool install ruff" in cmd for cmd in commands)


def test_python_env_vars_set():
    plugin = PythonPlugin()
    plan = plugin.runtime_plan({"version": "3.13"})
    assert "UV_CACHE_DIR" in plan.env
    assert "UV_PYTHON_INSTALL_DIR" in plan.env
    assert "UV_TOOL_DIR" in plan.env
    assert "UV_TOOL_BIN_DIR" in plan.env


# ============================================================================
# Rust plugin runtime plans
# ============================================================================


def test_rust_runtime_plan_installs_components():
    plugin = RustPlugin()
    plan = plugin.runtime_plan({"toolchain": "stable"})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("rustup toolchain install stable" in cmd for cmd in commands)
    assert any("rustup component add rustfmt clippy rust-src" in cmd for cmd in commands)


def test_rust_runtime_plan_default_toolchain():
    plugin = RustPlugin()
    plan = plugin.runtime_plan({})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("rustup toolchain install stable" in cmd for cmd in commands)


def test_rust_runtime_plan_custom_toolchain():
    plugin = RustPlugin()
    plan = plugin.runtime_plan({"toolchain": "nightly"})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("rustup toolchain install nightly" in cmd for cmd in commands)


def test_rust_env_vars_set():
    plugin = RustPlugin()
    plan = plugin.runtime_plan({"toolchain": "stable"})
    assert "RUSTUP_HOME" in plan.env
    assert "CARGO_HOME" in plan.env
    assert "SCCACHE_DIR" in plan.env
    assert "RUSTC_WRAPPER" in plan.env
    assert plan.env["RUSTC_WRAPPER"] == "sccache"


def test_rust_actions_are_critical():
    plugin = RustPlugin()
    plan = plugin.runtime_plan({"toolchain": "stable"})
    for action in plan.actions:
        if action.type in ("run", "verify_command", "download", "extract_tar"):
            assert action.critical is True, f"action {action.id} should be critical"


# ============================================================================
# Go plugin runtime plans
# ============================================================================


def test_go_runtime_plan_uses_selected_gopls_version():
    plugin = GoPlugin()
    plan = plugin.runtime_plan(
        {"version": "1.22.12", "tools": ["gopls"], "gopls_version": "v0.16.2"}
    )
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("golang.org/x/tools/gopls@v0.16.2" in cmd for cmd in commands)
    assert not any("golang.org/x/tools/gopls@latest" in cmd for cmd in commands)


def test_go_runtime_plan_has_download_and_extract():
    plugin = GoPlugin()
    plan = plugin.runtime_plan({"version": "1.22.12", "tools": ["gopls"]})
    action_types = {a.type for a in plan.actions}
    assert "download" in action_types
    assert "extract_tar" in action_types
    assert "path_prepend" in action_types


def test_go_runtime_plan_uses_sha256_when_provided():
    plugin = GoPlugin()
    plan = plugin.runtime_plan({"version": "1.22.12", "tools": [], "sha256": "abc123def456"})
    download = next(a for a in plan.actions if a.type == "download")
    assert download.values.get("sha256") == "abc123def456"


def test_go_runtime_plan_no_sha256_when_empty():
    plugin = GoPlugin()
    plan = plugin.runtime_plan({"version": "1.22.12", "tools": []})
    download = next(a for a in plan.actions if a.type == "download")
    assert download.values.get("sha256") is None


def test_go_download_url_format():
    plugin = GoPlugin()
    plan = plugin.runtime_plan({"version": "1.22.12", "tools": []})
    download = next(a for a in plan.actions if a.type == "download")
    assert "go1.22.12.linux-amd64.tar.gz" in str(download.values["url"])


def test_go_gopls_default_is_latest():
    plugin = GoPlugin()
    plan = plugin.runtime_plan({"version": "1.22.12", "tools": ["gopls"]})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("golang.org/x/tools/gopls@latest" in cmd for cmd in commands)


def test_go_extract_creates_flag():
    plugin = GoPlugin()
    plan = plugin.runtime_plan({"version": "1.22.12", "tools": []})
    extract = next(a for a in plan.actions if a.type == "extract_tar")
    assert extract.creates is not None
    assert extract.creates.endswith("/bin/go")


def test_go_env_vars_set():
    plugin = GoPlugin()
    plan = plugin.runtime_plan({"version": "1.22.12"})
    assert "GOROOT" in plan.env
    assert "GOBIN" in plan.env
    assert "GOCACHE" in plan.env
    assert "GOMODCACHE" in plan.env
    assert "GOPATH" in plan.env
    for val in plan.env.values():
        assert val.startswith("/workspace/.cdev")


# ============================================================================
# C/C++ plugin runtime plans
# ============================================================================


def test_cpp_runtime_plan_default_env():
    plugin = CppPlugin()
    plan = plugin.runtime_plan({})
    assert "CCACHE_DIR" in plan.env
    assert plan.env["CCACHE_DIR"].startswith("/workspace/.cdev")


def test_cpp_runtime_plan_has_path_prepend():
    plugin = CppPlugin()
    plan = plugin.runtime_plan({"llvm": "20"})
    pp_actions = [a for a in plan.actions if a.type == "path_prepend"]
    assert len(pp_actions) == 1
    assert "llvm/20" in str(pp_actions[0].values.get("path", ""))


def test_cpp_verify_clangd_is_non_critical():
    plugin = CppPlugin()
    plan = plugin.runtime_plan({"llvm": "latest"})
    verify = [a for a in plan.actions if a.type == "verify_command"]
    assert len(verify) == 1
    assert verify[0].critical is False


def test_cpp_uses_llvm_selection():
    plugin = CppPlugin()
    plan = plugin.runtime_plan({"llvm": "18"})
    assert plan.env["LLVM_VERSION"] == "18"
    pp = next(a for a in plan.actions if a.type == "path_prepend")
    assert "llvm/18" in str(pp.values["path"])


# ============================================================================
# Plugin class identity
# ============================================================================


def test_all_four_plugins_have_id_and_label():
    for cls in [PythonPlugin, RustPlugin, GoPlugin, CppPlugin]:
        instance = cls()
        assert isinstance(instance.id, str) and instance.id
        assert isinstance(instance.label, str) and instance.label
