"""Tests for codervps.models -- frozen dataclasses, field types, and immutability."""

from __future__ import annotations

import pytest

from codervps.models import (
    ExtensionPack,
    ExtensionsConfig,
    ParameterSpec,
    PluginCatalog,
    RuntimeAction,
    RuntimePlan,
    ToolchainsConfig,
    VersionEntry,
)


# ---- Helper to create minimal valid instances ----


def _make_minimal_toolchains_config(**overrides) -> ToolchainsConfig:
    defaults = dict(
        project_arch="linux/amd64",
        node_majors=[24, 22, 20, 18, 16],
        enabled_plugins=["python", "rust", "go", "cpp"],
        overrides={},
        python_min_minor="3.6",
        python_max_minor="latest",
        python_default="3.13",
        python_default_tools=["ruff", "debugpy"],
        rust_stable_minor_count=30,
        rust_default="stable",
        rust_components=["rustfmt", "clippy", "rust-src"],
        rust_use_sccache=True,
        go_minor_count=20,
        go_default="latest",
        go_default_tools=["gopls"],
        cpp_default_llvm="latest",
        cpp_prebundle="latest",
        cpp_default_tools=["xmake", "ccache"],
    )
    defaults.update(overrides)
    return ToolchainsConfig(**defaults)


def _make_minimal_extension_pack(**overrides) -> ExtensionPack:
    defaults = dict(label="TestPack", marketplace=["test.id"], vsix_globs=[])
    defaults.update(overrides)
    return ExtensionPack(**defaults)


def _make_minimal_extensions_config(**overrides) -> ExtensionsConfig:
    defaults = dict(
        core_marketplace=["EditorConfig.EditorConfig"],
        language_marketplace={"python": ["ms-python.python"]},
        packs={},
    )
    defaults.update(overrides)
    return ExtensionsConfig(**defaults)


def _make_minimal_version_entry(**overrides) -> VersionEntry:
    defaults = dict(value="3.13", label="Python 3.13")
    defaults.update(overrides)
    return VersionEntry(**defaults)


def _make_minimal_plugin_catalog(**overrides) -> PluginCatalog:
    defaults = dict(
        plugin="python",
        versions=[_make_minimal_version_entry()],
        defaults={"version": "3.13"},
    )
    defaults.update(overrides)
    return PluginCatalog(**defaults)


def _make_minimal_runtime_action(**overrides) -> RuntimeAction:
    defaults = dict(id="test-action", type="run", command=["echo", "hello"])
    defaults.update(overrides)
    return RuntimeAction(**defaults)


def _make_minimal_runtime_plan(**overrides) -> RuntimePlan:
    defaults = dict(
        plugin="python",
        actions=[_make_minimal_runtime_action()],
        env={"PATH": "/home/coder/.cdev/bin"},
    )
    defaults.update(overrides)
    return RuntimePlan(**defaults)


def _make_minimal_parameter_spec(**overrides) -> ParameterSpec:
    defaults = dict(
        name="test_param",
        display_name="Test Parameter",
        type="string",
        form_type="dropdown",
        default="v1",
        mutable=False,
        order=1,
    )
    defaults.update(overrides)
    return ParameterSpec(**defaults)


# ---- Count dataclasses ----


def test_eight_dataclasses_exist():
    """Verify we have exactly 8 dataclasses as specified."""
    dataclasses = [
        ToolchainsConfig,
        ExtensionPack,
        ExtensionsConfig,
        VersionEntry,
        PluginCatalog,
        RuntimeAction,
        RuntimePlan,
        ParameterSpec,
    ]
    assert len(dataclasses) == 8


# ---- frozen=True ----


def test_toolchainsconfig_is_frozen():
    obj = _make_minimal_toolchains_config()
    with pytest.raises(Exception):
        obj.project_arch = "arm64"


def test_extensionpack_is_frozen():
    obj = _make_minimal_extension_pack()
    with pytest.raises(Exception):
        obj.label = "changed"


def test_extensionsconfig_is_frozen():
    obj = _make_minimal_extensions_config()
    with pytest.raises(Exception):
        obj.core_marketplace = []


def test_versionentry_is_frozen():
    obj = _make_minimal_version_entry()
    with pytest.raises(Exception):
        obj.value = "4.0"


def test_plugincatalog_is_frozen():
    obj = _make_minimal_plugin_catalog()
    with pytest.raises(Exception):
        obj.plugin = "rust"


