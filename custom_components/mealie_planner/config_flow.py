"""UI configuration: the Mealie connection and AI, then how planning works."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .addons import async_detect_urls
from .ai import AIClient
from .const import (
    CHAIN_NAMES,
    CHAINS,
    CONF_AI_BASE_URL,
    CONF_AI_KEY,
    CONF_AI_MODEL,
    CONF_MEALIE_TOKEN,
    CONF_MEALIE_URL,
    AI_EFFORTS,
    DEFAULT_AI_BASE_URL,
    DEFAULT_AI_EFFORT,
    DEFAULT_AI_MODEL,
    DEFAULT_BROCHURE_URLS,
    DEFAULT_MAX_PAGES,
    DEFAULT_WEEK_START,
    DOMAIN,
    LISTS_API,
    MODE_AI,
    MODE_LOCAL,
    OPT_AI_EFFORT,
    OPT_BROCHURE_CHAINS,
    OPT_BROCHURE_URL_PREFIX,
    OPT_LIST_ENTRY,
    OPT_MAX_PAGES,
    OPT_PLANNER_MODE,
    OPT_WEB_CHAINS,
    OPT_WEEK_START,
    OPT_ZONE_PREFIX,
)
from .mealie import MealieClient, PlannerError


def _clean_url(value: str) -> str | None:
    url = value.strip().rstrip("/")
    parsed = urlsplit(url)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        return None
    return url


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    def field(key: str, fallback: Any = None) -> dict[str, Any]:
        return {"description": {"suggested_value": defaults.get(key, fallback)}}

    return vol.Schema(
        {
            vol.Required(CONF_MEALIE_URL, **field(CONF_MEALIE_URL)): str,
            vol.Required(CONF_MEALIE_TOKEN, **field(CONF_MEALIE_TOKEN)): str,
            vol.Optional(CONF_AI_BASE_URL, **field(CONF_AI_BASE_URL, DEFAULT_AI_BASE_URL)): str,
            vol.Optional(CONF_AI_KEY, **field(CONF_AI_KEY)): str,
            vol.Optional(CONF_AI_MODEL, **field(CONF_AI_MODEL, DEFAULT_AI_MODEL)): str,
        }
    )


class MealiePlannerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up one Mealie connection and, optionally, an AI."""

    VERSION = 1

    _detected: dict[str, str] | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MealiePlannerOptionsFlow()

    async def _detect(self) -> dict[str, str]:
        if self._detected is None:
            self._detected = await async_detect_urls(self.hass)
        return self._detected

    def _placeholders(self) -> dict[str, str]:
        return {"detected": (self._detected or {}).get(CONF_MEALIE_URL) or "—"}

    async def _validate(self, user_input: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
        errors: dict[str, str] = {}
        data: dict[str, Any] = {
            CONF_MEALIE_URL: _clean_url(user_input[CONF_MEALIE_URL]),
            CONF_MEALIE_TOKEN: user_input[CONF_MEALIE_TOKEN].strip(),
        }
        if data[CONF_MEALIE_URL] is None:
            errors[CONF_MEALIE_URL] = "invalid_url"
        key = (user_input.get(CONF_AI_KEY) or "").strip()
        base = (user_input.get(CONF_AI_BASE_URL) or "").strip()
        model = (user_input.get(CONF_AI_MODEL) or "").strip() or DEFAULT_AI_MODEL
        # AI is on with a key, or with a base URL of its own (Ollama needs no key).
        wants_ai = bool(key) or (base and base.rstrip("/") != DEFAULT_AI_BASE_URL)
        if wants_ai:
            data[CONF_AI_BASE_URL] = _clean_url(base or DEFAULT_AI_BASE_URL)
            data[CONF_AI_KEY] = key
            data[CONF_AI_MODEL] = model
            if data[CONF_AI_BASE_URL] is None:
                errors[CONF_AI_BASE_URL] = "invalid_url"
        if errors:
            return data, errors

        session = async_get_clientsession(self.hass)
        try:
            await MealieClient(session, data[CONF_MEALIE_URL], data[CONF_MEALIE_TOKEN]).check()
        except PlannerError as exc:
            errors["base"] = exc.code if exc.code in ("invalid_auth", "cannot_connect") else "cannot_connect"
            return data, errors
        if wants_ai:
            try:
                await AIClient(session, data[CONF_AI_BASE_URL], key, model, effort=DEFAULT_AI_EFFORT).check()
            except PlannerError as exc:
                errors[CONF_AI_KEY] = "ai_auth" if exc.code == "ai_auth" else "ai_failed"
        return data, errors

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data, errors = await self._validate(user_input)
            if not errors:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Mealie Planner", data=data)
        detected = await self._detect()
        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input or detected),
            errors=errors,
            description_placeholders=self._placeholders(),
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data, errors = await self._validate(user_input)
            if not errors:
                return self.async_update_reload_and_abort(entry, data=data)
        detected = await self._detect()
        current = {key: value for key, value in entry.data.items() if value}
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(user_input or {**detected, **current}),
            errors=errors,
            description_placeholders=self._placeholders(),
        )


