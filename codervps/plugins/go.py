from __future__ import annotations

from codervps.models import ParameterSpec, PluginCatalog, RuntimeAction, RuntimePlan

_CDEV = "/workspace/.cdev"


class GoPlugin:
    id: str = "go"
    label: str = "Go"

    def discover(self) -> PluginCatalog:
        """Discover available Go versions from go.dev/dl metadata."""
        raise NotImplementedError("catalog discovery is implemented in catalog.py")

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        """Produce Coder parameters for Go version and optional tools."""
        versions = catalog.versions
        default_ver = catalog.defaults.get("version", "latest")
        return [
            ParameterSpec(
                name="go_version",
                display_name="Go Version",
                type="string",
                form_type="dropdown",
                default=default_ver,
                mutable=False,
                order=300,
                options=versions,
                condition="contains(data.coder_parameter.languages.value, 'go')",
            ),
            ParameterSpec(
                name="go_tools",
                display_name="Go Tools",
                type="list(string)",
                form_type="multi-select",
                default=catalog.defaults.get("tools", '["gopls"]'),
                mutable=False,
                order=301,
                condition="contains(data.coder_parameter.languages.value, 'go')",
            ),
        ]

    def runtime_plan(self, selection: dict[str, str | list[str]]) -> RuntimePlan:
        """Produce runtime actions to download and install Go."""
        version = str(selection["version"])
        tools_raw = selection.get("tools", ["gopls"])
        tools: list[str] = [tools_raw] if isinstance(tools_raw, str) else list(tools_raw)
        gopls_version = str(selection.get("gopls_version", "latest"))
        dlv_version = str(selection.get("dlv_version", "latest"))

        root = f"{_CDEV}/toolchains/go/{version}"
        tarball = f"{_CDEV}/downloads/go{version}.linux-amd64.tar.gz"

        # Pull sha256 from selection metadata if available (from go_downloads)
        sha256 = str(selection.get("sha256", ""))

        actions: list[RuntimeAction] = [
            RuntimeAction(
                id="go-ensure-downloads",
                type="ensure_dir",
                values={"path": f"{_CDEV}/downloads"},
            ),
            RuntimeAction(
                id="go-download",
                type="download",
                critical=True,
                values={
                    "url": f"https://go.dev/dl/go{version}.linux-amd64.tar.gz",
                    "dest": tarball,
                    "sha256": sha256 if sha256 else None,
                },
            ),
            RuntimeAction(
                id="go-extract",
                type="extract_tar",
                critical=True,
                creates=f"{root}/bin/go",
                values={
                    "src": tarball,
                    "dest": root,
                    "strip_components": 1,
                },
            ),
            RuntimeAction(
                id="go-path-prepend",
                type="path_prepend",
                critical=True,
                values={"path": f"{root}/bin"},
            ),
            RuntimeAction(
                id="go-verify",
                type="verify_command",
                command=["go", "version"],
            ),
        ]

        if "gopls" in tools:
            actions.append(
                RuntimeAction(
                    id="go-tool-gopls",
                    type="run",
                    command=["go", "install", f"golang.org/x/tools/gopls@{gopls_version}"],
                )
            )
        if "dlv" in tools:
            actions.append(
                RuntimeAction(
                    id="go-tool-dlv",
                    type="run",
                    command=["go", "install", f"github.com/go-delve/delve/cmd/dlv@{dlv_version}"],
                )
            )

        return RuntimePlan(
            plugin=self.id,
            actions=actions,
            env={
                "GOROOT": root,
                "GOBIN": f"{_CDEV}/toolchains/go/bin",
                "GOCACHE": f"{_CDEV}/cache/go/build",
                "GOMODCACHE": f"{_CDEV}/cache/go/pkg/mod",
                "GOPATH": f"{_CDEV}/cache/go/gopath",
            },
        )
