from __future__ import annotations

from pathlib import Path

from codervps.discovery import python_versions
from codervps.models import ParameterSpec, PluginCatalog, RuntimeAction, RuntimePlan, VersionEntry


class PythonPlugin:
    id = "python"
    label = "Python"

    def discover(self, fixture_dir=None) -> PluginCatalog:
        entries = python_versions(
            Path(fixture_dir) if fixture_dir else None,
            default_minor="3.13",
        )
        versions = [
            VersionEntry(
                value=entry["request"],
                label=entry["label"],
                status=entry["status"],
                default=(
                    entry["implementation"] == "cpython"
                    and entry["minor"] == "3.13"
                    and entry["variant"] == "default"
                ),
                metadata={
                    "implementation": entry["implementation"],
                    "version": entry["version"],
                    "minor": entry["minor"],
                    "variant": entry["variant"],
                    "uv_key": entry["uv_key"],
                },
            )
            for entry in entries
        ]
        default = next(
            (entry.value for entry in versions if entry.default),
            versions[0].value if versions else "cpython@3.13",
        )
        return PluginCatalog(plugin=self.id, versions=versions, defaults={"version": default})

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        return [
            ParameterSpec(
                name="python_version",
                display_name="Python Runtime",
                type="string",
                form_type="dropdown",
                default=catalog.defaults.get("version", "cpython@3.13"),
                mutable=False,
                order=10,
                count="data.coder_parameter.enable_python.value ? 1 : 0",
                options=catalog.versions,
            ),
            ParameterSpec(
                name="python_tools",
                display_name="Python Tools",
                type="list(string)",
                form_type="multi-select",
                default='["ruff", "debugpy"]',
                mutable=False,
                order=11,
                count="data.coder_parameter.enable_python.value ? 1 : 0",
                options=[
                    VersionEntry(value="ruff", label="ruff"),
                    VersionEntry(value="debugpy", label="debugpy"),
                    VersionEntry(value="ipython", label="IPython"),
                    VersionEntry(value="jupyter", label="Jupyter"),
                ],
            ),
        ]

    def runtime_plan(self, selection: dict) -> RuntimePlan:
        version = str(selection["version"])
        tools = selection.get("tools", ["ruff", "debugpy"])
        if isinstance(tools, str):
            tools = [tools]
        actions: list[RuntimeAction] = [
            RuntimeAction(
                id="python-cache",
                type="ensure_dir",
                values={"path": "/home/coder/.cdev/cache/uv"},
            ),
            RuntimeAction(
                id="python-toolchains-dir",
                type="ensure_dir",
                values={"path": "/home/coder/.cdev/toolchains/python"},
            ),
            RuntimeAction(
                id="python-bin-dir",
                type="ensure_dir",
                values={"path": "/home/coder/.cdev/bin"},
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
                    "/home/coder/.cdev/toolchains/python",
                ],
                env={
                    "UV_PYTHON_INSTALL_DIR": "/home/coder/.cdev/toolchains/python",
                    "UV_CACHE_DIR": "/home/coder/.cdev/cache/uv",
                },
            ),
            RuntimeAction(
                id="python-verify",
                type="verify_command",
                command=["uv", "python", "find", version],
                critical=True,
            ),
            RuntimeAction(
                id="python-path",
                type="path_prepend",
                values={"path": "/home/coder/.cdev/bin"},
            ),
        ]
        tool_actions = {
            "ruff": RuntimeAction(
                id="python-tool-ruff",
                type="run",
                command=["uv", "tool", "install", "ruff"],
                env={
                    "UV_TOOL_DIR": "/home/coder/.cdev/toolchains/python-tools",
                    "UV_TOOL_BIN_DIR": "/home/coder/.cdev/bin",
                },
            ),
            "debugpy": RuntimeAction(
                id="python-tool-debugpy",
                type="run",
                command=["uv", "tool", "install", "debugpy"],
                env={
                    "UV_TOOL_DIR": "/home/coder/.cdev/toolchains/python-tools",
                    "UV_TOOL_BIN_DIR": "/home/coder/.cdev/bin",
                },
            ),
            "ipython": RuntimeAction(
                id="python-tool-ipython",
                type="run",
                command=["uv", "tool", "install", "ipython"],
                env={
                    "UV_TOOL_DIR": "/home/coder/.cdev/toolchains/python-tools",
                    "UV_TOOL_BIN_DIR": "/home/coder/.cdev/bin",
                },
            ),
            "jupyter": RuntimeAction(
                id="python-tool-jupyter",
                type="run",
                command=["uv", "tool", "install", "jupyter"],
                env={
                    "UV_TOOL_DIR": "/home/coder/.cdev/toolchains/python-tools",
                    "UV_TOOL_BIN_DIR": "/home/coder/.cdev/bin",
                },
            ),
        }
        for tool_name in tools:
            if tool_name in tool_actions:
                actions.append(tool_actions[tool_name])
        return RuntimePlan(
            plugin=self.id,
            actions=actions,
            env={
                "UV_CACHE_DIR": "/home/coder/.cdev/cache/uv",
                "UV_PYTHON_INSTALL_DIR": "/home/coder/.cdev/toolchains/python",
                "UV_TOOL_DIR": "/home/coder/.cdev/toolchains/python-tools",
                "UV_TOOL_BIN_DIR": "/home/coder/.cdev/bin",
            },
        )
