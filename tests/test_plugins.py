"""Tests for codervps.plugins -- registry, runtime plans, and plugin protocol."""

from __future__ import annotations

from pathlib import Path

import pytest

from codervps.config import load_toolchains_config
from codervps.models import ParameterSpec, PluginCatalog, RuntimeAction, RuntimePlan
from codervps.plugins import load_plugins
from codervps.plugins.cpp import CppPlugin
from codervps.plugins.go import GoPlugin
from codervps.plugins.python import PythonPlugin
from codervps.plugins.rust import RustPlugin


GO_1_22_12_SHA256 = "4fa4f869b0f7fc6bb1eb2660e74657fbf04cdd290b5aef905585c86051b34d43"


def _go_selection(**overrides: object) -> dict:
    selection = {"version": "1.22.12", "sha256": GO_1_22_12_SHA256}
    selection.update(overrides)
    return selection


def _selection_for(plugin_id: str) -> dict:
    if plugin_id == "python":
        return {"version": "3.13"}
    if plugin_id == "rust":
        return {"toolchain": "stable"}
    if plugin_id == "go":
        return _go_selection()
    if plugin_id == "cpp":
        return {"llvm": "19"}
    raise AssertionError(f"unknown plugin id {plugin_id}")


# ---- Registry ----


def test_enabled_plugins_load_in_config_order():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    plugins = load_plugins(cfg.enabled_plugins)
    assert [p.id for p in plugins] == ["python", "rust", "go", "cpp"]


def test_load_plugins_returns_correct_types():
    plugins = load_plugins(["python", "rust", "go", "cpp"])
    assert isinstance(plugins[0], PythonPlugin)
    assert isinstance(plugins[1], RustPlugin)
    assert isinstance(plugins[2], GoPlugin)
    assert isinstance(plugins[3], CppPlugin)


def test_load_plugins_subset():
    plugins = load_plugins(["python", "go"])
    assert len(plugins) == 2
    assert plugins[0].id == "python"
    assert plugins[1].id == "go"


def test_load_plugins_single():
    plugins = load_plugins(["rust"])
    assert len(plugins) == 1
    assert plugins[0].id == "rust"


def test_load_plugins_unknown_raises():
    with pytest.raises(ValueError, match="unknown plugins"):
        load_plugins(["python", "nonexistent"])


def test_load_plugins_empty_list():
    plugins = load_plugins([])
    assert plugins == []


def test_load_plugins_all_unknown_raises():
    with pytest.raises(ValueError, match="unknown plugins"):
        load_plugins(["foo", "bar"])


# ---- Plugin IDs and Labels ----


def test_python_plugin_id_and_label():
    p = PythonPlugin()
    assert p.id == "python"
    assert p.label == "Python"


def test_rust_plugin_id_and_label():
    p = RustPlugin()
    assert p.id == "rust"
    assert p.label == "Rust"


def test_go_plugin_id_and_label():
    p = GoPlugin()
    assert p.id == "go"
    assert p.label == "Go"


def test_cpp_plugin_id_and_label():
    p = CppPlugin()
    assert p.id == "cpp"
    assert p.label == "C/C++"


# ---- Discover returns PluginCatalog ----


def test_python_discover_returns_catalog():
    p = PythonPlugin()
    cat = p.discover(fixture_dir="tests/fixtures")
    assert isinstance(cat, PluginCatalog)
    assert cat.plugin == "python"
    assert len(cat.versions) > 0
    assert cat.defaults["version"] == "3.13"


def test_rust_discover_returns_catalog():
    p = RustPlugin()
    cat = p.discover(fixture_dir="tests/fixtures")
    assert isinstance(cat, PluginCatalog)
    assert cat.plugin == "rust"
    assert len(cat.versions) > 0


def test_go_discover_returns_catalog():
    p = GoPlugin()
    cat = p.discover(fixture_dir="tests/fixtures")
    assert isinstance(cat, PluginCatalog)
    assert cat.plugin == "go"
    assert len(cat.versions) > 0


def test_go_discover_with_fixtures():
    p = GoPlugin()
    cat = p.discover(fixture_dir="tests/fixtures")
    assert isinstance(cat, PluginCatalog)
    assert len(cat.versions) >= 5
    version_values = [v.value for v in cat.versions]
    assert "1.24.9" in version_values
    assert "1.23.12" in version_values


def test_cpp_discover_returns_catalog():
    p = CppPlugin()
    cat = p.discover(fixture_dir="tests/fixtures")
    assert isinstance(cat, PluginCatalog)
    assert cat.plugin == "cpp"
    assert len(cat.versions) > 0


# ---- Coder parameters ----


