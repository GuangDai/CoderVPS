from __future__ import annotations

from pathlib import Path

from codervps.discovery import rust_channels
from codervps.models import ParameterSpec, PluginCatalog, RuntimeAction, RuntimePlan, VersionEntry


class RustPlugin:
    id = "rust"
    label = "Rust"

    def discover(self, fixture_dir=None) -> PluginCatalog:
        entries = rust_channels(Path(fixture_dir) if fixture_dir else None)
        versions = [
            VersionEntry(
                value=entry["version"],
                label=entry["version"].title() if entry["version"].isalpha() else entry["version"],
                status=entry["status"],
                default=entry["version"] == "stable",
            )
            for entry in entries
        ]
        return PluginCatalog(
            plugin=self.id,
            versions=versions,
            defaults={"toolchain": "stable"},
        )

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        return [
            ParameterSpec(
                name="rust_toolchain",
                display_name="Rust Toolchain",
                type="string",
                form_type="dropdown",
                default="stable",
                mutable=False,
                order=20,
                count="data.coder_parameter.enable_rust.value ? 1 : 0",
                options=catalog.versions,
            ),
        ]

    def runtime_plan(self, selection: dict) -> RuntimePlan:
        toolchain = str(selection.get("toolchain", "stable"))
        return RuntimePlan(
            plugin=self.id,
            env={
                "RUSTUP_HOME": "/home/coder/.cdev/toolchains/rust/rustup",
                "CARGO_HOME": "/home/coder/.cdev/toolchains/rust/cargo",
                "CARGO_INSTALL_ROOT": "/home/coder/.cdev/toolchains/rust/cargo-install",
                "SCCACHE_DIR": "/home/coder/.cdev/cache/sccache",
                "RUSTC_WRAPPER": "sccache",
            },
            actions=[
                RuntimeAction(
                    id="rust-cache-sccache",
                    type="ensure_dir",
                    values={"path": "/home/coder/.cdev/cache/sccache"},
                ),
                RuntimeAction(
                    id="rust-toolchains-dir",
                    type="ensure_dir",
                    values={"path": "/home/coder/.cdev/toolchains/rust/rustup"},
                ),
                RuntimeAction(
                    id="rust-cargo-dir",
                    type="ensure_dir",
                    values={"path": "/home/coder/.cdev/toolchains/rust/cargo"},
                ),
                RuntimeAction(
                    id="rust-install",
                    type="run",
                    command=[
                        "rustup",
                        "toolchain",
                        "install",
                        toolchain,
                        "--profile",
                        "minimal",
                    ],
                    env={
                        "RUSTUP_HOME": "/home/coder/.cdev/toolchains/rust/rustup",
                        "CARGO_HOME": "/home/coder/.cdev/toolchains/rust/cargo",
                    },
                ),
                RuntimeAction(
                    id="rust-components",
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
                    env={
                        "RUSTUP_HOME": "/home/coder/.cdev/toolchains/rust/rustup",
                        "CARGO_HOME": "/home/coder/.cdev/toolchains/rust/cargo",
                    },
                ),
                RuntimeAction(
                    id="rust-default",
                    type="run",
                    command=["rustup", "default", toolchain],
                    env={
                        "RUSTUP_HOME": "/home/coder/.cdev/toolchains/rust/rustup",
                        "CARGO_HOME": "/home/coder/.cdev/toolchains/rust/cargo",
                    },
                ),
                RuntimeAction(
                    id="rust-path",
                    type="path_prepend",
                    values={"path": "/home/coder/.cdev/toolchains/rust/cargo/bin"},
                ),
                RuntimeAction(
                    id="rust-verify",
                    type="verify_command",
                    command=["rustc", "--version"],
                    critical=True,
                ),
            ],
        )
