"""Minimal Home Assistant import stubs for pure unit tests."""

import sys
from types import ModuleType

homeassistant = ModuleType("homeassistant")
config_entries = ModuleType("homeassistant.config_entries")
core = ModuleType("homeassistant.core")

config_entries.ConfigEntry = type("ConfigEntry", (), {})
core.HomeAssistant = type("HomeAssistant", (), {})

sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.config_entries", config_entries)
sys.modules.setdefault("homeassistant.core", core)
