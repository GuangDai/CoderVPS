# CoderVPS Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the pluginized Python generator, generated Coder template output, GitHub Actions image publishing flow, isolated workspace runtime, and thin `cdev` helper described in `docs/superpowers/specs/2026-05-12-codervps-refactor-design.md`.

**Architecture:** `main` contains source code, config, Dockerfile, runtime shell modules, tests, and workflows. The Python generator renders catalogs and a publishable template tree for the `generated` branch. Runtime setup installs selected language versions into a workspace-specific `/workspace/.cdev` tree and never shares toolchains or caches across workspaces.

**Tech Stack:** Python 3.11+, uv, pytest, ruff, stdlib `tomllib`/`json`, Bash runtime modules, Terraform JSON syntax, Docker Buildx, GitHub Actions, GHCR, Coder Terraform provider, Docker Terraform provider.

---

## File Structure

Create or modify these source files on `main`:

- Modify: `pyproject.toml` to use Python `>=3.11`, expose `codervps`, and add pytest/ruff dev tools.
- Delete with `/bin/rm`: `main.py` after `codervps/cli.py` exists.
- Create: `codervps/__init__.py` package metadata.
- Create: `codervps/__main__.py` CLI entrypoint.
- Create: `codervps/cli.py` argument parsing and command dispatch.
- Create: `codervps/models.py` dataclasses for catalogs, parameters, image requirements, runtime actions, and generated manifests.
- Create: `codervps/config.py` TOML loading and typed config normalization.
- Create: `codervps/plugin_api.py` `ToolchainPlugin` Protocol.
- Create: `codervps/plugins/__init__.py` registry.
- Create: `codervps/plugins/python.py`, `rust.py`, `go.py`, `cpp.py`.
- Create: `codervps/discovery.py` upstream metadata clients with injectable fixtures.
- Create: `codervps/catalog.py` catalog refresh orchestration.
- Create: `codervps/render/template.py` Terraform `main.tf.json` renderer.
- Create: `codervps/render/extensions.py` extension list and VSIX directory renderer.
- Create: `codervps/render/runtime.py` runtime file copier and selection/action-plan writer.
- Create: `codervps/render/docker.py` Docker build context and matrix renderer.
- Create: `codervps/render/generated.py` full generated-tree orchestrator.
- Create: `config/toolchains.toml` source toolchain config.
- Create: `config/extensions.toml` source extension config.
- Create: `docker/Dockerfile` source Dockerfile template.
- Create: `runtime/startup.sh`, `runtime/lib/actions.sh`, `runtime/lib/extensions.sh`.
- Create: `runtime/lib/run_actions.py`.
- Create: `runtime/plugins/python.sh`, `runtime/plugins/rust.sh`, `runtime/plugins/go.sh`, `runtime/plugins/cpp.sh`.
- Create: `tests/fixtures/*.json` deterministic upstream metadata fixtures.
- Create: `tests/test_*.py` unit and golden tests.
- Create: `.github/workflows/generate.yml` monthly/manual generator and image workflow.
- Modify: `cdev` into a thin VPS helper.
- Modify: `README.md` with operator workflow.

Generated output is not committed to `main`. Tests may render into `build/generated` and compare selected files.
Any `/bin/rm` instructions in this plan are execution rules for the agent/operator
performing repository changes on this VPS. They are not product implementation
requirements for generated scripts, Dockerfiles, workflows, or `cdev`.

## Task 1: Python Project Baseline

**Files:**
- Modify: `pyproject.toml`
- Create: `codervps/__init__.py`
- Create: `codervps/__main__.py`
- Create: `codervps/cli.py`
- Test: `tests/test_cli.py`
- Delete: `main.py` with `/bin/rm main.py`

- [ ] **Step 1: Write the failing CLI test**

Create `tests/test_cli.py`:

```python
from codervps.cli import main


def test_main_version(capsys):
    rc = main(["--version"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert out == "codervps 0.1.0"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/test_cli.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'codervps'`.

- [ ] **Step 3: Update `pyproject.toml`**

Replace the file with:

```toml
[project]
name = "codervps"
version = "0.1.0"
description = "Pluginized generator and runtime assets for CoderVPS workspaces"
readme = "README.md"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
codervps = "codervps.cli:main"

[dependency-groups]
dev = [
  "pytest>=8.3.0",
  "ruff>=0.8.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 4: Create the package files**

Create `codervps/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `codervps/__main__.py`:

```python
from .cli import main

raise SystemExit(main())
```

Create `codervps/cli.py`:

```python
from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codervps")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("validate", help="validate source configuration and generated assets")
    sub.add_parser("refresh-catalog", help="refresh toolchain catalog")
    sub.add_parser("render-generated", help="render the generated branch tree")
    sub.add_parser("build-matrix", help="print Docker image build matrix")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"codervps {__version__}")
        return 0
    if args.command is None:
        parser.print_help()
        return 0
    raise SystemExit(f"command not implemented yet: {args.command}")
```

- [ ] **Step 5: Remove the uv sample file**

Run:

```bash
/bin/rm main.py
```

Expected: `main.py` is gone.

- [ ] **Step 6: Run tests and lint**

Run:

```bash
uv sync
uv run pytest tests/test_cli.py -q
uv run ruff check codervps tests
```

Expected: pytest passes; ruff reports no issues.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml codervps tests .python-version
git add -u main.py
git commit -m "feat: add codervps cli package"
```

## Task 2: Core Models And Config Loader

**Files:**
- Create: `codervps/models.py`
- Create: `codervps/config.py`
- Create: `config/toolchains.toml`
- Create: `config/extensions.toml`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
from pathlib import Path

from codervps.config import load_extensions_config, load_toolchains_config


def test_load_toolchains_config():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    assert cfg.project_arch == "linux/amd64"
    assert cfg.node_majors == [24, 22, 20, 18, 16]
    assert cfg.enabled_plugins == ["python", "rust", "go", "cpp"]
    assert cfg.python_default_tools == ["ruff", "debugpy"]
    assert cfg.rust_components == ["rustfmt", "clippy", "rust-src"]
    assert cfg.go_minor_count == 20


def test_load_extensions_config():
    cfg = load_extensions_config(Path("config/extensions.toml"))
    assert "EditorConfig.EditorConfig" in cfg.core_marketplace
    assert cfg.language_marketplace["python"] == [
        "ms-python.python",
        "ms-python.debugpy",
        "charliermarsh.ruff",
    ]
    assert cfg.packs["leetcode"].label == "LeetCode"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
uv run pytest tests/test_config.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `codervps.config`.

- [ ] **Step 3: Add source config files**

Create `config/toolchains.toml`:

```toml
[project]
arch = "linux/amd64"

[node]
majors = [24, 22, 20, 18, 16]

[plugins]
enabled = ["python", "rust", "go", "cpp"]

[versions.override]
uv = ""
code_server = ""
sccache = ""
rust_bootstrap = ""
llvm_prebundle = ""

[python]
min_minor = "3.6"
max_minor = "latest"
default = "3.13"
default_tools = ["ruff", "debugpy"]
optional_tools = ["ipython", "jupyter"]

[rust]
stable_minor_count = 30
default = "stable"
default_components = ["rustfmt", "clippy", "rust-src"]
use_sccache = true

[go]
minor_count = 20
default = "latest"
default_tools = ["gopls"]

[cpp]
default_llvm = "latest"
prebundle = "latest"
default_tools = ["xmake", "ccache"]
```

Create `config/extensions.toml`:

```toml
[core]
marketplace = ["EditorConfig.EditorConfig", "redhat.vscode-yaml"]

[language.python]
marketplace = ["ms-python.python", "ms-python.debugpy", "charliermarsh.ruff"]

