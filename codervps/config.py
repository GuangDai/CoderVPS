from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # pragma: no cover

from .models import ExtensionPack, ExtensionsConfig, ToolchainsConfig


def _fail(message: str) -> None:
    """Report a configuration error and exit."""
    print(f"config error: {message}", file=sys.stderr)
    raise SystemExit(1)


def _require_str(raw: dict[str, Any], key: str, section: str) -> str:
    """Get a required string value from a dict, calling _fail if missing or wrong type."""
    if key not in raw:
        _fail(f"missing required key '{key}' in [{section}]")
    value = raw[key]
    if not isinstance(value, str):
        _fail(f"expected string for '{key}' in [{section}], got {type(value).__name__}")
    return value


def _get_str(raw: dict[str, Any], key: str, default: str) -> str:
    """Get an optional string value with a default."""
    value = raw.get(key, default)
    if not isinstance(value, str):
        return default
    return value


def _require_list(raw: dict[str, Any], key: str, section: str) -> list[Any]:
    """Get a required list from a dict, calling _fail if missing or wrong type."""
    if key not in raw:
        _fail(f"missing required key '{key}' in [{section}]")
    value = raw[key]
    if not isinstance(value, list):
        _fail(f"expected list for '{key}' in [{section}], got {type(value).__name__}")
    return value


def _get_list_str(
    raw: dict[str, Any], key: str, *, required: bool = False, section: str = ""
) -> list[str]:
    """Get a list of strings, optionally required."""
    if key not in raw:
        if required:
            _fail(f"missing required key '{key}' in [{section}]")
        return []
    value = raw[key]
    if not isinstance(value, list):
        _fail(f"expected list for '{key}' in [{section}], got {type(value).__name__}")
    return [str(v) for v in value]


def _get_int(raw: dict[str, Any], key: str, default: int) -> int:
    """Get an integer value with a default."""
    value = raw.get(key, default)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return default


def _get_bool(raw: dict[str, Any], key: str, default: bool) -> bool:
    """Get a boolean value with a default."""
    value = raw.get(key, default)
    if isinstance(value, bool):
        return value
    return default


def _read_toml(path: Path) -> dict[str, Any]:
    """Read a TOML file, calling _fail if it cannot be parsed."""
    if not path.exists():
        _fail(f"config file not found: {path}")
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except (OSError, ValueError) as exc:
        _fail(f"failed to read {path}: {exc}")


def load_toolchains_config(path: Path) -> ToolchainsConfig:
    """Load and validate toolchains configuration from a TOML file."""
    raw = _read_toml(path)

    # Project section
    project = raw.get("project")
    if not isinstance(project, dict):
        _fail("missing or invalid [project] section")
    project_arch = _require_str(project, "arch", "project")

    # Node section
    node = raw.get("node")
    if not isinstance(node, dict):
        _fail("missing or invalid [node] section")
    node_majors = [int(v) for v in _require_list(node, "majors", "node")]

    # Plugins section
    plugins = raw.get("plugins")
    if not isinstance(plugins, dict):
        _fail("missing or invalid [plugins] section")
    enabled_plugins = _get_list_str(plugins, "enabled", required=True, section="plugins")

    # Versions section
    versions = raw.get("versions")
    if not isinstance(versions, dict):
        _fail("missing or invalid [versions] section")
    overrides_section = versions.get("override")
    if not isinstance(overrides_section, dict):
        overrides = {}
    else:
        overrides = {str(k): str(v) for k, v in overrides_section.items()}

    # Python section
    python = raw.get("python")
    if not isinstance(python, dict):
        _fail("missing or invalid [python] section")
    python_min_minor = _require_str(python, "min_minor", "python")
    python_max_minor = _require_str(python, "max_minor", "python")
    python_default = _require_str(python, "default", "python")
    python_default_tools = _get_list_str(python, "default_tools", required=True, section="python")

    # Rust section
    rust = raw.get("rust")
    if not isinstance(rust, dict):
        _fail("missing or invalid [rust] section")
    rust_stable_minor_count = _get_int(rust, "stable_minor_count", 30)
    rust_default = _require_str(rust, "default", "rust")
    rust_components = _get_list_str(rust, "default_components", required=True, section="rust")
    rust_use_sccache = _get_bool(rust, "use_sccache", True)

    # Go section
    go = raw.get("go")
    if not isinstance(go, dict):
        _fail("missing or invalid [go] section")
    go_minor_count = _get_int(go, "minor_count", 20)
    go_default = _require_str(go, "default", "go")
    go_default_tools = _get_list_str(go, "default_tools", required=True, section="go")

    # C/C++ section
    cpp = raw.get("cpp")
    if not isinstance(cpp, dict):
        _fail("missing or invalid [cpp] section")
    cpp_default_llvm = _require_str(cpp, "default_llvm", "cpp")
    cpp_prebundle = _require_str(cpp, "prebundle", "cpp")
    cpp_default_tools = _get_list_str(cpp, "default_tools", required=True, section="cpp")

    return ToolchainsConfig(
        project_arch=project_arch,
        node_majors=node_majors,
        enabled_plugins=enabled_plugins,
        overrides=overrides,
        python_min_minor=python_min_minor,
        python_max_minor=python_max_minor,
        python_default=python_default,
        python_default_tools=python_default_tools,
        rust_stable_minor_count=rust_stable_minor_count,
        rust_default=rust_default,
        rust_components=rust_components,
        rust_use_sccache=rust_use_sccache,
        go_minor_count=go_minor_count,
        go_default=go_default,
        go_default_tools=go_default_tools,
        cpp_default_llvm=cpp_default_llvm,
        cpp_prebundle=cpp_prebundle,
        cpp_default_tools=cpp_default_tools,
    )


def load_extensions_config(path: Path) -> ExtensionsConfig:
    """Load and validate extensions configuration from a TOML file."""
    raw = _read_toml(path)

    # Core section
    core = raw.get("core")
    if not isinstance(core, dict):
        _fail("missing or invalid [core] section")
    core_marketplace = _get_list_str(core, "marketplace", required=True, section="core")

    # Language sections
    language_raw = raw.get("language")
    language: dict[str, list[str]] = {}
    if isinstance(language_raw, dict):
        for name, section in language_raw.items():
            if isinstance(section, dict):
                language[name] = _get_list_str(section, "marketplace", section=f"language.{name}")

    # Packs section
    packs_raw = raw.get("packs")
    packs: dict[str, ExtensionPack] = {}
    if isinstance(packs_raw, dict):
        for name, section in packs_raw.items():
            if isinstance(section, dict):
                label = _get_str(section, "label", name)
                marketplace = _get_list_str(section, "marketplace", section=f"packs.{name}")
                vsix_globs = _get_list_str(section, "vsix_globs", section=f"packs.{name}")
                packs[name] = ExtensionPack(
                    label=label,
                    marketplace=marketplace,
                    vsix_globs=vsix_globs,
                )

    return ExtensionsConfig(
        core_marketplace=core_marketplace,
        language_marketplace=language,
        packs=packs,
    )
