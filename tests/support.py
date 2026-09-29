"""What the tests share: stand-ins for Home Assistant and aiohttp, and a checker.

The tests run with nothing installed:

    python3 tests/test_planner.py
"""

from __future__ import annotations

from pathlib import Path
import sys
import types

COMPONENT = Path(__file__).resolve().parent.parent / "custom_components" / "mealie_planner"


def _module(name: str) -> types.ModuleType:
    return sys.modules.setdefault(name, types.ModuleType(name))


# --- aiohttp ------------------------------------------------------------------
aiohttp = _module("aiohttp")
aiohttp.ClientError = type("ClientError", (Exception,), {})
aiohttp.ClientSession = object

# --- Home Assistant -----------------------------------------------------------
for name in (
    "homeassistant",
    "homeassistant.core",
    "homeassistant.config_entries",
    "homeassistant.helpers",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.storage",
    "homeassistant.util",
):
    _module(name)

sys.modules["homeassistant.core"].HomeAssistant = object
sys.modules["homeassistant.core"].callback = lambda func: func
sys.modules["homeassistant.config_entries"].ConfigEntry = object
sys.modules["homeassistant.helpers.aiohttp_client"].async_get_clientsession = lambda hass: None


class _Store:
    def __init__(self, hass, version, key):
        self.data = None

    async def async_load(self):
        return self.data

    async def async_save(self, data):
        self.data = data


sys.modules["homeassistant.helpers.storage"].Store = _Store


class _Dt:
    from datetime import date as _date, datetime as _datetime, timezone as _timezone

    @classmethod
    def now(cls):
        return cls._datetime(2026, 10, 1, 12, 0)

    @classmethod
    def utcnow(cls):
        return cls._datetime(2026, 10, 1, 10, 0, tzinfo=cls._timezone.utc)


sys.modules["homeassistant.util"].dt = _Dt

# The integration is mounted as a package without running its __init__, which
# needs the real Home Assistant.
package = types.ModuleType("mealie_planner")
package.__path__ = [str(COMPONENT)]
sys.modules.setdefault("mealie_planner", package)

FAILURES: list[str] = []


def check(label: str, actual, expected) -> None:
    if actual == expected:
        print(f"ok   {label}")
    else:
        print(f"FAIL {label}\n     expected {expected!r}\n     got      {actual!r}")
        FAILURES.append(label)


def done() -> None:
    if FAILURES:
        print(f"\n{len(FAILURES)} failed")
        sys.exit(1)
    print("\nall passed")