[language.rust]
marketplace = ["rust-lang.rust-analyzer", "vadimcn.vscode-lldb"]

[language.go]
marketplace = ["golang.Go"]

[language.cpp]
marketplace = [
  "llvm-vs-code-extensions.vscode-clangd",
  "vadimcn.vscode-lldb",
  "tboox.xmake-vscode"
]

[packs.leetcode]
label = "LeetCode"
marketplace = ["leetcode.vscode-leetcode"]
vsix_globs = ["packs/leetcode/*.vsix"]
```

- [ ] **Step 4: Create model dataclasses**

Create `codervps/models.py` with:

```python
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
    condition: str | None = None
```

- [ ] **Step 5: Create config loader**

Create `codervps/config.py` with:

```python
from __future__ import annotations

from pathlib import Path
import tomllib

from .models import ExtensionPack, ExtensionsConfig, ToolchainsConfig


def _read_toml(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def load_toolchains_config(path: Path) -> ToolchainsConfig:
    raw = _read_toml(path)
    return ToolchainsConfig(
        project_arch=raw["project"]["arch"],
        node_majors=[int(v) for v in raw["node"]["majors"]],
        enabled_plugins=list(raw["plugins"]["enabled"]),
        overrides=dict(raw["versions"]["override"]),
        python_min_minor=raw["python"]["min_minor"],
        python_max_minor=raw["python"]["max_minor"],
        python_default=raw["python"]["default"],
        python_default_tools=list(raw["python"]["default_tools"]),
        rust_stable_minor_count=int(raw["rust"]["stable_minor_count"]),
        rust_default=raw["rust"]["default"],
        rust_components=list(raw["rust"]["default_components"]),
        rust_use_sccache=bool(raw["rust"]["use_sccache"]),
        go_minor_count=int(raw["go"]["minor_count"]),
        go_default=raw["go"]["default"],
        go_default_tools=list(raw["go"]["default_tools"]),
        cpp_default_llvm=raw["cpp"]["default_llvm"],
        cpp_prebundle=raw["cpp"]["prebundle"],
        cpp_default_tools=list(raw["cpp"]["default_tools"]),
    )


def load_extensions_config(path: Path) -> ExtensionsConfig:
    raw = _read_toml(path)
    language = {
        name: list(section.get("marketplace", []))
        for name, section in raw.get("language", {}).items()
    }
    packs = {
        name: ExtensionPack(
            label=section["label"],
            marketplace=list(section.get("marketplace", [])),
            vsix_globs=list(section.get("vsix_globs", [])),
        )
        for name, section in raw.get("packs", {}).items()
    }
    return ExtensionsConfig(
        core_marketplace=list(raw["core"]["marketplace"]),
        language_marketplace=language,
        packs=packs,
    )
```

- [ ] **Step 6: Run tests**

Run:

```bash
uv run pytest tests/test_config.py -q
uv run ruff check codervps tests
```

Expected: tests pass; ruff passes.

- [ ] **Step 7: Commit**

```bash
git add codervps config tests/test_config.py
git commit -m "feat: add source configuration models"
```

## Task 3: Plugin API And Static Plugin Runtime Plans

**Files:**
- Create: `codervps/plugin_api.py`
- Create: `codervps/plugins/__init__.py`
- Create: `codervps/plugins/python.py`
- Create: `codervps/plugins/rust.py`
- Create: `codervps/plugins/go.py`
- Create: `codervps/plugins/cpp.py`
- Test: `tests/test_plugins.py`

- [ ] **Step 1: Write failing plugin tests**

Create `tests/test_plugins.py`:

```python
from pathlib import Path

from codervps.config import load_toolchains_config
from codervps.plugins import load_plugins


def test_enabled_plugins_load_in_config_order():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    plugins = load_plugins(cfg.enabled_plugins)
    assert [p.id for p in plugins] == ["python", "rust", "go", "cpp"]


def test_python_runtime_plan_uses_workspace_paths():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan({"version": "3.13", "tools": ["ruff", "debugpy"]})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("uv python install 3.13" in cmd for cmd in commands)
    assert all("/workspace/.cdev" in str(action.values) or action.type == "run" for action in plan.actions)


def test_python_tools_are_individually_selectable():
    plugin = load_plugins(["python"])[0]
    plan = plugin.runtime_plan({"version": "3.13", "tools": ["debugpy"]})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("uv tool install debugpy" in cmd for cmd in commands)
    assert not any("uv tool install ruff" in cmd for cmd in commands)


def test_rust_runtime_plan_installs_components():
    plugin = load_plugins(["rust"])[0]
    plan = plugin.runtime_plan({"toolchain": "stable"})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("rustup toolchain install stable" in cmd for cmd in commands)
    assert any("rustup component add rustfmt clippy rust-src" in cmd for cmd in commands)


def test_go_runtime_plan_uses_selected_gopls_version():
    plugin = load_plugins(["go"])[0]
    plan = plugin.runtime_plan({"version": "1.22.12", "tools": ["gopls"], "gopls_version": "v0.16.2"})
    commands = [" ".join(action.command) for action in plan.actions if action.command]
    assert any("golang.org/x/tools/gopls@v0.16.2" in cmd for cmd in commands)
    assert not any("golang.org/x/tools/gopls@latest" in cmd for cmd in commands)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
uv run pytest tests/test_plugins.py -q
```

Expected: FAIL with missing `codervps.plugins`.

- [ ] **Step 3: Implement plugin API**

Create `codervps/plugin_api.py`:

```python
from __future__ import annotations

from typing import Protocol

from .models import ParameterSpec, PluginCatalog, RuntimePlan


class ToolchainPlugin(Protocol):
    id: str
    label: str

    def discover(self) -> PluginCatalog:
        raise NotImplementedError

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        raise NotImplementedError

    def runtime_plan(self, selection: dict[str, str | list[str]]) -> RuntimePlan:
        raise NotImplementedError
```

- [ ] **Step 4: Implement registry**

Create `codervps/plugins/__init__.py`:

```python
from __future__ import annotations

from codervps.plugin_api import ToolchainPlugin

from .cpp import CppPlugin
from .go import GoPlugin
from .python import PythonPlugin
from .rust import RustPlugin

_PLUGIN_TYPES = {
    "python": PythonPlugin,
    "rust": RustPlugin,
    "go": GoPlugin,
    "cpp": CppPlugin,
}


def load_plugins(enabled: list[str]) -> list[ToolchainPlugin]:
    missing = [name for name in enabled if name not in _PLUGIN_TYPES]
    if missing:
        raise ValueError(f"unknown plugins: {', '.join(missing)}")
    return [_PLUGIN_TYPES[name]() for name in enabled]
```

- [ ] **Step 5: Implement first plugin runtime plans**

Create `codervps/plugins/python.py`:

```python
from __future__ import annotations

from codervps.models import RuntimeAction, RuntimePlan


class PythonPlugin:
    id = "python"
    label = "Python"

    def discover(self):
        raise NotImplementedError("catalog discovery is implemented in Task 4")

    def coder_parameters(self, catalog):
        return []

    def runtime_plan(self, selection):
        version = str(selection["version"])
        tools = selection.get("tools", ["ruff", "debugpy"])
        if isinstance(tools, str):
            tools = [tools]
        actions = [
            RuntimeAction(
                id="python-cache",
                type="ensure_dir",
                values={"path": "/workspace/.cdev/cache/uv"},
            ),
            RuntimeAction(
                id="python-install",
                type="run",
                command=[
                    "uv",
                    "python",
                    "install",
                    version,
                    "--install-dir",
                    "/workspace/.cdev/toolchains/python",
                ],
            ),
            RuntimeAction(
                id="python-verify",
                type="verify_command",
                command=["uv", "python", "find", version],
            ),
        ]
        if "ruff" in tools:
            actions.append(RuntimeAction(id="python-tool-ruff", type="run", command=["uv", "tool", "install", "ruff"]))
        if "debugpy" in tools:
            actions.append(RuntimeAction(id="python-tool-debugpy", type="run", command=["uv", "tool", "install", "debugpy"]))
        if "ipython" in tools:
            actions.extend(
                [
                    RuntimeAction(id="python-tool-ipython", type="run", command=["uv", "tool", "install", "ipython"]),
                ]
            )
        if "jupyter" in tools:
            actions.extend(
                [
                    RuntimeAction(id="python-tool-jupyter", type="run", command=["uv", "tool", "install", "jupyter"]),
                ]
            )
        return RuntimePlan(
            plugin=self.id,
            actions=actions,
            env={
                "UV_CACHE_DIR": "/workspace/.cdev/cache/uv",
                "UV_PYTHON_INSTALL_DIR": "/workspace/.cdev/toolchains/python",
                "UV_TOOL_DIR": "/workspace/.cdev/toolchains/python-tools",
                "UV_TOOL_BIN_DIR": "/workspace/.cdev/bin",
            },
        )
```

Create `codervps/plugins/rust.py`:

```python
from __future__ import annotations

from codervps.models import RuntimeAction, RuntimePlan


class RustPlugin:
    id = "rust"
    label = "Rust"

    def discover(self):
        raise NotImplementedError("catalog discovery is implemented in Task 4")

    def coder_parameters(self, catalog):
        return []

    def runtime_plan(self, selection):
        toolchain = str(selection["toolchain"])
        return RuntimePlan(
            plugin=self.id,
            env={
                "RUSTUP_HOME": "/workspace/.cdev/toolchains/rust/rustup",
                "CARGO_HOME": "/workspace/.cdev/toolchains/rust/cargo",
                "CARGO_INSTALL_ROOT": "/workspace/.cdev/toolchains/rust/cargo-install",
                "SCCACHE_DIR": "/workspace/.cdev/cache/sccache",
                "RUSTC_WRAPPER": "sccache",
            },
            actions=[
                RuntimeAction(id="rust-cache", type="ensure_dir", values={"path": "/workspace/.cdev/cache/sccache"}),
                RuntimeAction(id="rust-install", type="run", command=["rustup", "toolchain", "install", toolchain, "--profile", "minimal"]),
                RuntimeAction(id="rust-components", type="run", command=["rustup", "component", "add", "rustfmt", "clippy", "rust-src", "--toolchain", toolchain]),
                RuntimeAction(id="rust-default", type="run", command=["rustup", "default", toolchain]),
                RuntimeAction(id="rust-verify", type="verify_command", command=["rustc", "--version"]),
            ],
        )
```

Create `codervps/plugins/go.py`:

```python
from __future__ import annotations

from codervps.models import RuntimeAction, RuntimePlan


class GoPlugin:
    id = "go"
    label = "Go"

    def discover(self):
        raise NotImplementedError("catalog discovery is implemented in Task 4")

    def coder_parameters(self, catalog):
        return []

    def runtime_plan(self, selection):
        version = str(selection["version"])
        tools = selection.get("tools", ["gopls"])
        if isinstance(tools, str):
            tools = [tools]
        gopls_version = str(selection.get("gopls_version", "latest"))
        dlv_version = str(selection.get("dlv_version", "latest"))
        root = f"/workspace/.cdev/toolchains/go/{version}"
        tarball = f"/workspace/.cdev/downloads/go{version}.linux-amd64.tar.gz"
        actions = [
            RuntimeAction(id="go-download", type="download", values={"url": f"https://go.dev/dl/go{version}.linux-amd64.tar.gz", "dest": tarball}),
            RuntimeAction(id="go-extract", type="extract_tar", creates=f"{root}/bin/go", values={"src": tarball, "dest": root, "strip_components": 1}),
            RuntimeAction(id="go-path", type="path_prepend", values={"path": f"{root}/bin"}),
            RuntimeAction(id="go-verify", type="verify_command", command=["go", "version"]),
        ]
        if "gopls" in tools:
            actions.append(RuntimeAction(id="go-tool-gopls", type="run", command=["go", "install", f"golang.org/x/tools/gopls@{gopls_version}"]))
        if "dlv" in tools:
            actions.append(RuntimeAction(id="go-tool-dlv", type="run", command=["go", "install", f"github.com/go-delve/delve/cmd/dlv@{dlv_version}"]))
        return RuntimePlan(
            plugin=self.id,
            actions=actions,
            env={
                "GOROOT": root,
                "GOBIN": "/workspace/.cdev/toolchains/go/bin",
                "GOCACHE": "/workspace/.cdev/cache/go/build",
                "GOMODCACHE": "/workspace/.cdev/cache/go/pkg/mod",
                "GOPATH": "/workspace/.cdev/cache/go/gopath",
            },
        )
```

Create `codervps/plugins/cpp.py`:

```python
from __future__ import annotations

from codervps.models import RuntimeAction, RuntimePlan


class CppPlugin:
    id = "cpp"
    label = "C/C++"

    def discover(self):
        raise NotImplementedError("catalog discovery is implemented in Task 4")

    def coder_parameters(self, catalog):
        return []

    def runtime_plan(self, selection):
        llvm = str(selection.get("llvm", "latest"))
        root = f"/workspace/.cdev/toolchains/llvm/{llvm}"
        return RuntimePlan(
            plugin=self.id,
            env={"CCACHE_DIR": "/workspace/.cdev/cache/ccache"},
            actions=[
                RuntimeAction(id="cpp-cache", type="ensure_dir", values={"path": "/workspace/.cdev/cache/ccache"}),
                RuntimeAction(id="cpp-llvm-dir", type="ensure_dir", values={"path": root}),
                RuntimeAction(id="cpp-path", type="path_prepend", values={"path": f"{root}/usr/bin"}),
                RuntimeAction(id="cpp-verify", type="verify_command", command=["clangd", "--version"], critical=False),
            ],
        )
```

- [ ] **Step 6: Run tests**

Run:

```bash
uv run pytest tests/test_plugins.py -q
uv run ruff check codervps tests
```

Expected: tests pass; ruff passes.

- [ ] **Step 7: Commit**

```bash
git add codervps/plugins codervps/plugin_api.py tests/test_plugins.py
git commit -m "feat: add toolchain plugin interface"
```

## Task 4: Catalog Refresh With Deterministic Fixtures

**Files:**
- Create: `codervps/discovery.py`
- Create: `codervps/catalog.py`
- Create: `tests/fixtures/node-index.json`
- Create: `tests/fixtures/go-dl.json`
- Test: `tests/test_catalog.py`

- [ ] **Step 1: Write failing catalog tests**

Create `tests/test_catalog.py`:

```python
from pathlib import Path

from codervps.catalog import refresh_catalog
from codervps.config import load_toolchains_config


def test_refresh_catalog_from_fixtures():
    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))
    assert catalog["schema_version"] == 1
    assert catalog["arch"] == "linux/amd64"
    assert sorted(catalog["node"]["majors"]) == ["16", "18", "20", "22", "24"]
    assert "python" in catalog["plugins"]
    assert "rust" in catalog["plugins"]
    assert "go" in catalog["plugins"]
    assert "cpp" in catalog["plugins"]