def _guess_zone(hass, chain: str) -> str | None:
    """A zone named after the chain, the way HomeBasket Lists matches shops."""
    wanted = CHAIN_NAMES[chain].casefold()
    for state in hass.states.async_all("zone"):
        name = str(state.attributes.get("friendly_name") or state.object_id).casefold()
        if wanted in name or wanted in state.object_id.casefold():
            return state.entity_id
    return None


class MealiePlannerOptionsFlow(OptionsFlow):
    """Planner mode, sources, shops as zones and the shopping list."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            options = {key: value for key, value in user_input.items() if value not in (None, "")}
            for key in (OPT_WEEK_START, OPT_MAX_PAGES):
                if key in options:
                    options[key] = int(options[key])
            return self.async_create_entry(data=options)

        current = self.config_entry.options
        has_ai = bool(self.config_entry.data.get(CONF_AI_BASE_URL))
        chains = [selector.SelectOptionDict(value=chain, label=CHAIN_NAMES[chain]) for chain in CHAINS]
        fields: dict[Any, Any] = {
            vol.Required(OPT_PLANNER_MODE, default=current.get(OPT_PLANNER_MODE, MODE_AI if has_ai else MODE_LOCAL)): selector.SelectSelector(
                selector.SelectSelectorConfig(options=[MODE_LOCAL, MODE_AI], translation_key="planner_mode")
            ),
            vol.Optional(OPT_WEB_CHAINS, default=current.get(OPT_WEB_CHAINS, list(CHAINS))): selector.SelectSelector(
                selector.SelectSelectorConfig(options=chains, multiple=True)
            ),
            vol.Optional(OPT_BROCHURE_CHAINS, default=current.get(OPT_BROCHURE_CHAINS, list(CHAINS) if has_ai else [])): selector.SelectSelector(
                selector.SelectSelectorConfig(options=chains, multiple=True)
            ),
        }
        for chain in CHAINS:
            key = f"{OPT_ZONE_PREFIX}{chain}"
            suggested = current.get(key) or _guess_zone(self.hass, chain)
            fields[vol.Optional(key, description={"suggested_value": suggested})] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="zone")
            )
        api = self.hass.data.get(LISTS_API)
        lists = list(getattr(api, "lists", []) or []) if api is not None else []
        if lists:
            fields[vol.Optional(OPT_LIST_ENTRY, description={"suggested_value": current.get(OPT_LIST_ENTRY)})] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[selector.SelectOptionDict(value=item["entry_id"], label=item["name"]) for item in lists]
                )
            )
        if has_ai:
            fields[vol.Required(OPT_AI_EFFORT, default=current.get(OPT_AI_EFFORT, DEFAULT_AI_EFFORT))] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(AI_EFFORTS), translation_key="ai_effort")
            )
        fields[vol.Required(OPT_WEEK_START, default=str(current.get(OPT_WEEK_START, DEFAULT_WEEK_START)))] = selector.SelectSelector(
            selector.SelectSelectorConfig(options=[str(day) for day in range(7)], translation_key="weekday")
        )
        fields[vol.Required(OPT_MAX_PAGES, default=current.get(OPT_MAX_PAGES, DEFAULT_MAX_PAGES))] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=120, step=1, mode=selector.NumberSelectorMode.BOX)
        )
        for chain in CHAINS:
            key = f"{OPT_BROCHURE_URL_PREFIX}{chain}"
            fields[vol.Optional(key, description={"suggested_value": current.get(key) or DEFAULT_BROCHURE_URLS[chain]})] = str
        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))