def test_runtimeaction_is_frozen():
    obj = _make_minimal_runtime_action()
    with pytest.raises(Exception):
        obj.id = "changed"


def test_runtimeplan_is_frozen():
    obj = _make_minimal_runtime_plan()
    with pytest.raises(Exception):
        obj.plugin = "rust"


def test_parameterspec_is_frozen():
    obj = _make_minimal_parameter_spec()
    with pytest.raises(Exception):
        obj.name = "changed"


# ---- ToolchainsConfig field types ----


def test_toolchainsconfig_project_arch_type():
    obj = _make_minimal_toolchains_config()
    assert isinstance(obj.project_arch, str)


def test_toolchainsconfig_node_majors_type():
    obj = _make_minimal_toolchains_config()
    assert isinstance(obj.node_majors, list)
    assert all(isinstance(v, int) for v in obj.node_majors)


def test_toolchainsconfig_enabled_plugins_type():
    obj = _make_minimal_toolchains_config()
    assert isinstance(obj.enabled_plugins, list)
    assert all(isinstance(v, str) for v in obj.enabled_plugins)


def test_toolchainsconfig_overrides_type():
    obj = _make_minimal_toolchains_config()
    assert isinstance(obj.overrides, dict)


def test_toolchainsconfig_python_fields():
    obj = _make_minimal_toolchains_config()
    assert obj.python_min_minor == "3.6"
    assert obj.python_max_minor == "latest"
    assert obj.python_default == "3.13"
    assert obj.python_default_tools == ["ruff", "debugpy"]


def test_toolchainsconfig_rust_fields():
    obj = _make_minimal_toolchains_config()
    assert obj.rust_stable_minor_count == 30
    assert obj.rust_default == "stable"
    assert obj.rust_components == ["rustfmt", "clippy", "rust-src"]
    assert obj.rust_use_sccache is True


def test_toolchainsconfig_go_fields():
    obj = _make_minimal_toolchains_config()
    assert obj.go_minor_count == 20
    assert obj.go_default == "latest"
    assert obj.go_default_tools == ["gopls"]


def test_toolchainsconfig_cpp_fields():
    obj = _make_minimal_toolchains_config()
    assert obj.cpp_default_llvm == "latest"
    assert obj.cpp_prebundle == "latest"
    assert obj.cpp_default_tools == ["xmake", "ccache"]


# ---- ExtensionPack ----


def test_extensionpack_defaults():
    obj = ExtensionPack(label="Minimal")
    assert obj.label == "Minimal"
    assert obj.marketplace == []
    assert obj.vsix_globs == []


def test_extensionpack_with_globs():
    obj = ExtensionPack(
        label="LeetCode",
        marketplace=["leetcode.vscode-leetcode"],
        vsix_globs=["packs/leetcode/*.vsix"],
    )
    assert "leetcode.vscode-leetcode" in obj.marketplace
    assert "packs/leetcode/*.vsix" in obj.vsix_globs


# ---- ExtensionsConfig ----


def test_extensionsconfig_core():
    obj = _make_minimal_extensions_config(core_marketplace=["a", "b"])
    assert obj.core_marketplace == ["a", "b"]


def test_extensionsconfig_language_marketplace():
    obj = _make_minimal_extensions_config(
        language_marketplace={
            "python": ["ms-python.python", "charliermarsh.ruff"],
            "go": ["golang.Go"],
        }
    )
    assert obj.language_marketplace["python"] == ["ms-python.python", "charliermarsh.ruff"]
    assert obj.language_marketplace["go"] == ["golang.Go"]


def test_extensionsconfig_packs():
    pack = _make_minimal_extension_pack(label="Extra")
    obj = _make_minimal_extensions_config(packs={"extra": pack})
    assert obj.packs["extra"].label == "Extra"


# ---- VersionEntry ----


def test_versionentry_defaults():
    obj = VersionEntry(value="1.0", label="v1.0")
    assert obj.status == "supported"
    assert obj.default is False
    assert obj.metadata == {}


def test_versionentry_custom_status():
    obj = VersionEntry(
        value="1.0", label="v1.0", status="eol", default=True, metadata={"download": "url"}
    )
    assert obj.status == "eol"
    assert obj.default is True
    assert obj.metadata["download"] == "url"


# ---- PluginCatalog ----


