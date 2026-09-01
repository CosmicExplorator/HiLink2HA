"""Minimal Home Assistant import stubs for pure unit tests."""

import sys
from types import ModuleType

homeassistant = ModuleType("homeassistant")
components = ModuleType("homeassistant.components")
http = ModuleType("homeassistant.components.http")
config_entries = ModuleType("homeassistant.config_entries")
core = ModuleType("homeassistant.core")
helpers = ModuleType("homeassistant.helpers")
helpers_typing = ModuleType("homeassistant.helpers.typing")

http.StaticPathConfig = type("StaticPathConfig", (), {})
config_entries.ConfigEntry = type("ConfigEntry", (), {})
core.HomeAssistant = type("HomeAssistant", (), {})
helpers_typing.ConfigType = dict

sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.components", components)
sys.modules.setdefault("homeassistant.components.http", http)
sys.modules.setdefault("homeassistant.config_entries", config_entries)
sys.modules.setdefault("homeassistant.core", core)
sys.modules.setdefault("homeassistant.helpers", helpers)
sys.modules.setdefault("homeassistant.helpers.typing", helpers_typing)
