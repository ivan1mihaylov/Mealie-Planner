"""Find a running Mealie add-on to prefill the config flow."""

from __future__ import annotations

import asyncio
import logging

from aiohttp import ClientError, ClientSession

from homeassistant.components.network import async_get_source_ip
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.hassio import is_hassio

from .const import CONF_MEALIE_URL

_LOGGER = logging.getLogger(__name__)
_PROBE_TIMEOUT = 5


async def async_detect_urls(hass: HomeAssistant) -> dict[str, str]:
    """Return the working URL of a started Mealie add-on, if there is one."""
    if not is_hassio(hass):
        return {}
    # Imported here because hassio only loads on Home Assistant OS/Supervised.
    from homeassistant.components.hassio import get_supervisor_client

    client = get_supervisor_client(hass)
    try:
        addons = await client.addons.list()
    except Exception:  # noqa: BLE001 - detection is best effort
        _LOGGER.debug("Could not list add-ons", exc_info=True)
        return {}

    session = async_get_clientsession(hass)
    lan_host = await _lan_host(hass)
    found: dict[str, str] = {}
    for key, kind, probe in ((CONF_MEALIE_URL, "mealie", _is_mealie),):
        for addon in addons:
            if _kind(addon) != kind or addon.state != "started":
                continue
            try:
                info = await client.addons.addon_info(addon.slug)
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Could not read add-on %s", addon.slug, exc_info=True)
                continue
            candidates = _candidates(info.hostname, info.network or {}, info.host_network, lan_host)
            results = await asyncio.gather(*(probe(session, url) for url in candidates))
            if url := next((url for url, ok in zip(candidates, results) if ok), None):
                found[key] = url
                break
    return found


def _kind(addon) -> str | None:
    """Which add-on this is; "Social to Mealie" must not count as Mealie."""
    text = f"{addon.slug} {addon.name}".lower()
    if "social" in text and "mealie" in text:
        return "social"
    if "mealie" in text:
        return "mealie"
    return None


async def _lan_host(hass: HomeAssistant) -> str | None:
    """Home Assistant's LAN IP, reachable from Core and from browsers."""
    try:
        return await async_get_source_ip(hass)
    except Exception:  # noqa: BLE001
        _LOGGER.debug("Could not determine the LAN address", exc_info=True)
        return None


def _candidates(
    hostname: str, network: dict[str, int | None], host_network: bool, lan_host: str | None
) -> list[str]:
    """Prefer a LAN address that browsers can open too, then the internal name."""
    urls: list[str] = []
    for container, host_port in network.items():
        port, _, protocol = container.partition("/")
        if protocol not in ("", "tcp"):
            continue
        published = port if host_network else host_port
        if lan_host and published:
            urls.append(f"http://{lan_host}:{published}")
        urls.append(f"http://{hostname}:{port}")
    return list(dict.fromkeys(urls))


async def _get_json(session: ClientSession, url: str, params: dict | None = None):
    try:
        async with asyncio.timeout(_PROBE_TIMEOUT):
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                return await response.json(content_type=None)
    except (TimeoutError, ClientError, ValueError):
        return None


async def _is_mealie(session: ClientSession, url: str) -> bool:
    body = await _get_json(session, f"{url}/api/app/about")
    return isinstance(body, dict) and "version" in body


async def async_mealie_panel(hass: HomeAssistant) -> dict[str, str] | None:
    """Slug and ingress URL of a started Mealie add-on with a sidebar panel."""
    if not is_hassio(hass):
        return None
    from homeassistant.components.hassio import get_supervisor_client

    client = get_supervisor_client(hass)
    try:
        for addon in await client.addons.list():
            if _kind(addon) != "mealie" or addon.state != "started":
                continue
            info = await client.addons.addon_info(addon.slug)
            if info.ingress_url:
                return {"slug": addon.slug, "ingress_url": info.ingress_url}
    except Exception:  # noqa: BLE001 - the panel falls back to a browser tab
        _LOGGER.debug("Could not look up the Mealie add-on", exc_info=True)
    return None