```

- [ ] **Step 2: Add compact fixtures**

Create `tests/fixtures/node-index.json`:

```json
[
  {"version": "v24.11.1", "lts": "Krypton"},
  {"version": "v22.21.0", "lts": "Jod"},
  {"version": "v20.19.5", "lts": "Iron"},
  {"version": "v18.20.8", "lts": "Hydrogen"},
  {"version": "v16.20.2", "lts": "Gallium"}
]
```

Create `tests/fixtures/go-dl.json`:

```json
[
  {
    "version": "go1.26.3",
    "stable": true,
    "files": [{"filename": "go1.26.3.linux-amd64.tar.gz", "sha256": "sha-go-1263"}]
  },
  {
    "version": "go1.25.5",
    "stable": true,
    "files": [{"filename": "go1.25.5.linux-amd64.tar.gz", "sha256": "sha-go-1255"}]
  },
  {
    "version": "go1.24.9",
    "stable": true,
    "files": [{"filename": "go1.24.9.linux-amd64.tar.gz", "sha256": "sha-go-1249"}]
  },
  {
    "version": "go1.23.12",
    "stable": true,
    "files": [{"filename": "go1.23.12.linux-amd64.tar.gz", "sha256": "sha-go-12312"}]
  }
]
```

- [ ] **Step 3: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_catalog.py -q
```

