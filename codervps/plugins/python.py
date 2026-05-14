from __future__ import annotations

from codervps.models import ParameterSpec, PluginCatalog, RuntimeAction, RuntimePlan

_CDEV = "/workspace/.cdev"


class PythonPlugin:
    id: str = "python"
    label: str = "Python"

    def discover(self) -> PluginCatalog:
        """Discover available CPython versions from the uv-managed catalog."""
        raise NotImplementedError("catalog discovery is implemented in catalog.py")

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        """Produce Coder parameters for Python version and optional tools."""
        versions = catalog.versions
        default_ver = catalog.defaults.get("version", "3.13")
        return [
            ParameterSpec(
                name="python_version",
                display_name="Python Version",
                type="string",
                form_type="dropdown",
                default=default_ver,
                mutable=False,
                order=100,
                options=versions,
                condition="contains(data.coder_parameter.languages.value, 'python')",
            ),
            ParameterSpec(
                name="python_tools",
                display_name="Python Tools",
                type="list(string)",
                form_type="multi-select",
                default=catalog.defaults.get("tools", '["ruff","debugpy"]'),
                mutable=False,
                order=101,
                condition="contains(data.coder_parameter.languages.value, 'python')",
            ),
        ]

    def runtime_plan(self, selection: dict[str, str | list[str]]) -> RuntimePlan:
        """Produce runtime actions to install Python with uv."""
        version = str(selection["version"])
        tools_raw = selection.get("tools", ["ruff", "debugpy"])
        tools: list[str] = [tools_raw] if isinstance(tools_raw, str) else list(tools_raw)

        actions: list[RuntimeAction] = [
            RuntimeAction(
                id="python-ensure-cache",
                type="ensure_dir",
                values={"path": f"{_CDEV}/cache/uv"},
            ),
            RuntimeAction(
                id="python-ensure-toolchains",
                type="ensure_dir",
                values={"path": f"{_CDEV}/toolchains/python"},
            ),
            RuntimeAction(
                id="python-ensure-tools",
                type="ensure_dir",
                values={"path": f"{_CDEV}/toolchains/python-tools"},
            ),
            RuntimeAction(
                id="python-ensure-bin",
                type="ensure_dir",
                values={"path": f"{_CDEV}/bin"},
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
                    f"{_CDEV}/toolchains/python",
                ],
            ),
            RuntimeAction(
                id="python-verify",
                type="verify_command",
                command=["uv", "python", "find", version],
            ),
        ]

        for tool in tools:
            actions.append(
                RuntimeAction(
                    id=f"python-tool-{tool}",
                    type="run",
                    command=["uv", "tool", "install", tool],
                )
            )

        return RuntimePlan(
            plugin=self.id,
            actions=actions,
            env={
                "UV_CACHE_DIR": f"{_CDEV}/cache/uv",
                "UV_PYTHON_INSTALL_DIR": f"{_CDEV}/toolchains/python",
                "UV_TOOL_DIR": f"{_CDEV}/toolchains/python-tools",
                "UV_TOOL_BIN_DIR": f"{_CDEV}/bin",
            },
        )
