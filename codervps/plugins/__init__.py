from __future__ import annotations

from codervps.languages import LANGUAGE_IDS
from codervps.plugin_api import ToolchainPlugin

from .cpp import CppPlugin
from .go import GoPlugin
from .python import PythonPlugin
from .rust import RustPlugin

_PLUGIN_CLASSES = (PythonPlugin, RustPlugin, GoPlugin, CppPlugin)
_PLUGIN_TYPES: dict[str, type] = {plugin.id: plugin for plugin in _PLUGIN_CLASSES}

if tuple(_PLUGIN_TYPES) != LANGUAGE_IDS:
    raise RuntimeError("plugin registry order must match codervps.languages.LANGUAGE_IDS")


def load_plugins(enabled: list[str]) -> list[ToolchainPlugin]:
    missing = [name for name in enabled if name not in _PLUGIN_TYPES]
    if missing:
        raise ValueError(f"unknown plugins: {', '.join(missing)}")
    return [_PLUGIN_TYPES[name]() for name in enabled]