Expected: FAIL with missing `codervps.catalog`.

- [ ] **Step 4: Implement fixture-backed discovery**

Create `codervps/discovery.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen


def load_json(path: Path) -> object:
    return json.loads(path.read_text())


def fetch_json(url: str) -> object:
    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def node_index(fixture_dir: Path | None = None) -> list[dict]:
    if fixture_dir:
        return list(load_json(fixture_dir / "node-index.json"))
    return list(fetch_json("https://nodejs.org/dist/index.json"))


def go_downloads(fixture_dir: Path | None = None) -> list[dict]:
    if fixture_dir:
        return list(load_json(fixture_dir / "go-dl.json"))
    return list(fetch_json("https://go.dev/dl/?mode=json&include=all"))
```

Create `codervps/catalog.py` with this structure:

```python
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from .discovery import go_downloads, node_index
from .models import ToolchainsConfig


def _latest_node_patch(index: list[dict], major: int) -> str:
    prefix = f"v{major}."
    for entry in index:
        version = str(entry["version"])
        if version.startswith(prefix):
            return version.removeprefix("v")
    raise ValueError(f"missing Node major {major}")


def _node_status(major: int) -> str:
    if major == 24:
        return "active_lts"
    if major == 22:
        return "maintenance_lts"
    return "eol"


def refresh_catalog(cfg: ToolchainsConfig, fixture_dir: Path | None = None) -> dict:
    nodes = node_index(fixture_dir)
    go_downloads(fixture_dir)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "arch": cfg.project_arch,
        "base": {
            "source": "codercom/example-base",
            "ubuntu": "noble",
            "tag": "ubuntu-noble-20260511",
        },
        "node": {
            "majors": {
                str(major): {
                    "version": _latest_node_patch(nodes, major),
                    "status": _node_status(major),
                }
                for major in cfg.node_majors
            }
        },
        "plugins": {
            "python": {"versions": [], "defaults": {"version": cfg.python_default}},
            "rust": {"versions": [], "defaults": {"toolchain": cfg.rust_default}},
            "go": {"versions": [], "defaults": {"version": cfg.go_default}},
            "cpp": {"versions": [], "defaults": {"llvm": cfg.cpp_default_llvm}},
        },
        "tools": {
            "uv": {"version": cfg.overrides.get("uv") or "auto"},
            "code_server": {"version": cfg.overrides.get("code_server") or "auto"},
            "sccache": {
                "version": cfg.overrides.get("sccache") or "auto",
                "sha256": "resolved-sccache-release-sha256",
            },
            "llvm_prebundle": {"version": cfg.overrides.get("llvm_prebundle") or "auto"},
        },
    }
```

- [ ] **Step 5: Run tests**

Run:

```bash
uv run pytest tests/test_catalog.py tests/test_plugins.py tests/test_config.py -q
uv run ruff check codervps tests
```

Expected: tests pass; ruff passes.

- [ ] **Step 6: Commit**

```bash
git add codervps/discovery.py codervps/catalog.py tests/fixtures tests/test_catalog.py
git commit -m "feat: add deterministic catalog refresh"
```

## Task 5: Generated Terraform JSON Renderer

**Files:**
- Create: `codervps/render/__init__.py`
- Create: `codervps/render/template.py`
- Test: `tests/test_template_renderer.py`

- [ ] **Step 1: Write failing renderer tests**

Create `tests/test_template_renderer.py`:

```python
import json

from codervps.render.template import render_main_tf_json


def test_main_tf_json_contains_isolated_workspace_volume():
    doc = render_main_tf_json(
        images={
            "images": [
                {
                    "node_major": 24,
                    "image": "ghcr.io/guangdai/codervps-devbox:noble-20260511-node24",
                }
            ]
        },
        catalog={"plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}}},
    )
    resources = doc["resource"]
    volume = resources["docker_volume"]["workspace"]
    assert volume["name"] == "coder-${data.coder_workspace.me.id}-workspace"
    assert volume["lifecycle"]["ignore_changes"] == "all"
    container = resources["docker_container"]["workspace"]
    assert container["volumes"][0]["container_path"] == "/workspace"
    assert container["volumes"][0]["volume_name"] == "${docker_volume.workspace.name}"


def test_parameters_are_immutable():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    params = doc["data"]["coder_parameter"]
    assert params["node_major"]["mutable"] is False
    assert params["languages"]["mutable"] is False


def test_template_does_not_mount_host_docker_socket_or_block_destroy():
    doc = render_main_tf_json(images={"images": []}, catalog={"plugins": {}})
    text = json.dumps(doc, sort_keys=True)
    assert "/var/run/docker.sock" not in text
    assert "docker.sock" not in text
    assert "prevent_destroy" not in text
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
uv run pytest tests/test_template_renderer.py -q
```

Expected: FAIL with missing `codervps.render`.

- [ ] **Step 3: Implement renderer**

Create `codervps/render/__init__.py` as an empty file.

Create `codervps/render/template.py` with this minimum implementation:

```python
from __future__ import annotations


def render_main_tf_json(images: dict, catalog: dict) -> dict:
    return {
        "terraform": {
            "required_providers": {
                "coder": {"source": "coder/coder", "version": ">= 2.25.0"},
                "docker": {"source": "kreuzwerker/docker"},
            }
        },
        "provider": {"coder": [{}], "docker": [{}]},
        "data": {
            "coder_workspace": {"me": {}},
            "coder_workspace_owner": {"me": {}},
            "coder_provisioner": {"me": {}},
            "coder_parameter": {
                "node_major": {
                    "name": "node_major",
                    "display_name": "Node.js",
                    "type": "string",
                    "form_type": "dropdown",
                    "mutable": False,
                    "default": "24",
                    "option": [{"name": f"Node {m}", "value": str(m)} for m in [24, 22, 20, 18, 16]],
                },
                "languages": {
                    "name": "languages",
                    "display_name": "Languages",
                    "type": "list(string)",
                    "form_type": "multi-select",
                    "mutable": False,
                    "default": '["python"]',
                    "option": [
                        {"name": "Python", "value": "python"},
                        {"name": "Rust", "value": "rust"},
                        {"name": "Go", "value": "go"},
                        {"name": "C/C++", "value": "cpp"},
                    ],
                },
            },
        },
        "resource": {
            "docker_volume": {
                "workspace": {
                    "name": "coder-${data.coder_workspace.me.id}-workspace",
                    "lifecycle": {"ignore_changes": "all"},
                    "labels": [
                        {"label": "coder.workspace_id", "value": "${data.coder_workspace.me.id}"},
                        {"label": "coder.owner", "value": "${data.coder_workspace_owner.me.name}"},
                    ],
                }
            },
            "coder_agent": {
                "main": {
                    "arch": "${data.coder_provisioner.me.arch}",
                    "os": "linux",
                    "dir": "/workspace",
                    "startup_script": "${file(\"${path.module}/startup.sh\")}",
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
                        {"label": "coder.workspace_id", "value": "${data.coder_workspace.me.id}"},
                        {"label": "coder.owner", "value": "${data.coder_workspace_owner.me.name}"},
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
```

