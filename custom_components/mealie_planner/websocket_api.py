"""Authenticated browser commands for the Mealie Planner panel."""

from __future__ import annotations

from datetime import date
import functools
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api as ws
from homeassistant.core import HomeAssistant, callback

from .const import CHAINS, DOMAIN, MODE_AI, MODE_LOCAL
from .mealie import PlannerError
from .rules import presets as rules_presets
from .service import PlannerService

_LOGGER = logging.getLogger(__name__)


def _service(hass: HomeAssistant) -> PlannerService:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        return entry.runtime_data
    raise PlannerError("Интеграцията Mealie Planner не е заредена.", "not_loaded")


def _week(service: PlannerService, msg: dict[str, Any]) -> date:
    if msg.get("week"):
        start = date.fromisoformat(msg["week"])
        return start
    return service.week_start(1)


def _handler(func):
    """Send the result, or the error the panel can show."""

    @functools.wraps(func)
    async def wrapper(hass: HomeAssistant, connection: ws.ActiveConnection, msg: dict[str, Any]) -> None:
        try:
            result = await func(hass, _service(hass), msg, connection)
        except PlannerError as exc:
            connection.send_error(msg["id"], exc.code, str(exc))
            return
        except ValueError as exc:
            connection.send_error(msg["id"], "invalid", str(exc))
            return
        connection.send_result(msg["id"], result)

    return wrapper


_WEEK = vol.Optional("week")


@callback
def async_register(hass: HomeAssistant) -> None:
    for handler in (
        state, offers, refresh, rescan, add_brochure, probe, settings_get, settings_set,
        organizers, plan_get, plan_generate, plan_update_slot, plan_move_slot, plan_save,
        recipes_pick, shopping_alternatives, shopping_choose, shopping_check, shopping_add,
        offer_add,
    ):
        ws.async_register_command(hass, handler)


@ws.websocket_command({vol.Required("type"): f"{DOMAIN}/state"})
@ws.async_response
@_handler
async def state(hass, service: PlannerService, msg, connection=None):
    return {
        "ai": service.ai is not None,
        "mode": service.mode,
        "week": service.week_start(1).isoformat(),
        "this_week": service.week_start(0).isoformat(),
        "settings": service.settings,
        "presets": rules_presets(),
        "lists": service.lists_info(),
        "admin": bool(connection and connection.user and connection.user.is_admin),
    }


@ws.websocket_command({vol.Required("type"): f"{DOMAIN}/offers"})
@ws.async_response
@_handler
async def offers(hass, service: PlannerService, msg, connection=None):
    return service.offers_view()


@ws.websocket_command({vol.Required("type"): f"{DOMAIN}/offers/refresh"})
@ws.require_admin
@ws.async_response
@_handler
async def refresh(hass, service: PlannerService, msg, connection=None):
    if service.refreshing:
        return {"started": False}

    async def run() -> None:
        try:
            await service.async_refresh_offers()
        except PlannerError as exc:
            _LOGGER.debug("Refresh skipped: %s", exc)

    # Reading a brochure with AI takes minutes; the panel watches for the end.
    hass.async_create_background_task(run(), f"{DOMAIN} offers refresh")
    service.refreshing = True
    return {"started": True}


@ws.websocket_command({vol.Required("type"): f"{DOMAIN}/offers/rescan", vol.Required("source_id"): str})
@ws.require_admin
@ws.async_response
@_handler
async def rescan(hass, service: PlannerService, msg, connection=None):
    return await service.async_rescan(msg["source_id"])


@ws.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/offers/add_url",
        vol.Required("chain"): vol.In(CHAINS),
        vol.Required("url"): vol.All(str, vol.Length(min=8, max=2000)),
        vol.Optional("title"): vol.Any(str, None),
        vol.Optional("valid_from"): vol.Any(str, None),
        vol.Optional("valid_to"): vol.Any(str, None),
    }
)
@ws.require_admin
@ws.async_response
@_handler
async def add_brochure(hass, service: PlannerService, msg, connection=None):
    if service.ai is None:
        raise PlannerError("За четене на брошура е нужен AI.", "ai_missing")
    return await service.async_add_brochure(msg["chain"], msg["url"], msg.get("title"), msg.get("valid_from"), msg.get("valid_to"))


@ws.websocket_command({vol.Required("type"): f"{DOMAIN}/offers/probe"})
@ws.require_admin
@ws.async_response
@_handler
async def probe(hass, service: PlannerService, msg, connection=None):
    return await service.async_probe()


@ws.websocket_command({vol.Required("type"): f"{DOMAIN}/settings/get"})
@ws.async_response
@_handler
async def settings_get(hass, service: PlannerService, msg, connection=None):
    return service.settings