def test_plugin_coder_parameters():
    for plugin in [PythonPlugin(), RustPlugin(), GoPlugin(), CppPlugin()]:
        cat = plugin.discover(fixture_dir="tests/fixtures")
        params = plugin.coder_parameters(cat)
        assert isinstance(params, list)
        for param in params:
            assert isinstance(param, ParameterSpec)
            assert param.name
            assert param.mutable is False


def test_python_coder_parameters_has_condition():
    p = PythonPlugin()
    cat = p.discover(fixture_dir="tests/fixtures")
    params = p.coder_parameters(cat)
    conditions = [param.condition for param in params if param.condition]
    assert any("python" in c for c in conditions if c)


def test_go_coder_parameters_has_condition():
    p = GoPlugin()
    cat = p.discover(fixture_dir="tests/fixtures")
    params = p.coder_parameters(cat)
    conditions = [param.condition for param in params if param.condition]
    assert any("go" in c for c in conditions if c)


# ---- Python runtime plan ----


def test_python_runtime_plan_uses_workspace_paths():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan({"version": "3.13", "tools": ["ruff", "debugpy"]})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("uv python install 3.13" in cmd for cmd in commands)
    all_values = [str(action.values) for action in plan.actions]
    all_envs = [str(action.env) for action in plan.actions]
    combined = " ".join(all_values) + " " + str(plan.env) + " " + " ".join(all_envs)
    assert "/workspace/.cdev" in combined


def test_python_tools_are_individually_selectable():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan({"version": "3.13", "tools": ["debugpy"]})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("uv tool install debugpy" in cmd for cmd in commands)
    assert not any("uv tool install ruff" in cmd for cmd in commands)


def test_python_runtime_plan_version_as_number():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan({"version": "3.12"})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("3.12" in cmd for cmd in commands)


def test_python_runtime_plan_no_tools():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan({"version": "3.13", "tools": []})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert not any("uv tool install" in cmd for cmd in commands)


def test_python_runtime_plan_all_optional_tools():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan(
        {"version": "3.13", "tools": ["ruff", "debugpy", "ipython", "jupyter"]}
    )
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("uv tool install ruff" in cmd for cmd in commands)
    assert any("uv tool install debugpy" in cmd for cmd in commands)
    assert any("uv tool install ipython" in cmd for cmd in commands)
    assert any("uv tool install jupyter" in cmd for cmd in commands)


def test_python_runtime_plan_env_vars():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan({"version": "3.13"})
    assert plan.env["UV_CACHE_DIR"] == "/workspace/.cdev/cache/uv"
    assert plan.env["UV_PYTHON_INSTALL_DIR"] == "/workspace/.cdev/toolchains/python"
    assert plan.env["UV_TOOL_DIR"] == "/workspace/.cdev/toolchains/python-tools"
    assert plan.env["UV_TOOL_BIN_DIR"] == "/workspace/.cdev/bin"


def test_python_runtime_plan_has_verify_action():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan({"version": "3.13"})
    verify_actions = [a for a in plan.actions if a.type == "verify_command"]
    assert len(verify_actions) > 0


def test_python_runtime_plan_has_ensure_dir_actions():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan({"version": "3.13"})
    dir_actions = [a for a in plan.actions if a.type == "ensure_dir"]
    assert len(dir_actions) > 0


def test_python_runtime_plan_has_path_prepend():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan({"version": "3.13"})
    path_actions = [a for a in plan.actions if a.type == "path_prepend"]
    assert len(path_actions) > 0


def test_python_runtime_plan_tools_as_string():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan({"version": "3.13", "tools": "ruff"})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("uv tool install ruff" in cmd for cmd in commands)


# ---- Rust runtime plan ----


def test_rust_runtime_plan_installs_components():
    plugin = load_plugins(["rust"])[0]
    plan = plugin.runtime_plan({"toolchain": "stable"})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("rustup toolchain install stable" in cmd for cmd in commands)
    assert any("rustup component add rustfmt clippy rust-src" in cmd for cmd in commands)


def test_rust_runtime_plan_env_vars():
    plugin = load_plugins(["rust"])[0]
    plan = plugin.runtime_plan({"toolchain": "stable"})
    assert plan.env["RUSTUP_HOME"] == "/workspace/.cdev/toolchains/rust/rustup"
    assert plan.env["CARGO_HOME"] == "/workspace/.cdev/toolchains/rust/cargo"
    assert plan.env["SCCACHE_DIR"] == "/workspace/.cdev/cache/sccache"
    assert plan.env["RUSTC_WRAPPER"] == "sccache"


def test_rust_runtime_plan_different_toolchains():
    plugin = load_plugins(["rust"])[0]
    for tc in ["stable", "beta", "nightly"]:
        plan = plugin.runtime_plan({"toolchain": tc})
        commands = [" ".join(action.command) for action in plan.actions if action.command]
        assert any(tc in cmd for cmd in commands)