- [ ] **Step 4: Run tests**

Run:

```bash
uv run pytest tests/test_template_renderer.py -q
uv run ruff check codervps tests
```

Expected: tests pass; ruff passes.

- [ ] **Step 5: Commit**

```bash
git add codervps/render tests/test_template_renderer.py
git commit -m "feat: render coder terraform json"
```

## Task 6: Runtime Shell Action Executor

**Files:**
- Create: `runtime/lib/actions.sh`
- Create: `runtime/lib/run_actions.py`
- Create: `runtime/startup.sh`
- Create: `runtime/plugins/python.sh`
- Create: `runtime/plugins/rust.sh`
- Create: `runtime/plugins/go.sh`
- Create: `runtime/plugins/cpp.sh`
- Test: `tests/test_runtime_static.py`

- [ ] **Step 1: Write static runtime tests**

Create `tests/test_runtime_static.py`:

```python
from pathlib import Path


def test_runtime_does_not_use_shared_cache_root():
    text = "\n".join(path.read_text() for path in Path("runtime").rglob("*.sh"))
    assert "/opt/cde/cache" not in text
    assert "CDE_CACHE_ROOT" not in text


def test_runtime_uses_workspace_cdev_root():
    text = "\n".join(path.read_text() for path in Path("runtime").rglob("*.sh"))
    assert "/workspace/.cdev" in text


def test_runtime_has_startup_lock_and_atomic_install_guards():
    startup = Path("runtime/startup.sh").read_text()
    runner = Path("runtime/lib/run_actions.py").read_text()
    assert "startup.lock" in startup
    assert "flock" in startup
    assert "selection.sha256" in startup
    assert ".part" in runner
    assert "os.replace" in runner
    assert "/workspace/.cdev/tmp" in runner
    assert "/workspace/.cdev/state" in runner
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
uv run pytest tests/test_runtime_static.py -q
```

Expected: FAIL because `runtime` does not exist.

- [ ] **Step 3: Create runtime shell files**

Create `runtime/startup.sh`:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

export CDEV_ROOT="${CDEV_ROOT:-/workspace/.cdev}"
mkdir -p \
  "$CDEV_ROOT/downloads" \
  "$CDEV_ROOT/toolchains" \
  "$CDEV_ROOT/cache" \
  "$CDEV_ROOT/logs" \
  "$CDEV_ROOT/tmp" \
  "$CDEV_ROOT/locks" \
  "$CDEV_ROOT/state" \
  "$CDEV_ROOT/bin"

exec 9>"$CDEV_ROOT/locks/startup.lock"
flock -n 9 || {
  echo "another CoderVPS startup is already running" >&2
  exit 1
}
trap 'rm -f "$CDEV_ROOT/selection.new.json" "$CDEV_ROOT/selection.new.sha256"' EXIT

if [[ -n "${CDEV_SELECTION_JSON:-}" ]]; then
  printf '%s\n' "$CDEV_SELECTION_JSON" > "$CDEV_ROOT/selection.new.json"
  sha256sum "$CDEV_ROOT/selection.new.json" | awk '{print $1}' > "$CDEV_ROOT/selection.new.sha256"
  if [[ -f "$CDEV_ROOT/selection.sha256" ]] && ! cmp -s "$CDEV_ROOT/selection.new.sha256" "$CDEV_ROOT/selection.sha256"; then
    echo "immutable workspace selection changed; refusing startup" >&2
    exit 1
  fi
  mv "$CDEV_ROOT/selection.new.json" "$CDEV_ROOT/selection.json"
  mv "$CDEV_ROOT/selection.new.sha256" "$CDEV_ROOT/selection.sha256"
fi

source /opt/cde/runtime/lib/actions.sh

if [[ -f "$CDEV_ROOT/runtime-plan.json" ]]; then
  cdev_run_actions "$CDEV_ROOT/runtime-plan.json"
fi

cat > "$CDEV_ROOT/env.sh" <<'ENV'
export PATH="/workspace/.cdev/bin:$PATH"
ENV
```

Create `runtime/lib/actions.sh`:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

: "${CDEV_ROOT:=/workspace/.cdev}"

cdev_run_actions() {
  local plan="$1"
  python3 /opt/cde/runtime/lib/run_actions.py "$plan"
}
```

Create `runtime/lib/run_actions.py`:

```python
from __future__ import annotations

import json
import os
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import urlopen

CDEV_ROOT = Path("/workspace/.cdev")
STATE_ROOT = CDEV_ROOT / "state"
TMP_ROOT = CDEV_ROOT / "tmp"


def inside_allowed_root(path: str) -> bool:
    resolved = Path(path).resolve().as_posix()
    return (
        resolved.startswith("/workspace/.cdev/")
        or resolved == "/workspace/.cdev"
        or resolved.startswith("/home/coder/.local/share/code-server/")
        or resolved.startswith("/home/coder/.config/code-server/")
    )


def require_workspace_path(path: str) -> Path:
    if not inside_allowed_root(path):
        raise SystemExit(f"refusing non-workspace path: {path}")
    return Path(path)


def state_marker(action_id: str) -> Path:
    return STATE_ROOT / f"{action_id}.done"


def verify_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise SystemExit(f"sha256 mismatch for {path}")


def download(url: str, dest: str, sha256: str | None) -> None:
    final = require_workspace_path(dest)
    part = final.with_name(final.name + ".part")
    final.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=60) as response, part.open("wb") as fh:
        shutil.copyfileobj(response, fh)
    if sha256:
        verify_sha256(part, sha256)
    os.replace(part, final)


def extract_tar(src: str, dest: str, strip_components: int = 0) -> None:
    source = require_workspace_path(src)
    final = require_workspace_path(dest)
    final.parent.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="extract-", dir="/workspace/.cdev/tmp") as tmp:
        with tarfile.open(source) as archive:
            tmp_resolved = Path(tmp).resolve()
            for member in archive.getmembers():
                target = (Path(tmp) / member.name).resolve()
                if not str(target).startswith(str(tmp_resolved) + os.sep):
                    raise SystemExit(f"refusing unsafe archive path: {member.name}")
            archive.extractall(tmp)
        extracted = Path(tmp)
        if strip_components:
            children = [p for p in extracted.iterdir()]
            if len(children) == 1 and children[0].is_dir():
                extracted = children[0]
        os.replace(extracted, final)


def run(plan_path: Path) -> int:
    plan = json.loads(plan_path.read_text())
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    for action in plan.get("actions", []):
        marker = state_marker(action["id"])
        if marker.exists():
            continue
        creates = action.get("creates")
        if creates and Path(creates).exists():
            marker.touch()
            continue
        kind = action["type"]
        if kind == "ensure_dir":
            path = action["values"]["path"]
            require_workspace_path(path).mkdir(parents=True, exist_ok=True)
        elif kind == "download":
            download(action["values"]["url"], action["values"]["dest"], action["values"].get("sha256"))
        elif kind == "extract_tar":
            extract_tar(
                action["values"]["src"],
                action["values"]["dest"],
                int(action["values"].get("strip_components", 0)),
            )
        elif kind == "run":
            subprocess.run(action["command"], check=bool(action.get("critical", True)))
        elif kind == "verify_command":
            subprocess.run(action["command"], check=bool(action.get("critical", True)))
        elif kind in {"path_prepend", "env"}:
            continue
        elif kind in {"symlink", "write_file"}:
            require_workspace_path(action["values"]["dest"])
        else:
            raise SystemExit(f"unknown action type: {kind}")
        marker.touch()
    return 0


if __name__ == "__main__":
    raise SystemExit(run(Path(sys.argv[1])))
```

