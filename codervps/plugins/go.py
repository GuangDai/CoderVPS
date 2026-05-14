from __future__ import annotations

import json
from pathlib import Path

from codervps.models import ParameterSpec, PluginCatalog, RuntimeAction, RuntimePlan, VersionEntry


class GoPlugin:
    id = "go"
    label = "Go"

    def discover(self, fixture_dir=None) -> PluginCatalog:
        if fixture_dir:
            data = json.loads((Path(fixture_dir) / "go-dl.json").read_text())
        else:
            data = self._default_go_versions()
        versions = []
        for item in data:
            ver = item["version"]
            version_str = ver.removeprefix("go")
            stable = item.get("stable", False)
            versions.append(
                VersionEntry(
                    value=version_str,
                    label=f"Go {version_str}",
                    status="active" if stable else "prerelease",
                    default=(version_str == "1.24.9"),
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

    @staticmethod
    def _default_go_versions() -> list[dict]:
        return [
            {
                "version": "go1.26.3",
                "stable": True,
                "files": [{"filename": "go1.26.3.linux-amd64.tar.gz", "sha256": "sha-go-1263"}],
            },
            {
                "version": "go1.25.5",
                "stable": True,
                "files": [{"filename": "go1.25.5.linux-amd64.tar.gz", "sha256": "sha-go-1255"}],
            },
            {
                "version": "go1.24.9",
                "stable": True,
                "files": [{"filename": "go1.24.9.linux-amd64.tar.gz", "sha256": "sha-go-1249"}],
            },
            {
                "version": "go1.23.12",
                "stable": True,
                "files": [{"filename": "go1.23.12.linux-amd64.tar.gz", "sha256": "sha-go-12312"}],
            },
            {
                "version": "go1.22.12",
                "stable": True,
                "files": [{"filename": "go1.22.12.linux-amd64.tar.gz", "sha256": "sha-go-12212"}],
            },
        ]

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
                condition='contains(data.coder_parameter.languages.value, "go")',
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
                condition='contains(data.coder_parameter.languages.value, "go")',
                options=[
                    VersionEntry(value="gopls", label="gopls"),
                    VersionEntry(value="dlv", label="dlv (Delve debugger)"),
                ],
            ),
        ]

    def runtime_plan(self, selection: dict) -> RuntimePlan:
        version = str(selection["version"])
        tools = selection.get("tools", ["gopls"])
        if isinstance(tools, str):
            tools = [tools]
        gopls_version = str(selection.get("gopls_version", "latest"))
        dlv_version = str(selection.get("dlv_version", "latest"))
        root = f"/workspace/.cdev/toolchains/go/{version}"
        tarball = f"/workspace/.cdev/downloads/go{version}.linux-amd64.tar.gz"
        url = f"https://go.dev/dl/go{version}.linux-amd64.tar.gz"
        actions: list[RuntimeAction] = [
            RuntimeAction(
                id="go-downloads-dir",
                type="ensure_dir",
                values={"path": "/workspace/.cdev/downloads"},
            ),
            RuntimeAction(
                id="go-cache-dir",
                type="ensure_dir",
                values={"path": "/workspace/.cdev/cache/go/build"},
            ),
            RuntimeAction(
                id="go-cache-mod-dir",
                type="ensure_dir",
                values={"path": "/workspace/.cdev/cache/go/pkg/mod"},
            ),
            RuntimeAction(
                id="go-download",
                type="download",
                values={
                    "url": url,
                    "dest": tarball,
                    "sha256": "auto",
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
                values={"path": "/workspace/.cdev/toolchains/go/bin"},
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
                        "GOBIN": "/workspace/.cdev/toolchains/go/bin",
                        "GOPATH": "/workspace/.cdev/cache/go/gopath",
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
                        "GOBIN": "/workspace/.cdev/toolchains/go/bin",
                        "GOPATH": "/workspace/.cdev/cache/go/gopath",
                    },
                )
            )
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
