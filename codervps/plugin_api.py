from __future__ import annotations

from typing import Protocol

from .models import ParameterSpec, PluginCatalog, RuntimePlan


class ToolchainPlugin(Protocol):
    """Protocol for language toolchain plugins.

    Each language plugin (python, rust, go, cpp) implements this interface
    to provide catalog discovery, Coder template parameters, and runtime
    action plans for workspace startup.
    """

    id: str
    label: str

    def discover(self) -> PluginCatalog:
        """Discover available versions from upstream metadata sources."""
        ...

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        """Produce Coder template parameter definitions for this language."""
        ...

    def runtime_plan(self, selection: dict[str, str | list[str]]) -> RuntimePlan:
        """Produce a runtime action plan for installing/activating this language."""
        ...


__all__ = ["ToolchainPlugin"]