Create the four `runtime/plugins/*.sh` files with this content pattern, changing the echoed language name:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
echo "runtime plugin loaded: python"
```

- [ ] **Step 4: Run static tests**

Run:

```bash
uv run pytest tests/test_runtime_static.py -q
uv run ruff check codervps tests
```

Expected: tests pass; ruff passes.

- [ ] **Step 5: Commit**

```bash
git add runtime tests/test_runtime_static.py
git commit -m "feat: add isolated runtime action executor"
```

## Task 7: Extensions And VSIX Renderer

**Files:**
- Create: `codervps/render/extensions.py`
- Create: `tests/test_extensions_renderer.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_extensions_renderer.py`:

```python
from pathlib import Path

from codervps.config import load_extensions_config
from codervps.render.extensions import render_extensions


def test_render_extensions_creates_language_lists(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    assert (tmp_path / "extensions/core.txt").read_text().splitlines()[0] == "EditorConfig.EditorConfig"
    assert "ms-python.python" in (tmp_path / "extensions/python.txt").read_text()
    assert (tmp_path / "vsix/packs/leetcode/README.md").exists()
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_extensions_renderer.py -q
```

Expected: FAIL with missing `codervps.render.extensions`.

- [ ] **Step 3: Implement renderer**

Create `codervps/render/extensions.py` with `render_extensions(cfg, output_dir)`. It must write extension list files and VSIX directory README files. It must not copy `.vsix` binaries.

- [ ] **Step 4: Run tests**

Run:

```bash
uv run pytest tests/test_extensions_renderer.py -q
uv run ruff check codervps tests
```

Expected: tests pass; ruff passes.

- [ ] **Step 5: Commit**

```bash
git add codervps/render/extensions.py tests/test_extensions_renderer.py
git commit -m "feat: render extension catalogs"
```

## Task 8: Dockerfile Template And Build Matrix

**Files:**
- Create: `docker/Dockerfile`
- Create: `codervps/render/docker.py`
- Test: `tests/test_docker_renderer.py`

- [ ] **Step 1: Write failing Docker tests**

Create `tests/test_docker_renderer.py`:

```python
from codervps.render.docker import build_matrix


def test_build_matrix_has_five_node_images():
    catalog = {
        "base": {"ubuntu": "noble", "tag": "ubuntu-noble-20260511"},
        "node": {
            "majors": {
                "24": {"version": "24.11.1"},
                "22": {"version": "22.21.0"},
                "20": {"version": "20.19.5"},
                "18": {"version": "18.20.8"},
                "16": {"version": "16.20.2"},
            }
        },
    }
    matrix = build_matrix(catalog, "ghcr.io/guangdai/codervps-devbox")
    assert [item["node_major"] for item in matrix] == [24, 22, 20, 18, 16]
    assert matrix[0]["tag"] == "noble-20260511-node24"
    assert matrix[0]["image"] == "ghcr.io/guangdai/codervps-devbox:noble-20260511-node24"
    assert matrix[0]["base_image"].endswith(":ubuntu-noble-20260511")
    assert "sccache_sha256" in matrix[0]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_docker_renderer.py -q
```

Expected: FAIL with missing `codervps.render.docker`.

- [ ] **Step 3: Create Dockerfile template**

Create `docker/Dockerfile` with this starting content:

```dockerfile
# syntax=docker/dockerfile:1.7

ARG BASE_IMAGE
ARG NODE_VERSION
ARG UV_VERSION
ARG CODE_SERVER_VERSION
ARG SCCACHE_VERSION
ARG SCCACHE_SHA256
ARG LLVM_VERSION

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv_bin

FROM ${BASE_IMAGE}

USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/usr/local/go/bin:/usr/local/cargo/bin:/home/coder/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN --mount=type=cache,id=codervps-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=codervps-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      bash ca-certificates curl git gnupg jq unzip zip tar xz-utils file \
      ripgrep fd-find htop procps tree openssh-client sudo locales \
      build-essential pkg-config make cmake ninja-build autoconf automake libtool \
      gdb ccache xmake python3 python3-venv python3-dev pipx lsb-release; \
    ln -sf /usr/bin/fdfind /usr/local/bin/fd || true; \
    if ! id -u coder >/dev/null 2>&1; then useradd --create-home --shell /bin/bash coder; fi; \
    usermod -aG sudo coder || true; \
    echo "coder ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-coder; \
    chmod 0440 /etc/sudoers.d/90-coder

RUN set -eux; \
    curl -fsSL https://code-server.dev/install.sh | sh -s -- --version "${CODE_SERVER_VERSION}"; \
    code-server --version

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in amd64) node_arch=x64 ;; arm64) node_arch=arm64 ;; *) exit 1 ;; esac; \
    node_file="node-v${NODE_VERSION}-linux-${node_arch}.tar.xz"; \
    node_url="https://nodejs.org/dist/v${NODE_VERSION}"; \
    curl -fsSLo /tmp/SHASUMS256.txt "${node_url}/SHASUMS256.txt"; \
    node_sha="$(awk -v f="$node_file" '$2 == f {print $1}' /tmp/SHASUMS256.txt)"; \
    curl -fsSLo "/tmp/${node_file}" "${node_url}/${node_file}"; \
    echo "${node_sha}  /tmp/${node_file}" | sha256sum -c -; \
    tar -xJf "/tmp/${node_file}" -C /usr/local --strip-components=1; \
    rm -f "/tmp/${node_file}" /tmp/SHASUMS256.txt; \
    node --version; npm --version; corepack enable || true

RUN --mount=type=bind,from=uv_bin,source=/uv,target=/tmp/uv,ro \
    --mount=type=bind,from=uv_bin,source=/uvx,target=/tmp/uvx,ro \
    set -eux; \
    install -m 0755 /tmp/uv /usr/local/bin/uv; \
    install -m 0755 /tmp/uvx /usr/local/bin/uvx; \
    uv --version

RUN set -eux; \
    export RUSTUP_HOME=/usr/local/rustup; \
    export CARGO_HOME=/usr/local/cargo; \
    curl https://sh.rustup.rs -sSf | sh -s -- -y --profile minimal --default-toolchain stable; \
    chmod -R a+w /usr/local/rustup /usr/local/cargo; \
    rustup --version; rustc --version

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in amd64) sccache_arch=x86_64-unknown-linux-musl ;; arm64) sccache_arch=aarch64-unknown-linux-musl ;; *) exit 1 ;; esac; \
    file="sccache-v${SCCACHE_VERSION}-${sccache_arch}.tar.gz"; \
    url="https://github.com/mozilla/sccache/releases/download/v${SCCACHE_VERSION}/${file}"; \
    test -n "${SCCACHE_SHA256}"; \
    curl -fsSLo "/tmp/${file}" "$url"; \
    echo "${SCCACHE_SHA256}  /tmp/${file}" | sha256sum -c -; \
    mkdir -p /tmp/sccache; \
    tar -xzf "/tmp/${file}" --strip-components=1 -C /tmp/sccache; \
    install -m 0755 /tmp/sccache/sccache /usr/local/bin/sccache; \
    rm -rf "/tmp/${file}" /tmp/sccache; \
    sccache --version