@ws.websocket_command({vol.Required("type"): f"{DOMAIN}/settings/set", vol.Required("settings"): dict})
@ws.require_admin
@ws.async_response
@_handler
async def settings_set(hass, service: PlannerService, msg, connection=None):
    return await service.async_set_settings(msg["settings"])


@ws.websocket_command({vol.Required("type"): f"{DOMAIN}/mealie/organizers"})
@ws.async_response
@_handler
async def organizers(hass, service: PlannerService, msg, connection=None):
    return await service.async_organizers()


@ws.websocket_command({vol.Required("type"): f"{DOMAIN}/plan/get", _WEEK: str})
@ws.async_response
@_handler
async def plan_get(hass, service: PlannerService, msg, connection=None):
    return await service.async_week(_week(service, msg))


@ws.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/plan/generate",
        _WEEK: str,
        vol.Optional("mode"): vol.In((MODE_LOCAL, MODE_AI)),
        vol.Optional("seed"): int,
        vol.Optional("replace_saved", default=False): bool,
    }
)
@ws.async_response
@_handler
async def plan_generate(hass, service: PlannerService, msg, connection=None):
    return await service.async_generate(
        _week(service, msg), mode=msg.get("mode"), seed=msg.get("seed"), replace_saved=msg["replace_saved"]
    )


@ws.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/plan/update_slot",
        _WEEK: str,
        vol.Required("slot"): str,
        vol.Optional("recipe_id"): vol.Any(str, None),
        vol.Optional("locked"): bool,
    }
)
@ws.async_response
@_handler
async def plan_update_slot(hass, service: PlannerService, msg, connection=None):
    if "recipe_id" not in msg and "locked" not in msg:
        raise PlannerError("Nothing to change.", "invalid")
    return await service.async_update_slot(
        _week(service, msg),
        msg["slot"],
        set_recipe="recipe_id" in msg,
        recipe_id=msg.get("recipe_id") or None,
        locked=msg.get("locked"),
    )


@ws.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/plan/move_slot", _WEEK: str, vol.Required("source"): str, vol.Required("target"): str}
)
@ws.async_response
@_handler
async def plan_move_slot(hass, service: PlannerService, msg, connection=None):
    return await service.async_move_slot(_week(service, msg), msg["source"], msg["target"])


@ws.websocket_command({vol.Required("type"): f"{DOMAIN}/plan/save", _WEEK: str})
@ws.async_response
@_handler
async def plan_save(hass, service: PlannerService, msg, connection=None):
    return await service.async_save(_week(service, msg))


@ws.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/recipes/pick", _WEEK: str, vol.Required("slot"): str, vol.Optional("query"): vol.Any(str, None)}
)
@ws.async_response
@_handler
async def recipes_pick(hass, service: PlannerService, msg, connection=None):
    return service.picker(_week(service, msg), msg["slot"], (msg.get("query") or "").strip() or None)


@ws.websocket_command({vol.Required("type"): f"{DOMAIN}/shopping/alternatives", _WEEK: str, vol.Required("key"): str})
@ws.async_response
@_handler
async def shopping_alternatives(hass, service: PlannerService, msg, connection=None):
    return await service.async_alternatives(_week(service, msg), msg["key"])


@ws.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/shopping/choose", _WEEK: str, vol.Required("key"): str, vol.Optional("offer_id"): vol.Any(str, None)}
)
@ws.async_response
@_handler
async def shopping_choose(hass, service: PlannerService, msg, connection=None):
    return await service.async_choose(_week(service, msg), msg["key"], msg.get("offer_id"))


@ws.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/shopping/check", _WEEK: str, vol.Required("keys"): [str], vol.Required("checked"): bool}
)
@ws.async_response
@_handler
async def shopping_check(hass, service: PlannerService, msg, connection=None):
    return await service.async_check(_week(service, msg), msg["keys"], msg["checked"])


@ws.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/shopping/add", _WEEK: str, vol.Required("keys"): [str], vol.Optional("entry_id"): vol.Any(str, None)}
)
@ws.async_response
@_handler
async def shopping_add(hass, service: PlannerService, msg, connection=None):
    view = await service.async_view(_week(service, msg))
    wanted = set(msg["keys"])
    items = [item for item in view["basket"] if item["key"] in wanted]
    return await service.async_add_to_list(items, msg.get("entry_id"))


@ws.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/offer/add_to_list", vol.Required("offer_id"): str, vol.Optional("entry_id"): vol.Any(str, None)}
)
@ws.async_response
@_handler
async def offer_add(hass, service: PlannerService, msg, connection=None):
    return await service.async_add_offer(msg["offer_id"], msg.get("entry_id"))