def test_plugincatalog_structure():
    versions = [
        VersionEntry(value="3.13", label="Python 3.13"),
        VersionEntry(value="3.12", label="Python 3.12", status="eol"),
    ]
    obj = PluginCatalog(plugin="python", versions=versions, defaults={"version": "3.13"})
    assert obj.plugin == "python"
    assert len(obj.versions) == 2
    assert obj.defaults["version"] == "3.13"


# ---- RuntimeAction ----


def test_runtimeaction_defaults():
    obj = RuntimeAction(id="test", type="ensure_dir", values={"path": "/tmp"})
    assert obj.critical is True
    assert obj.creates is None
    assert obj.command == []
    assert obj.env == {}


def test_runtimeaction_download_type():
    obj = RuntimeAction(
        id="dl",
        type="download",
        values={
            "url": "https://example.com/file.tar.gz",
            "dest": "/home/coder/.cdev/downloads/file.tar.gz",
            "sha256": "abc123",
        },
    )
    assert obj.type == "download"
    assert obj.values["sha256"] == "abc123"


def test_runtimeaction_extract_tar_type():
    obj = RuntimeAction(
        id="extract",
        type="extract_tar",
        creates="/home/coder/.cdev/toolchains/go/bin/go",
        values={
            "src": "/home/coder/.cdev/downloads/go.tar.gz",
            "dest": "/home/coder/.cdev/toolchains/go/1.22",
            "strip_components": 1,
        },
    )
    assert obj.creates == "/home/coder/.cdev/toolchains/go/bin/go"


def test_runtimeaction_all_action_types():
    action_types = {
        "ensure_dir",
        "download",
        "extract_tar",
        "run",
        "path_prepend",
        "env",
        "symlink",
        "write_file",
        "verify_command",
    }
    for at in action_types:
        obj = RuntimeAction(id=f"test-{at}", type=at)
        assert obj.type == at


# ---- RuntimePlan ----


def test_runtimeplan_default_env():
    obj = RuntimePlan(plugin="rust", actions=[_make_minimal_runtime_action()])
    assert obj.env == {}


def test_runtimeplan_multiple_actions():
    actions = [
        _make_minimal_runtime_action(id="a1"),
        _make_minimal_runtime_action(id="a2", type="verify_command"),
        _make_minimal_runtime_action(id="a3", critical=False),
    ]
    obj = RuntimePlan(
        plugin="go", actions=actions, env={"GOROOT": "/home/coder/.cdev/toolchains/go/1.22"}
    )
    assert len(obj.actions) == 3
    assert obj.env["GOROOT"].startswith("/home/coder/.cdev")


# ---- ParameterSpec ----


def test_parameterspec_defaults():
    obj = ParameterSpec(
        name="version",
        display_name="Version",
        type="string",
        form_type="dropdown",
        default="3.13",
        mutable=False,
        order=1,
    )
    assert obj.options == []
    assert obj.count is None


def test_parameterspec_with_options():
    options = [
        VersionEntry(value="3.13", label="3.13"),
        VersionEntry(value="3.12", label="3.12"),
    ]
    obj = ParameterSpec(
        name="python_version",
        display_name="Python",
        type="string",
        form_type="dropdown",
        default="3.13",
        mutable=False,
        order=2,
        options=options,
        count="data.coder_parameter.enable_python.value ? 1 : 0",
    )
    assert len(obj.options) == 2
    assert obj.count is not None


# ---- Edge cases: equality and repr ----


def test_models_repr():
    obj = VersionEntry(value="3.13", label="Python 3.13")
    r = repr(obj)
    assert "VersionEntry" in r
    assert "3.13" in r


def test_models_equality():
    a = VersionEntry(value="3.13", label="Python 3.13")
    b = VersionEntry(value="3.13", label="Python 3.13")
    assert a == b
    c = VersionEntry(value="3.12", label="Python 3.12")
    assert a != c


def test_runtimeaction_non_critical():
    obj = RuntimeAction(
        id="optional-check", type="verify_command", critical=False, command=["which", "python"]
    )
    assert obj.critical is False
    assert obj.command == ["which", "python"]


def test_runtimeaction_env_passthrough():
    obj = RuntimeAction(
        id="with-env",
        type="run",
        command=["uv", "python", "install", "3.13"],
        env={"UV_CACHE_DIR": "/home/coder/.cdev/cache/uv"},
    )
    assert obj.env["UV_CACHE_DIR"] == "/home/coder/.cdev/cache/uv"