RUN --mount=type=cache,id=codervps-apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=codervps-apt-lists,target=/var/lib/apt/lists,sharing=locked \
    set -eux; \
    . /etc/os-release; codename="${VERSION_CODENAME:-noble}"; \
    curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor -o /usr/share/keyrings/llvm-archive-keyring.gpg; \
    echo "deb [signed-by=/usr/share/keyrings/llvm-archive-keyring.gpg] http://apt.llvm.org/${codename}/ llvm-toolchain-${codename}-${LLVM_VERSION} main" > /etc/apt/sources.list.d/llvm.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends clang-${LLVM_VERSION} clangd-${LLVM_VERSION} clang-format-${LLVM_VERSION} lld-${LLVM_VERSION} lldb-${LLVM_VERSION}; \
    update-alternatives --install /usr/bin/clang clang /usr/bin/clang-${LLVM_VERSION} 100; \
    update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-${LLVM_VERSION} 100; \
    update-alternatives --install /usr/bin/clangd clangd /usr/bin/clangd-${LLVM_VERSION} 100; \
    clangd --version

RUN set -eux; \
    xmake --version

RUN set -eux; \
    mkdir -p /workspace /opt/cde/runtime /opt/cde/extensions /opt/cde/vsix /home/coder/.local/bin; \
    chown -R coder:coder /workspace /home/coder

USER coder
WORKDIR /workspace
```

- [ ] **Step 4: Implement build matrix helper**

Create `codervps/render/docker.py` with `build_matrix(catalog, image_repo) -> list[dict]` and deterministic tag generation. Each matrix item must include `image`, `base_image`, `node_major`, `node_version`, `uv_version`, `code_server_version`, `sccache_version`, `sccache_sha256`, and `llvm_version`. The CLI must support a `--format github-output` mode that writes a JSON matrix to `matrix=...` for GitHub Actions.

- [ ] **Step 5: Run tests**

Run:

```bash
uv run pytest tests/test_docker_renderer.py -q
uv run ruff check codervps tests
```

Expected: tests pass; ruff passes.

- [ ] **Step 6: Commit**

```bash
git add docker codervps/render/docker.py tests/test_docker_renderer.py
git commit -m "feat: add docker image matrix"
```

## Task 9: Full Generated Tree Renderer

**Files:**
- Create: `codervps/render/generated.py`
- Modify: `codervps/cli.py`
- Test: `tests/test_generated_tree.py`

- [ ] **Step 1: Write failing generated tree test**

Create `tests/test_generated_tree.py`:

```python
from pathlib import Path

from codervps.render.generated import render_generated_tree


def test_render_generated_tree(tmp_path):
    render_generated_tree(
        output_dir=tmp_path,
        catalog={
            "schema_version": 1,
            "base": {"ubuntu": "noble", "tag": "ubuntu-noble-20260511"},
            "node": {"majors": {"24": {"version": "24.11.1"}}},
            "plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}},
        },
        images={
            "schema_version": 1,
            "images": [
                {
                    "node_major": 24,
                    "image": "ghcr.io/guangdai/codervps-devbox:noble-20260511-node24",
                }
            ],
        },
    )
    assert (tmp_path / "generated/catalog/toolchains.json").exists()
    assert (tmp_path / "generated/catalog/images.json").exists()
    manifest = (tmp_path / "generated/manifest.json").read_text()
    assert "source_commit" in manifest
    assert "workflow_run_id" in manifest
    assert "generator_version" in manifest
    assert "image_tags" in manifest
    assert (tmp_path / "templates/devbox/main.tf.json").exists()
    assert (tmp_path / "templates/devbox/runtime/startup.sh").exists()
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_generated_tree.py -q
```

Expected: FAIL with missing `codervps.render.generated`.

- [ ] **Step 3: Implement generated tree renderer**

Create `codervps/render/generated.py`. It must write JSON with sorted keys, copy runtime files, render extension files, create VSIX directory README files, and write `generated/manifest.json` with schema version, generated timestamp, source commit, workflow run id, generator version, Coder base tag, Node patch versions, resolved tool versions, image tags, catalog path, and template path.

- [ ] **Step 4: Wire CLI commands**

Modify `codervps/cli.py` so `validate`, `refresh-catalog`, `render-generated`, and `build-matrix` call real functions and return `0` on success. `refresh-catalog` and `render-generated` must accept `--output`; `render-generated` and `build-matrix` must accept `--catalog` so the workflow can use one matched catalog for generated assets and image builds. `build-matrix` must accept `--format json` and `--format github-output`.

- [ ] **Step 5: Run tests**

Run:

```bash
uv run pytest tests/test_generated_tree.py tests/test_cli.py -q
uv run ruff check codervps tests
```

Expected: tests pass; ruff passes.

- [ ] **Step 6: Commit**

```bash
git add codervps/render/generated.py codervps/cli.py tests/test_generated_tree.py
git commit -m "feat: render generated branch tree"
```

## Task 10: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/generate.yml`
- Test: `tests/test_workflow_static.py`

- [ ] **Step 1: Write workflow static tests**

Create `tests/test_workflow_static.py`:

```python
from pathlib import Path


def test_generate_workflow_uses_uv_and_buildx():
    text = Path(".github/workflows/generate.yml").read_text()
    assert "astral-sh/setup-uv" in text
    assert "docker/setup-buildx-action" in text
    assert "docker/build-push-action" in text
    assert "actions/upload-artifact" in text
    assert "actions/download-artifact" in text
    assert "linux/amd64" in text
    assert "workflow_dispatch" in text
    assert "schedule" in text
    assert "concurrency:" in text
    assert "allow_rebuild_date_tag" in text
    assert "docker buildx imagetools inspect" in text
    assert "--force-with-lease" in text
    assert "--force\n" not in text
    assert "! -name .git" in text
    assert "codervps-devbox:test" not in text
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_workflow_static.py -q
```

Expected: FAIL because workflow file does not exist.

- [ ] **Step 3: Create workflow**

Create `.github/workflows/generate.yml` with:

- `workflow_dispatch`
- manual input `allow_rebuild_date_tag`, default false
- monthly cron
- top-level `concurrency` so generated-branch publishing is serialized
- `permissions: contents: write, packages: write`
- setup uv
- run `uv sync`
- run `uv run pytest`
- run `uv run ruff check`
- run `uv run codervps refresh-catalog --output build/toolchains.json`
- run `uv run codervps render-generated --catalog build/toolchains.json --output build/generated`
- setup Buildx
- login to GHCR with `GITHUB_TOKEN`
- verify date tags do not already exist in GHCR unless `allow_rebuild_date_tag` is explicitly true
- build and push only `linux/amd64`
- update `generated` branch only after image builds succeed

Use this initial workflow body:

