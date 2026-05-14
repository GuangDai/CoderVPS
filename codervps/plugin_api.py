from __future__ import annotations

from typing import Protocol

from .models import ParameterSpec, PluginCatalog, RuntimePlan


class ToolchainPlugin(Protocol):
    id: str
    label: str

    def discover(self, fixture_dir=None) -> PluginCatalog:
        raise NotImplementedError

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        raise NotImplementedError

    def runtime_plan(self, selection: dict) -> RuntimePlan:
        raise NotImplementedError
