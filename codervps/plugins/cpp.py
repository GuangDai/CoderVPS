from __future__ import annotations

from pathlib import Path

from codervps.discovery import cpp_llvm_versions
from codervps.models import ParameterSpec, PluginCatalog, RuntimeAction, RuntimePlan, VersionEntry


class CppPlugin:
    id = "cpp"
    label = "C/C++"

    def discover(self, fixture_dir=None) -> PluginCatalog:
        entries = cpp_llvm_versions(Path(fixture_dir) if fixture_dir else None)
        default = next((entry["version"] for entry in entries if entry["status"] != "snapshot"), "")
        versions = [
            VersionEntry(
                value=entry["version"],
                label=f"LLVM {entry['version']}",
                status=entry["status"],
                default=entry["version"] == default,
            )
            for entry in entries
        ]
        return PluginCatalog(
            plugin=self.id,
            versions=versions,
            defaults={"llvm": default},
        )

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        return [
            ParameterSpec(
                name="cpp_llvm",
                display_name="LLVM / Clang Version",
                type="string",
                form_type="dropdown",
                default=catalog.defaults.get("llvm", "19"),
                mutable=False,
                order=40,
                count="data.coder_parameter.enable_cpp.value ? 1 : 0",
                options=catalog.versions,
            ),
        ]

    def runtime_plan(self, selection: dict) -> RuntimePlan:
        llvm = str(selection.get("llvm", "19"))
        root = f"/home/coder/.cdev/toolchains/llvm/{llvm}"
        is_prebundled = llvm == "19"
        actions: list[RuntimeAction] = [
            RuntimeAction(
                id="cpp-cache-ccache",
                type="ensure_dir",
                values={"path": "/home/coder/.cdev/cache/ccache"},
            ),
            RuntimeAction(
                id="cpp-llvm-dir",
                type="ensure_dir",
                values={"path": root},
            ),
        ]
        if not is_prebundled:
            actions.append(
                RuntimeAction(
                    id="cpp-llvm-path",
                    type="path_prepend",
                    values={"path": f"{root}/usr/bin"},
                )
            )
        actions.append(
            RuntimeAction(
                id="cpp-verify",
                type="verify_command",
                command=["clangd", "--version"],
                critical=False,
            )
        )
        return RuntimePlan(
            plugin=self.id,
            env={
                "CCACHE_DIR": "/home/coder/.cdev/cache/ccache",
            },
            actions=actions,
        )
