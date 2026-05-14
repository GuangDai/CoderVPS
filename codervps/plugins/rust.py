from __future__ import annotations

from codervps.models import ParameterSpec, PluginCatalog, RuntimeAction, RuntimePlan

_CDEV = "/workspace/.cdev"


class RustPlugin:
    id: str = "rust"
    label: str = "Rust"

    def discover(self) -> PluginCatalog:
        """Discover available Rust toolchains from the rustup catalog."""
        raise NotImplementedError("catalog discovery is implemented in catalog.py")

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        """Produce Coder parameters for Rust toolchain selection."""
        versions = catalog.versions
        default_tc = catalog.defaults.get("toolchain", "stable")
        return [
            ParameterSpec(
                name="rust_toolchain",
                display_name="Rust Toolchain",
                type="string",
                form_type="dropdown",
                default=default_tc,
                mutable=False,
                order=200,
                options=versions,
                condition="contains(data.coder_parameter.languages.value, 'rust')",
            ),
        ]

    def runtime_plan(self, selection: dict[str, str | list[str]]) -> RuntimePlan:
        """Produce runtime actions to install the selected Rust toolchain."""
        toolchain = str(selection.get("toolchain", "stable"))

        return RuntimePlan(
            plugin=self.id,
            env={
                "RUSTUP_HOME": f"{_CDEV}/toolchains/rust/rustup",
                "CARGO_HOME": f"{_CDEV}/toolchains/rust/cargo",
                "CARGO_INSTALL_ROOT": f"{_CDEV}/toolchains/rust/cargo-install",
                "SCCACHE_DIR": f"{_CDEV}/cache/sccache",
                "RUSTC_WRAPPER": "sccache",
            },
            actions=[
                RuntimeAction(
                    id="rust-ensure-sccache-cache",
                    type="ensure_dir",
                    values={"path": f"{_CDEV}/cache/sccache"},
                ),
                RuntimeAction(
                    id="rust-install-toolchain",
                    type="run",
                    command=["rustup", "toolchain", "install", toolchain, "--profile", "minimal"],
                ),
                RuntimeAction(
                    id="rust-add-components",
                    type="run",
                    command=[
                        "rustup",
                        "component",
                        "add",
                        "rustfmt",
                        "clippy",
                        "rust-src",
                        "--toolchain",
                        toolchain,
                    ],
                ),
                RuntimeAction(
                    id="rust-set-default",
                    type="run",
                    command=["rustup", "default", toolchain],
                ),
                RuntimeAction(
                    id="rust-verify",
                    type="verify_command",
                    command=["rustc", "--version"],
                ),
            ],
        )
