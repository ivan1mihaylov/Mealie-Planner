"""Plan the week's meals in Mealie from rules and the shops' offers."""

from __future__ import annotations

from datetime import timedelta
import logging
from pathlib import Path

from homeassistant.components.frontend import async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.panel_custom import async_register_panel
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_call_later, async_track_time_change
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import DOMAIN
from .mealie import PlannerError
from .service import PlannerService
from .websocket_api import async_register

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_PANEL_PATH = "mealie-planner"
_SCRIPT_URL = "/mealie_planner/panel.js"
_FIRST_CHECK = timedelta(minutes=2)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the static script and WebSocket commands once per Home Assistant run."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(_SCRIPT_URL, str(Path(__file__).parent / "panel.js"), False)]
    )
    async_register(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Load the stored offers and plans, check the shops daily, and show the panel."""
    service = PlannerService(hass, entry)
    await service.async_load()
    entry.runtime_data = service

    async def check_offers(_now=None) -> None:
        try:
            await service.async_refresh_offers()
        except PlannerError as exc:
            _LOGGER.debug("Offer check skipped: %s", exc)
        except Exception:  # noqa: BLE001 - a failed check must not stop the next one
            _LOGGER.exception("Checking the shops' offers failed")

    # Once shortly after start, then every morning. Only brochures not read
    # before are sent to AI, so the daily check is cheap.
    entry.async_on_unload(async_call_later(hass, _FIRST_CHECK, check_offers))
    entry.async_on_unload(async_track_time_change(hass, check_offers, hour=6, minute=7, second=0))
    entry.async_on_unload(entry.add_update_listener(_async_reload))

    integration = await async_get_integration(hass, DOMAIN)
    await async_register_panel(
        hass,
        frontend_url_path=_PANEL_PATH,
        webcomponent_name="mealie-planner-panel",
        sidebar_title="Mealie Planner",
        sidebar_icon="mdi:calendar-heart",
        # The version busts the browser cache after an update from HACS.
        module_url=f"{_SCRIPT_URL}?v={integration.version}",
        config_panel_domain=DOMAIN,
    )
    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove the panel when the integration is removed or reloaded."""
    async_remove_panel(hass, _PANEL_PATH)
    return True
