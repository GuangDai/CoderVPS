from __future__ import annotations

from codervps.plugin_api import ToolchainPlugin

from .cpp import CppPlugin
from .go import GoPlugin
from .python import PythonPlugin
from .rust import RustPlugin

_PLUGIN_TYPES: dict[str, type] = {
    "python": PythonPlugin,
    "rust": RustPlugin,
    "go": GoPlugin,
    "cpp": CppPlugin,
}


def load_plugins(enabled: list[str]) -> list[ToolchainPlugin]:
    """Instantiate enabled plugins in the given order.

    Raises ValueError if any name in ``enabled`` is unknown.
    """
    missing = [name for name in enabled if name not in _PLUGIN_TYPES]
    if missing:
        raise ValueError(f"unknown plugins: {', '.join(missing)}")
    return [_PLUGIN_TYPES[name]() for name in enabled]


def get_plugin(name: str) -> ToolchainPlugin:
    """Return the single plugin instance for *name*.

    Raises ValueError if the plugin name is unknown.
    """
    if name not in _PLUGIN_TYPES:
        raise ValueError(f"unknown plugin: {name}")
    return _PLUGIN_TYPES[name]()


__all__ = ["get_plugin", "load_plugins"]