```yaml
name: Generate CoderVPS Images

on:
  workflow_dispatch:
    inputs:
      allow_rebuild_date_tag:
        description: "Allow rebuilding an existing immutable date tag"
        required: false
        default: false
        type: boolean
  schedule:
    - cron: "17 3 1 * *"

permissions:
  contents: write
  packages: write

concurrency:
  group: codervps-generated
  cancel-in-progress: false

jobs:
  prepare:
    runs-on: ubuntu-24.04
    outputs:
      matrix: ${{ steps.matrix.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v5

      - name: Install dependencies
        run: uv sync

      - name: Test
        run: uv run pytest -q

      - name: Lint
        run: uv run ruff check codervps tests

      - name: Refresh catalog
        run: uv run codervps refresh-catalog --output build/toolchains.json

      - name: Render generated tree
        run: uv run codervps render-generated --catalog build/toolchains.json --output build/generated

      - name: Prepare image matrix
        id: matrix
        run: uv run codervps build-matrix --catalog build/toolchains.json --format github-output >> "$GITHUB_OUTPUT"

      - uses: actions/upload-artifact@v4
        with:
          name: generated-tree
          path: build/generated

  build:
    runs-on: ubuntu-24.04
    needs: prepare
    strategy:
      fail-fast: false
      matrix:
        include: ${{ fromJson(needs.prepare.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Check image tags are new
        if: ${{ !inputs.allow_rebuild_date_tag }}
        run: |
          if docker buildx imagetools inspect "${{ matrix.image }}" >/dev/null 2>&1; then
            echo "::error title=Existing immutable tag::${{ matrix.image }} already exists"
            exit 1
          fi

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          file: docker/Dockerfile
          platforms: linux/amd64
          push: true
          tags: ${{ matrix.image }}
          build-args: |
            BASE_IMAGE=${{ matrix.base_image }}
            NODE_VERSION=${{ matrix.node_version }}
            UV_VERSION=${{ matrix.uv_version }}
            CODE_SERVER_VERSION=${{ matrix.code_server_version }}
            SCCACHE_VERSION=${{ matrix.sccache_version }}
            SCCACHE_SHA256=${{ matrix.sccache_sha256 }}
            LLVM_VERSION=${{ matrix.llvm_version }}

  publish-generated:
    runs-on: ubuntu-24.04
    needs: [prepare, build]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/download-artifact@v4
        with:
          name: generated-tree
          path: build/generated

      - name: Publish generated branch
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git fetch origin generated:refs/remotes/origin/generated || true
          git switch --orphan generated-work
          find . -mindepth 1 -maxdepth 1 ! -name build ! -name .git -exec rm -rf {} +
          cp -a build/generated/. .
          git add -A
          git commit -m "chore: update generated assets"
          git push origin HEAD:generated --force-with-lease
```

- [ ] **Step 4: Run test**

Run:

```bash
uv run pytest tests/test_workflow_static.py -q
uv run ruff check codervps tests
```

Expected: tests pass; ruff passes.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/generate.yml tests/test_workflow_static.py
git commit -m "ci: add generated branch image workflow"
```

## Task 11: Thin `cdev`

**Files:**
- Modify: `cdev`
- Test: `tests/test_cdev_static.py`

- [ ] **Step 1: Write static tests for cdev scope**

Create `tests/test_cdev_static.py`:

```python
from pathlib import Path


def test_cdev_has_no_legacy_patch_or_build_commands():
    text = Path("cdev").read_text()
    assert "patch-runtime" not in text
    assert "clean-main-tf" not in text
    assert "write-startup" not in text
    assert "rebuild-devbox" not in text
    assert "docker build" not in text


def test_cdev_does_not_prune_coder_managed_volumes():
    text = Path("cdev").read_text()
    assert "docker volume prune" not in text
    assert "docker system prune --volumes" not in text
    assert "docker volume rm" not in text


def test_cdev_sync_generated_is_locked_and_atomic():
    text = Path("cdev").read_text()
    assert "flock" in text
    assert "/opt/coder-cde/.locks" in text
    assert "check-generated" in text
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_cdev_static.py -q
```

Expected: FAIL because legacy commands are present and the new locked/validated
sync flow is not implemented yet.

- [ ] **Step 3: Rewrite cdev as thin helper**

Modify `cdev` to keep only:

- `info`
- `doctor`
- `ps`
- `logs`
- `restart`
- `template-dir`
- `push-template`
- `sync-generated`
- `check-generated`
- `check-images`
- `list-workspace-volumes`
- `install-self`

Do not run `docker build`. Do not patch template source files.
Deletion inside `cdev` may use normal shell commands, but it must be path-scoped to generated template staging directories and guarded by validation.
`list-workspace-volumes` may list volumes by Coder labels for diagnostics, but `cdev` must not delete them. `sync-generated` must write into a temporary directory, validate with `check-generated`, then atomically switch the template directory while holding a lock under `/opt/coder-cde/.locks`.

- [ ] **Step 4: Run tests**

Run:

```bash
uv run pytest tests/test_cdev_static.py -q
uv run ruff check codervps tests
```

Expected: tests pass; ruff passes.

- [ ] **Step 5: Commit**

```bash
git add cdev tests/test_cdev_static.py
git commit -m "refactor: reduce cdev to vps operations"
```

## Task 12: README And Operator Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/generated-branch.md`
- Create: `docs/vsix.md`
- Test: `tests/test_docs_static.py`

- [ ] **Step 1: Write docs static test**

Create `tests/test_docs_static.py`:

```python
from pathlib import Path


def test_readme_mentions_generated_branch_and_no_gh_cli():
    text = Path("README.md").read_text()
    assert "generated branch" in text
    assert "GitHub CLI is not required" in text
    assert "/workspace/.cdev" in text


def test_vsix_docs_say_binaries_are_not_committed():
    text = Path("docs/vsix.md").read_text()
    assert ".vsix files are not committed" in text
    assert "/opt/coder-cde/vsix" in text
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_docs_static.py -q
```

Expected: FAIL because docs do not contain required text.

- [ ] **Step 3: Write docs**

Update `README.md` with the high-level operator workflow:

- source branch and generated branch roles
- monthly GitHub Actions build
- GHCR tag pattern
- no GitHub CLI requirement
- `cdev sync-generated` and `cdev push-template`
- workspace lifecycle and deletion behavior
- why `docker volume prune` and `docker system prune --volumes` are not normal cleanup tools for Coder-managed workspace volumes

Create `docs/generated-branch.md` with generated branch structure and publishing steps.

Create `docs/vsix.md` with VSIX directory layout and the sentence `.vsix files are not committed`.

- [ ] **Step 4: Run tests**

Run:

```bash
uv run pytest tests/test_docs_static.py -q
uv run ruff check codervps tests
```

Expected: tests pass; ruff passes.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/generated-branch.md docs/vsix.md tests/test_docs_static.py
git commit -m "docs: document generated publishing workflow"
```

## Task 13: Full Validation And Cleanup

**Files:**
- Modify only files needed to fix validation failures.

- [ ] **Step 1: Run full test suite**

Run:

```bash
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run formatting/lint checks**

Run:

```bash
uv run ruff check codervps tests
uv run ruff format --check codervps tests
```

Expected: both commands pass.

- [ ] **Step 3: Render a local generated tree**

Run:

```bash
uv run codervps refresh-catalog --output build/toolchains.json
uv run codervps render-generated --catalog build/toolchains.json --output build/generated
```

Expected: exits `0` and writes `build/generated/templates/devbox/main.tf.json`.

- [ ] **Step 4: Validate no generated output is tracked on main**

Run:

```bash
git status --short
```

Expected: no tracked generated output changes. If `build/generated` appears, add `build/` to `.gitignore` and commit it.

- [ ] **Step 5: Commit final validation fixes**

If changes were needed:

```bash
git add <changed-files>
git commit -m "test: validate codervps refactor"
```

If no changes were needed, do not create an empty commit.

## Spec Coverage Checklist

- Pluginized Python generator: Tasks 1-5 and 9.
- TOML source configuration: Task 2.
- Plugin interface and four first-version plugins: Task 3.
- Catalog refresh and generated branch catalog data: Tasks 4 and 9.
- Terraform JSON template: Task 5.
- Runtime action model and workspace isolation: Task 6.
- Extension and VSIX management: Task 7.
- Docker image matrix and GHCR tag generation: Task 8.
- GitHub Actions monthly/manual workflow: Task 10.
- Thin `cdev`: Task 11.
- Operator docs: Task 12.
- Full validation: Task 13.