def test_rust_runtime_plan_has_verify():
    plugin = load_plugins(["rust"])[0]
    plan = plugin.runtime_plan({"toolchain": "stable"})
    verify_actions = [a for a in plan.actions if a.type == "verify_command"]
    assert len(verify_actions) > 0


def test_rust_runtime_plan_uses_default_component():
    plugin = load_plugins(["rust"])[0]
    plan = plugin.runtime_plan({})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("rustup toolchain install stable" in cmd for cmd in commands)


def test_rust_runtime_plan_isolation():
    plugin = load_plugins(["rust"])[0]
    plan = plugin.runtime_plan({"toolchain": "stable"})
    all_paths = str(plan.env) + str(plan.actions)
    assert "/opt/cde/cache" not in all_paths
    assert "/workspace/.cdev" in all_paths


# ---- Go runtime plan ----


def test_go_runtime_plan_uses_selected_gopls_version():
    plugin = load_plugins(["go"])[0]
    plan = plugin.runtime_plan(
        _go_selection(
            tools=["gopls"],
            gopls_version="v0.16.2",
        )
    )
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("golang.org/x/tools/gopls@v0.16.2" in cmd for cmd in commands)
    assert not any("golang.org/x/tools/gopls@latest" in cmd for cmd in commands)


def test_go_runtime_plan_download_and_extract():
    plugin = load_plugins(["go"])[0]
    plan = plugin.runtime_plan(_go_selection(tools=["gopls"]))
    action_types = [a.type for a in plan.actions]
    assert "download" in action_types
    assert "extract_tar" in action_types


def test_go_runtime_plan_download_url():
    plugin = load_plugins(["go"])[0]
    plan = plugin.runtime_plan(_go_selection())
    dl = [a for a in plan.actions if a.type == "download"][0]
    assert "go1.22.12.linux-amd64.tar.gz" in dl.values["url"]


def test_go_runtime_plan_requires_real_sha256_when_downloading():
    plugin = load_plugins(["go"])[0]
    sha256 = GO_1_22_12_SHA256
    plan = plugin.runtime_plan(_go_selection(sha256=sha256))
    dl = [a for a in plan.actions if a.type == "download"][0]
    assert dl.values["sha256"] == sha256
    assert "auto" not in str(dl.values)


def test_go_runtime_plan_missing_sha256_fails_fast():
    plugin = load_plugins(["go"])[0]
    with pytest.raises(ValueError, match="sha256"):
        plugin.runtime_plan({"version": "1.22.12"})


def test_go_runtime_plan_env_vars():
    plugin = load_plugins(["go"])[0]
    plan = plugin.runtime_plan(_go_selection())
    assert plan.env["GOROOT"] == "/workspace/.cdev/toolchains/go/1.22.12"
    assert plan.env["GOBIN"] == "/workspace/.cdev/toolchains/go/bin"
    assert plan.env["GOCACHE"] == "/workspace/.cdev/cache/go/build"
    assert plan.env["GOMODCACHE"] == "/workspace/.cdev/cache/go/pkg/mod"
    assert plan.env["GOPATH"] == "/workspace/.cdev/cache/go/gopath"


def test_go_runtime_plan_extract_creates():
    plugin = load_plugins(["go"])[0]
    plan = plugin.runtime_plan(_go_selection())
    extract = [a for a in plan.actions if a.type == "extract_tar"][0]
    assert extract.creates is not None
    assert "/bin/go" in extract.creates


def test_go_runtime_plan_no_tools():
    plugin = load_plugins(["go"])[0]
    plan = plugin.runtime_plan(_go_selection(tools=[]))
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert not any("golang.org/x/tools/gopls" in cmd for cmd in commands)
    assert not any("github.com/go-delve" in cmd for cmd in commands)


def test_go_runtime_plan_with_dlv():
    plugin = load_plugins(["go"])[0]
    plan = plugin.runtime_plan(
        _go_selection(
            tools=["gopls", "dlv"],
            dlv_version="v1.23.0",
        )
    )
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("dlv@v1.23.0" in cmd for cmd in commands)


def test_go_runtime_plan_path_prepend_actions():
    plugin = load_plugins(["go"])[0]
    plan = plugin.runtime_plan(_go_selection())
    path_actions = [a for a in plan.actions if a.type == "path_prepend"]
    assert len(path_actions) >= 2


def test_go_runtime_plan_tools_as_string():
    plugin = load_plugins(["go"])[0]
    plan = plugin.runtime_plan(_go_selection(tools="gopls"))
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("golang.org/x/tools/gopls" in cmd for cmd in commands)


# ---- C/C++ runtime plan ----


