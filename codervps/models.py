from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ActionType = Literal[
    "ensure_dir",
    "download",
    "extract_tar",
    "run",
    "path_prepend",
    "env",
    "symlink",
    "write_file",
    "verify_command",
]


@dataclass(frozen=True)
class ToolchainsConfig:
    project_arch: str
    node_majors: list[int]
    enabled_plugins: list[str]
    overrides: dict[str, str]
    python_min_minor: str
    python_max_minor: str
    python_default: str
    python_default_tools: list[str]
    rust_stable_minor_count: int
    rust_default: str
    rust_components: list[str]
    rust_use_sccache: bool
    go_minor_count: int
    go_default: str
    go_default_tools: list[str]
    cpp_default_llvm: str
    cpp_prebundle: str
    cpp_default_tools: list[str]


@dataclass(frozen=True)
class ExtensionPack:
    label: str
    marketplace: list[str] = field(default_factory=list)
    vsix_globs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExtensionsConfig:
    core_marketplace: list[str]
    language_marketplace: dict[str, list[str]]
    packs: dict[str, ExtensionPack]


@dataclass(frozen=True)
class VersionEntry:
    value: str
    label: str
    status: str = "supported"
    default: bool = False
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PluginCatalog:
    plugin: str
    versions: list[VersionEntry]
    defaults: dict[str, str]


@dataclass(frozen=True)
class RuntimeAction:
    id: str
    type: ActionType
    critical: bool = True
    creates: str | None = None
    command: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    values: dict[str, str | int | bool | list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimePlan:
    plugin: str
    actions: list[RuntimeAction]
    env: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    display_name: str
    type: str
    form_type: str
    default: str
    mutable: bool
    order: int
    options: list[VersionEntry] = field(default_factory=list)
    count: str | None = None
