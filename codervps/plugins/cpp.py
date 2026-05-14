from __future__ import annotations

from codervps.models import ParameterSpec, PluginCatalog, RuntimeAction, RuntimePlan

_CDEV = "/workspace/.cdev"


class CppPlugin:
    id: str = "cpp"
    label: str = "C/C++"

    def discover(self) -> PluginCatalog:
        """Discover available LLVM/clangd versions."""
        raise NotImplementedError("catalog discovery is implemented in catalog.py")

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        """Produce Coder parameters for C/C++ LLVM version selection."""
        versions = catalog.versions
        default_llvm = catalog.defaults.get("llvm", "latest")
        return [
            ParameterSpec(
                name="cpp_llvm",
                display_name="LLVM/Clangd Version",
                type="string",
                form_type="dropdown",
                default=default_llvm,
                mutable=False,
                order=400,
                options=versions,
                condition="contains(data.coder_parameter.languages.value, 'cpp')",
            ),
        ]

    def runtime_plan(self, selection: dict[str, str | list[str]]) -> RuntimePlan:
        """Produce runtime actions for C/C++ workspace setup.

        LLVM/clangd is pre-installed in the base image.  This plugin
        records the selection for activation and ensures cache directories
        exist.  When a non-prebundled LLVM version is selected the runtime
        must install it into the workspace volume (handled at a later
        stage via the catalog).
        """
        llvm = str(selection.get("llvm", "latest"))
        root = f"{_CDEV}/toolchains/llvm/{llvm}"

        return RuntimePlan(
            plugin=self.id,
            env={
                "CCACHE_DIR": f"{_CDEV}/cache/ccache",
                "LLVM_VERSION": llvm,
            },
            actions=[
                RuntimeAction(
                    id="cpp-ensure-ccache",
                    type="ensure_dir",
                    values={"path": f"{_CDEV}/cache/ccache"},
                ),
                RuntimeAction(
                    id="cpp-ensure-llvm-dir",
                    type="ensure_dir",
                    values={"path": root},
                ),
                RuntimeAction(
                    id="cpp-llvm-path-prepend",
                    type="path_prepend",
                    values={"path": f"{root}/usr/bin"},
                ),
                RuntimeAction(
                    id="cpp-verify-clangd",
                    type="verify_command",
                    command=["clangd", "--version"],
                    critical=False,
                ),
            ],
        )
