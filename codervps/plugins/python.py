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
                value=entry["version"],
                label=f"Python {entry['version']}",
                status=entry["status"],
                default=entry["version"] == "3.13",
            )
            for entry in entries
        ]
        return PluginCatalog(plugin=self.id, versions=versions, defaults={"version": "3.13"})

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        return [
            ParameterSpec(
                name="python_version",
                display_name="Python Version",
                type="string",
                form_type="dropdown",
                default="3.13",
                mutable=False,
                order=10,
                condition='contains(data.coder_parameter.languages.value, "python")',
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
                condition='contains(data.coder_parameter.languages.value, "python")',
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
                values={"path": "/workspace/.cdev/cache/uv"},
            ),
            RuntimeAction(
                id="python-toolchains-dir",
                type="ensure_dir",
                values={"path": "/workspace/.cdev/toolchains/python"},
            ),
            RuntimeAction(
                id="python-bin-dir",
                type="ensure_dir",
                values={"path": "/workspace/.cdev/bin"},
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
                env={
                    "UV_PYTHON_INSTALL_DIR": "/workspace/.cdev/toolchains/python",
                    "UV_CACHE_DIR": "/workspace/.cdev/cache/uv",
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
                values={"path": "/workspace/.cdev/bin"},
            ),
        ]
        tool_actions = {
            "ruff": RuntimeAction(
                id="python-tool-ruff",
                type="run",
                command=["uv", "tool", "install", "ruff"],
                env={
                    "UV_TOOL_DIR": "/workspace/.cdev/toolchains/python-tools",
                    "UV_TOOL_BIN_DIR": "/workspace/.cdev/bin",
                },
            ),
            "debugpy": RuntimeAction(
                id="python-tool-debugpy",
                type="run",
                command=["uv", "tool", "install", "debugpy"],
                env={
                    "UV_TOOL_DIR": "/workspace/.cdev/toolchains/python-tools",
                    "UV_TOOL_BIN_DIR": "/workspace/.cdev/bin",
                },
            ),
            "ipython": RuntimeAction(
                id="python-tool-ipython",
                type="run",
                command=["uv", "tool", "install", "ipython"],
                env={
                    "UV_TOOL_DIR": "/workspace/.cdev/toolchains/python-tools",
                    "UV_TOOL_BIN_DIR": "/workspace/.cdev/bin",
                },
            ),
            "jupyter": RuntimeAction(
                id="python-tool-jupyter",
                type="run",
                command=["uv", "tool", "install", "jupyter"],
                env={
                    "UV_TOOL_DIR": "/workspace/.cdev/toolchains/python-tools",
                    "UV_TOOL_BIN_DIR": "/workspace/.cdev/bin",
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
                "UV_CACHE_DIR": "/workspace/.cdev/cache/uv",
                "UV_PYTHON_INSTALL_DIR": "/workspace/.cdev/toolchains/python",
                "UV_TOOL_DIR": "/workspace/.cdev/toolchains/python-tools",
                "UV_TOOL_BIN_DIR": "/workspace/.cdev/bin",
            },
        )
