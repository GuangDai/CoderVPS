from __future__ import annotations

import re
from pathlib import Path

from codervps.discovery import go_downloads, go_linux_amd64_sha256
from codervps.models import ParameterSpec, PluginCatalog, RuntimeAction, RuntimePlan, VersionEntry


class GoPlugin:
    id = "go"
    label = "Go"

    def discover(self, fixture_dir=None) -> PluginCatalog:
        data = go_downloads(Path(fixture_dir) if fixture_dir else None)
        versions = []
        for item in data:
            ver = item["version"]
            version_str = ver.removeprefix("go")
            stable = item.get("stable", False)
            sha256 = go_linux_amd64_sha256(item)
            if not sha256:
                continue
            versions.append(
                VersionEntry(
                    value=version_str,
                    label=f"Go {version_str}",
                    status="active" if stable else "prerelease",
                    default=(version_str == "1.24.9"),
                    metadata={"sha256": sha256},
                )
            )
        if not any(v.default for v in versions) and versions:
            versions_without_default = [
                VersionEntry(
                    value=v.value,
                    label=v.label,
                    status=v.status,
                    default=(i == 0),
                    metadata=v.metadata,
                )
                for i, v in enumerate(versions)
            ]
            return PluginCatalog(
                plugin=self.id,
                versions=versions_without_default,
                defaults={"version": versions[0].value},
            )
        first_stable = next(
            (v for v in versions if v.status == "active"), versions[0] if versions else None
        )
        return PluginCatalog(
            plugin=self.id,
            versions=versions,
            defaults={"version": first_stable.value if first_stable else "1.24.9"},
        )

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        return [
            ParameterSpec(
                name="go_version",
                display_name="Go Version",
                type="string",
                form_type="dropdown",
                default=catalog.defaults.get("version", "1.24.9"),
                mutable=False,
                order=30,
                count="data.coder_parameter.enable_go.value ? 1 : 0",
                options=catalog.versions,
            ),
            ParameterSpec(
                name="go_tools",
                display_name="Go Tools",
                type="list(string)",
                form_type="multi-select",
                default='["gopls"]',
                mutable=False,
                order=31,
                count="data.coder_parameter.enable_go.value ? 1 : 0",
                options=[
                    VersionEntry(value="gopls", label="gopls"),
                    VersionEntry(value="dlv", label="dlv (Delve debugger)"),
                ],
            ),
        ]

    def runtime_plan(self, selection: dict) -> RuntimePlan:
        version = str(selection["version"])
        sha256 = str(selection.get("sha256", ""))
        if not sha256:
            raise ValueError("Go runtime_plan requires sha256 for selected version")
        if not re.fullmatch(r"[0-9a-f]{64}", sha256):
            raise ValueError("Go runtime_plan requires a real 64-character hex sha256")
        tools = selection.get("tools", ["gopls"])
        if isinstance(tools, str):
            tools = [tools]
        gopls_version = str(selection.get("gopls_version", "latest"))
        dlv_version = str(selection.get("dlv_version", "latest"))
        root = f"/home/coder/.cdev/toolchains/go/{version}"
        tarball = f"/home/coder/.cdev/downloads/go{version}.linux-amd64.tar.gz"
        url = f"https://go.dev/dl/go{version}.linux-amd64.tar.gz"
        actions: list[RuntimeAction] = [
            RuntimeAction(
                id="go-downloads-dir",
                type="ensure_dir",
                values={"path": "/home/coder/.cdev/downloads"},
            ),
            RuntimeAction(
                id="go-cache-dir",
                type="ensure_dir",
                values={"path": "/home/coder/.cdev/cache/go/build"},
            ),
            RuntimeAction(
                id="go-cache-mod-dir",
                type="ensure_dir",
                values={"path": "/home/coder/.cdev/cache/go/pkg/mod"},
            ),
            RuntimeAction(
                id="go-download",
                type="download",
                values={
                    "url": url,
                    "dest": tarball,
                    "sha256": sha256,
                },
            ),
            RuntimeAction(
                id="go-extract",
                type="extract_tar",
                creates=f"{root}/bin/go",
                values={
                    "src": tarball,
                    "dest": root,
                    "strip_components": 1,
                },
            ),
            RuntimeAction(
                id="go-path",
                type="path_prepend",
                values={"path": f"{root}/bin"},
            ),
            RuntimeAction(
                id="go-bin-path",
                type="path_prepend",
                values={"path": "/home/coder/.cdev/toolchains/go/bin"},
            ),
            RuntimeAction(
                id="go-verify",
                type="verify_command",
                command=["go", "version"],
                critical=True,
            ),
        ]
        if "gopls" in tools:
            actions.append(
                RuntimeAction(
                    id="go-tool-gopls",
                    type="run",
                    command=["go", "install", f"golang.org/x/tools/gopls@{gopls_version}"],
                    env={
                        "GOROOT": root,
                        "GOBIN": "/home/coder/.cdev/toolchains/go/bin",
                        "GOPATH": "/home/coder/.cdev/cache/go/gopath",
                    },
                )
            )
        if "dlv" in tools:
            actions.append(
                RuntimeAction(
                    id="go-tool-dlv",
                    type="run",
                    command=["go", "install", f"github.com/go-delve/delve/cmd/dlv@{dlv_version}"],
                    env={
                        "GOROOT": root,
                        "GOBIN": "/home/coder/.cdev/toolchains/go/bin",
                        "GOPATH": "/home/coder/.cdev/cache/go/gopath",
                    },
                )
            )
        return RuntimePlan(
            plugin=self.id,
            actions=actions,
            env={
                "GOROOT": root,
                "GOBIN": "/home/coder/.cdev/toolchains/go/bin",
                "GOCACHE": "/home/coder/.cdev/cache/go/build",
                "GOMODCACHE": "/home/coder/.cdev/cache/go/pkg/mod",
                "GOPATH": "/home/coder/.cdev/cache/go/gopath",
            },
        )
