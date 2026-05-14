from __future__ import annotations

from codervps.models import ParameterSpec, PluginCatalog, RuntimeAction, RuntimePlan, VersionEntry


class CppPlugin:
    id = "cpp"
    label = "C/C++"

    def discover(self, fixture_dir=None) -> PluginCatalog:
        versions = [
            VersionEntry(value="20", label="LLVM 20", status="prerelease"),
            VersionEntry(value="19", label="LLVM 19", default=True, status="active"),
            VersionEntry(value="18", label="LLVM 18", status="active"),
            VersionEntry(value="17", label="LLVM 17", status="supported"),
            VersionEntry(value="16", label="LLVM 16", status="eol"),
        ]
        return PluginCatalog(
            plugin=self.id,
            versions=versions,
            defaults={"llvm": "19"},
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
                condition='contains(data.coder_parameter.languages.value, "cpp")',
                options=catalog.versions,
            ),
        ]

    def runtime_plan(self, selection: dict) -> RuntimePlan:
        llvm = str(selection.get("llvm", "19"))
        root = f"/workspace/.cdev/toolchains/llvm/{llvm}"
        is_prebundled = llvm == "19"
        actions: list[RuntimeAction] = [
            RuntimeAction(
                id="cpp-cache-ccache",
                type="ensure_dir",
                values={"path": "/workspace/.cdev/cache/ccache"},
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
                "CCACHE_DIR": "/workspace/.cdev/cache/ccache",
            },
            actions=actions,
        )