def test_cpp_runtime_plan_uses_llvm():
    plugin = load_plugins(["cpp"])[0]
    plan = plugin.runtime_plan({"llvm": "19"})
    env_paths = str(plan.env) + str(plan.actions)
    assert "/workspace/.cdev/toolchains/llvm/19" in env_paths


def test_cpp_runtime_plan_env_vars():
    plugin = load_plugins(["cpp"])[0]
    plan = plugin.runtime_plan({"llvm": "19"})
    assert plan.env["CCACHE_DIR"] == "/workspace/.cdev/cache/ccache"


def test_cpp_runtime_plan_default_llvm():
    plugin = load_plugins(["cpp"])[0]
    plan = plugin.runtime_plan({})
    env_paths = str(plan.env) + str(plan.actions)
    assert "/workspace/.cdev" in env_paths


def test_cpp_runtime_plan_has_ensure_dir():
    plugin = load_plugins(["cpp"])[0]
    plan = plugin.runtime_plan({"llvm": "19"})
    dir_actions = [a for a in plan.actions if a.type == "ensure_dir"]
    assert len(dir_actions) > 0


def test_cpp_runtime_plan_has_verify():
    plugin = load_plugins(["cpp"])[0]
    plan = plugin.runtime_plan({"llvm": "19"})
    verify_actions = [a for a in plan.actions if a.type == "verify_command"]
    assert len(verify_actions) > 0


def test_cpp_prebundled_no_path_prepend():
    plugin = load_plugins(["cpp"])[0]
    plan = plugin.runtime_plan({"llvm": "19"})
    path_actions = [a for a in plan.actions if a.type == "path_prepend"]
    assert len(path_actions) == 0


def test_cpp_non_prebundled_has_path_prepend():
    plugin = load_plugins(["cpp"])[0]
    plan = plugin.runtime_plan({"llvm": "18"})
    path_actions = [a for a in plan.actions if a.type == "path_prepend"]
    assert len(path_actions) > 0


# ---- Runtime plan structural tests ----


def test_all_plugins_return_runtime_plan():
    plugins = load_plugins(["python", "rust", "go", "cpp"])
    for plugin in plugins:
        plan = plugin.runtime_plan(_selection_for(plugin.id))
        assert isinstance(plan, RuntimePlan)
        assert plan.plugin == plugin.id
        assert isinstance(plan.actions, list)
        assert len(plan.actions) > 0


def test_all_plugins_actions_have_ids():
    plugins = load_plugins(["python", "rust", "go", "cpp"])
    for plugin in plugins:
        plan = plugin.runtime_plan(_selection_for(plugin.id))
        for action in plan.actions:
            assert isinstance(action, RuntimeAction)
            assert action.id, f"empty action id in {plugin.id}"
            assert action.type, f"empty action type in {plugin.id}"


def test_all_plugins_action_ids_are_unique():
    plugins = load_plugins(["python", "rust", "go", "cpp"])
    for plugin in plugins:
        plan = plugin.runtime_plan(_selection_for(plugin.id))
        ids = [a.id for a in plan.actions]
        assert len(ids) == len(set(ids)), f"duplicate action ids in {plugin.id}: {ids}"


def test_all_plugins_no_shared_cache_root():
    plugins = load_plugins(["python", "rust", "go", "cpp"])
    for plugin in plugins:
        plan = plugin.runtime_plan(_selection_for(plugin.id))
        text = str(plan.env) + str(plan.actions)
        assert "/opt/cde/cache" not in text, f"{plugin.id} references shared cache"


def test_runtime_plans_do_not_emit_auto_placeholders():
    plugins = load_plugins(["python", "rust", "go", "cpp"])
    selections = {
        "python": {"version": "3.13"},
        "rust": {"toolchain": "stable"},
        "go": {
            "version": "1.22.12",
            "sha256": "4fa4f869b0f7fc6bb1eb2660e74657fbf04cdd290b5aef905585c86051b34d43",
        },
        "cpp": {"llvm": "22"},
    }
    for plugin in plugins:
        plan = plugin.runtime_plan(selections[plugin.id])
        assert "auto" not in str(plan)


def test_all_plugins_workspace_cdev_in_all_actions():
    plugins = load_plugins(["python", "rust", "go", "cpp"])
    for plugin in plugins:
        plan = plugin.runtime_plan(_selection_for(plugin.id))
        for action in plan.actions:
            text = (
                str(action.values)
                + str(action.env)
                + str(action.command)
                + str(action.creates or "")
            )
            if action.type in (
                "download",
                "extract_tar",
                "ensure_dir",
                "path_prepend",
                "symlink",
                "write_file",
            ):
                assert "/workspace/.cdev" in text, (
                    f"{plugin.id} action {action.id} ({action.type}) missing workspace path"
                )
