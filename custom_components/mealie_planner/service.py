"""Everything the panel asks for: offers, the week's plan and its products."""

from __future__ import annotations

import asyncio
from datetime import date, timedelta
import hashlib
import logging
import os
from urllib.parse import urlsplit
from random import randrange
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession, async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from . import crops, extraction, planner, rules as rules_mod, shopping
from .ai import AIClient
from .const import (
    BILLA,
    CHAIN_NAMES,
    CHAINS,
    CONF_AI_BASE_URL,
    CONF_AI_KEY,
    CONF_AI_MODEL,
    CONF_MEALIE_TOKEN,
    CONF_MEALIE_URL,
    DEFAULT_AI_BASE_URL,
    DEFAULT_AI_EFFORT,
    DEFAULT_AI_MODEL,
    DEFAULT_BROCHURE_TITLES,
    DEFAULT_BROCHURE_URLS,
    DEFAULT_MAX_PAGES,
    DEFAULT_WEEK_START,
    DOMAIN,
    KAUFLAND,
    LIDL,
    LISTS_API,
    MEAL_TYPES,
    MODE_AI,
    MODE_LOCAL,
    OPT_AI_EFFORT,
    OPT_BROCHURE_CHAINS,
    OPT_BROCHURE_TITLE_PREFIX,
    OPT_BROCHURE_URL_PREFIX,
    OPT_LIST_ENTRY,
    OPT_MAX_PAGES,
    OPT_PLANNER_MODE,
    OPT_WEB_CHAINS,
    OPT_WEEK_START,
    OPT_ZONE_PREFIX,
    PICTURES_DIR,
    PICTURES_URL,
)
from .mealie import MealieClient, PlannerError
from .offers import OfferBook, OfferIndex
from .recipes import RecipeIndex
from .sources import billa, brochures, kaufland, lidl
from .sources import common as source_common
from .sources.common import MAX_HEADER, SourceError, describe_page, fetch_each_profile
from .text import iso

_LOGGER = logging.getLogger(__name__)

_STORE_VERSION = 1
_RECIPES_FRESH = timedelta(minutes=30)
_AI_CANDIDATES = 120


def default_settings() -> dict[str, Any]:
    return {
        "rules": rules_mod.presets(),
        # Weekday (0 = Monday) to the meal types planned that day.
        "slots": {str(day): ["dinner"] for day in range(7)},
        "recent_weeks": 2,
    }


class PlannerService:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.session = async_get_clientsession(hass)
        self.shop_session = _shop_session(hass)
        data = entry.data
        self.mealie = MealieClient(self.session, data[CONF_MEALIE_URL], data[CONF_MEALIE_TOKEN])
        self.ai: AIClient | None = None
        if data.get(CONF_AI_KEY) or (data.get(CONF_AI_BASE_URL) and data[CONF_AI_BASE_URL] != DEFAULT_AI_BASE_URL):
            self.ai = AIClient(
                self.session,
                data.get(CONF_AI_BASE_URL) or DEFAULT_AI_BASE_URL,
                data.get(CONF_AI_KEY) or "",
                data.get(CONF_AI_MODEL) or DEFAULT_AI_MODEL,
                effort=_effort(entry.options.get(OPT_AI_EFFORT, DEFAULT_AI_EFFORT)),
            )
        self._offers_store: Store = Store(hass, _STORE_VERSION, f"{DOMAIN}.offers")
        self._recipes_store: Store = Store(hass, _STORE_VERSION, f"{DOMAIN}.recipes")
        self._settings_store: Store = Store(hass, _STORE_VERSION, f"{DOMAIN}.settings")
        self._drafts_store: Store = Store(hass, _STORE_VERSION, f"{DOMAIN}.drafts")
        self.book = OfferBook()
        self.recipes = RecipeIndex()
        self.settings = default_settings()
        self.drafts: dict[str, dict[str, Any]] = {}
        self._recipes_read: Any = None
        self._refresh_lock = asyncio.Lock()
        self._recipes_lock = asyncio.Lock()
        self.refreshing = False
        self.last_refresh: dict[str, Any] = {}

    async def async_load(self) -> None:
        self.book = OfferBook(await self._offers_store.async_load())
        # The fetchers keep what worked in PREFERRED; the book stores it.
        source_common.PREFERRED.update(self.book.profiles)
        # Offers read before pictures were cut out show their brochure page.
        self.book.fill_page_images()
        self.book.profiles = source_common.PREFERRED
        self.recipes = RecipeIndex(await self._recipes_store.async_load())
        stored = await self._settings_store.async_load()
        if stored:
            self.settings = {**default_settings(), **stored}
        self.drafts = (await self._drafts_store.async_load() or {}).get("weeks", {})

    # --- Options --------------------------------------------------------------
    @property
    def options(self) -> dict[str, Any]:
        return self.entry.options

    @property
    def mode(self) -> str:
        wanted = self.options.get(OPT_PLANNER_MODE, MODE_LOCAL)
        return MODE_AI if wanted == MODE_AI and self.ai else MODE_LOCAL

    @property
    def web_chains(self) -> list[str]:
        return list(self.options.get(OPT_WEB_CHAINS, CHAINS))

    @property
    def brochure_chains(self) -> list[str]:
        return list(self.options.get(OPT_BROCHURE_CHAINS, [])) if self.ai else []

    def _brochure_title(self, chain: str) -> str:
        """The text a brochure's title must have to be read; empty reads them all."""
        key = f"{OPT_BROCHURE_TITLE_PREFIX}{chain}"
        if key in self.options:
            return str(self.options.get(key) or "")
        return DEFAULT_BROCHURE_TITLES[chain]

    def zone(self, chain: str | None) -> str | None:
        return self.options.get(f"{OPT_ZONE_PREFIX}{chain}") if chain else None

    def today(self) -> date:
        return dt_util.now().date()

    # --- Offers ---------------------------------------------------------------
    async def async_refresh_offers(self, *, brochures_too: bool = True) -> dict[str, Any]:
        """Read the chains' offer pages, and any brochure not read before."""
        if self._refresh_lock.locked():
            raise PlannerError("Проверката на промоциите вече тече.", "busy")
        async with self._refresh_lock:
            self.refreshing = True
            try:
                return await self._refresh(brochures_too)
            finally:
                self.refreshing = False

    async def _refresh(self, brochures_too: bool) -> dict[str, Any]:
        today = self.today()
        now = dt_util.utcnow().isoformat()
        summary: dict[str, Any] = {"web": {}, "brochures": {}, "tokens": {"prompt": 0, "completion": 0}}
        removed = self.book.purge(today)
        adapters = {KAUFLAND: kaufland.fetch, BILLA: billa.fetch}
        for chain in self.web_chains:
            try:
                if chain == LIDL:
                    found = await lidl.fetch(self.shop_session, today, self.book.web_offers_by_url(LIDL))
                else:
                    found = await adapters[chain](self.shop_session, today)
            except (SourceError, KeyError) as exc:
                _LOGGER.warning("%s offers could not be read: %s", CHAIN_NAMES.get(chain, chain), exc)
                self.book.replace_web(chain, [], now, error=str(exc))
                summary["web"][chain] = {"error": str(exc)}
                continue
            found = [offer for offer in found if not offer.get("valid_to") or date.fromisoformat(offer["valid_to"]) >= today]
            unknown = self.book.replace_web(chain, found, now)
            if unknown and self.ai:
                try:
                    tokens = await extraction.name_offers(self.ai, unknown)
                    self.book.add_usage(tokens)
                    self._add(summary["tokens"], tokens)
                except PlannerError as exc:
                    _LOGGER.warning("Naming %s offers with AI failed: %s", chain, exc)
            summary["web"][chain] = {"count": len(found), "named_by_ai": len(unknown) if self.ai else 0}
            await self._offers_store.async_save(self.book.as_dict())

        if brochures_too:
            for chain in self.brochure_chains:
                url = self.options.get(f"{OPT_BROCHURE_URL_PREFIX}{chain}") or DEFAULT_BROCHURE_URLS[chain]
                try:
                    found_brochures = brochures.titled(
                        await brochures.find(self.shop_session, chain, url, today), self._brochure_title(chain)
                    )
                except SourceError as exc:
                    summary["brochures"][chain] = {"error": str(exc)}
                    continue
                new = [brochure for brochure in found_brochures if not self.book.knows(brochure["id"])]
                summary["brochures"][chain] = {"found": len(found_brochures), "read": 0}
                for brochure in new:
                    result = await self._read_brochure(brochure, now)
                    self._add(summary["tokens"], result.get("tokens") or {})
                    summary["brochures"][chain]["read"] += 1
        await self._offers_store.async_save(self.book.as_dict())
        await self._forget_pictures()
        summary["expired"] = removed
        summary["at"] = now
        self.last_refresh = summary
        return summary

    @staticmethod
    def _add(total: dict[str, int], tokens: dict[str, int]) -> None:
        for key in ("prompt", "completion"):
            total[key] = total.get(key, 0) + int(tokens.get(key, 0))

    async def _read_brochure(self, brochure: dict[str, Any], when: str) -> dict[str, Any]:
        if self.ai is None:
            raise PlannerError("За четене на брошури е нужен AI.", "ai_missing")
        max_pages = int(self.options.get(OPT_MAX_PAGES, DEFAULT_MAX_PAGES))
        try:
            offers, tokens = await extraction.read_brochure(
                self.ai, self.shop_session, brochure, max_pages, cropper=self._keep_picture
            )
        except (PlannerError, SourceError) as exc:
            _LOGGER.warning("Brochure %s could not be read: %s", brochure.get("title"), exc)
            self.book.add_brochure(brochure, [], when, error=str(exc))
            await self._offers_store.async_save(self.book.as_dict())
            return {"error": str(exc)}
        added = self.book.add_brochure(brochure, offers, when, tokens)
        await self._offers_store.async_save(self.book.as_dict())
        return {"added": added, "tokens": tokens}

    async def async_rescan(self, source_id: str) -> dict[str, Any]:
        source = self.book.sources.get(source_id)
        if not source or not source.get("brochure"):
            raise PlannerError("Няма такава брошура.", "not_found")
        brochure = source["brochure"]
        self.book.forget(source_id)
        result = await self._read_brochure(brochure, dt_util.utcnow().isoformat())
        await self._forget_pictures()
        return result

    # --- Pictures cut out of brochure pages ---------------------------------
    def _pictures_dir(self) -> str:
        return self.hass.config.path(*PICTURES_DIR)

    async def _keep_picture(self, data: bytes, box: tuple, offer_id: str) -> str | None:
        """Cut an offer's picture out of its page and keep it; its URL, or None."""
        picture = await self.hass.async_add_executor_job(crops.crop, data, box)
        if not picture:
            return None
        name = crops.file_name(offer_id)
        folder = self._pictures_dir()

        def save() -> None:
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, name), "wb") as file:
                file.write(picture)

        await self.hass.async_add_executor_job(save)
        # The version makes browsers fetch a picture read again.
        return f"{PICTURES_URL}/{name}?v={hashlib.sha1(picture).hexdigest()[:8]}"

    async def _forget_pictures(self) -> None:
        """Delete the pictures of offers that have ended or were read again."""
        keep = {crops.file_name(offer_id) for offer_id in self.book.offers}
        folder = self._pictures_dir()

        def clean() -> None:
            if not os.path.isdir(folder):
                return
            for name in os.listdir(folder):
                if name.endswith(".jpg") and name not in keep:
                    os.remove(os.path.join(folder, name))

        await self.hass.async_add_executor_job(clean)

    async def async_add_brochure(self, chain: str, url: str, title: str | None, valid_from: str | None, valid_to: str | None) -> dict[str, Any]:
        """Read a brochure the user points at: a PDF, an image, or a page linking to one."""
        today = self.today()
        lower = url.lower().split("?")[0]
        if lower.endswith(".pdf"):
            found = [brochures.pdf_brochure(chain, url, today, title)]
        elif lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
            found = [{"id": brochures.brochure_id(chain, url), "chain": chain, "title": title or url.rsplit("/", 1)[-1], "valid_from": None, "valid_to": None, "pages": [url], "pdf": None}]
        else:
            try:
                found = await brochures.find(self.shop_session, chain, url, today)
            except SourceError as exc:
                raise PlannerError(f"Страницата не се чете: {exc}", "not_found") from exc
        if not found:
            raise PlannerError("На този адрес няма брошура.", "not_found")
        results = []
        for brochure in found:
            brochure["valid_from"] = iso(valid_from) or brochure.get("valid_from")
            brochure["valid_to"] = iso(valid_to) or brochure.get("valid_to")
            brochure["url"] = url
            if title:
                brochure["title"] = title
            results.append(await self._read_brochure(brochure, dt_util.utcnow().isoformat()))
        return {"brochures": results}

    async def async_probe(self) -> dict[str, Any]:
        """What each source finds right now, without keeping anything or spending AI."""
        today = self.today()
        report: dict[str, Any] = {}
        for chain, fetch in ((KAUFLAND, kaufland.fetch), (LIDL, lidl.fetch), (BILLA, billa.fetch)):
            try:
                found = await fetch(self.shop_session, today)
                dated = sum(1 for offer in found if offer.get("valid_to"))
                base = {KAUFLAND: kaufland.URL, LIDL: lidl.BASE, BILLA: billa.BASE}[chain]
                report[f"{chain}:web"] = {
                    "count": len(found), "with_dates": dated, "profile": self._profile(base), "samples": found[:3],
                }
                if not found or not dated:
                    report[f"{chain}:web"]["page"] = await self._diagnose(chain)
            except SourceError as exc:
                report[f"{chain}:web"] = {"error": str(exc), "page": await self._diagnose(chain)}
            url = self.options.get(f"{OPT_BROCHURE_URL_PREFIX}{chain}") or DEFAULT_BROCHURE_URLS[chain]
            try:
                every = await brochures.find(self.shop_session, chain, url, today)
                found_brochures = brochures.titled(every, self._brochure_title(chain))
                report[f"{chain}:brochures"] = {
                    "url": url,
                    "title_filter": self._brochure_title(chain) or None,
                    "all_titles": [brochure.get("title") for brochure in every],
                    "page": None if found_brochures else await self._diagnose(chain, url, f"{chain}-brochures"),
                    "count": len(found_brochures),
                    "samples": [
                        {**brochure, "pages": len(brochure.get("pages") or [])} for brochure in found_brochures[:3]
                    ],
                }
            except SourceError as exc:
                report[f"{chain}:brochures"] = {"url": url, "error": str(exc), "page": await self._diagnose(chain, url, f"{chain}-brochures")}
        # Keep the ways of asking that worked, for the next check.
        await self._offers_store.async_save(self.book.as_dict())
        return report

    async def _diagnose(self, chain: str, url: str | None = None, name: str | None = None) -> dict[str, Any]:
        """Ask for a page every way there is, and keep each answer to send in.

        Shows which way of asking gets the whole page, and which one the
        source uses now.
        """
        url = url or {KAUFLAND: kaufland.URL, LIDL: lidl.BASE, BILLA: billa.BASE}[chain]
        pages = await fetch_each_profile(self.shop_session, url)
        folder = self.hass.config.path("mealie_planner_debug")

        def save() -> None:
            os.makedirs(folder, exist_ok=True)
            for profile, html, _ in pages:
                if html is not None:
                    with open(os.path.join(folder, f"{name or chain}-{profile}.html"), "w", encoding="utf-8") as file:
                        file.write(html)

        await self.hass.async_add_executor_job(save)
        profiles: dict[str, Any] = {}
        for profile, html, error in pages:
            if html is None:
                profiles[profile] = {"error": error}
            else:
                profiles[profile] = {"saved_to": os.path.join(folder, f"{name or chain}-{profile}.html"), **describe_page(html)}
        return {"url": url, "used_profile": self._profile(url), "profiles": profiles}

    @staticmethod
    def _profile(url: str) -> str | None:
        return source_common.PREFERRED.get(urlsplit(url).hostname or "")

    async def async_close(self) -> None:
        await self.shop_session.close()

    def offers_view(self) -> dict[str, Any]:
        today = self.today()
        return {
            "offers": sorted(self.book.current(today), key=lambda offer: (offer["chain"], offer["name"])),
            "sources": self.book.status(),
            "usage": self.book.usage,
            "refreshing": self.refreshing,
            "last_refresh": self.last_refresh,
            "chains": {chain: {"web": chain in self.web_chains, "brochures": chain in self.brochure_chains, "zone": self.zone(chain)} for chain in CHAINS},
            "today": today.isoformat(),
        }

    # --- Settings -------------------------------------------------------------
    async def async_set_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        clean: dict[str, Any] = {}
        if "rules" in settings:
            clean["rules"] = [rules_mod.clean_rule(rule) for rule in settings["rules"]]
            ids = [rule["id"] for rule in clean["rules"]]
            if len(set(ids)) != len(ids):
                raise PlannerError("Правилата трябва да са с различни имена.", "invalid")
        if "slots" in settings:
            clean["slots"] = {
                str(day): [meal for meal in settings["slots"].get(str(day), []) if meal in MEAL_TYPES]
                for day in range(7)
            }
        if "recent_weeks" in settings:
            clean["recent_weeks"] = max(0, min(8, int(settings["recent_weeks"])))
        self.settings = {**self.settings, **clean}
        await self._settings_store.async_save(self.settings)
        return self.settings

    async def async_organizers(self) -> dict[str, Any]:
        tags, categories, foods = await asyncio.gather(self.mealie.tags(), self.mealie.categories(), self.mealie.foods())
        return {
            "tags": sorted({tag.get("name") for tag in tags if tag.get("name")}),
            "categories": sorted({category.get("name") for category in categories if category.get("name")}),
            "foods": sorted({food.get("name") for food in foods if food.get("name")}),
        }

    # --- Weeks and drafts -----------------------------------------------------
    def week_start(self, offset: int = 1) -> date:
        """The first day of this week (offset 0), next week (1), and so on."""
        first = int(self.options.get(OPT_WEEK_START, DEFAULT_WEEK_START))
        today = self.today()
        this_week = today - timedelta(days=(today.weekday() - first) % 7)
        return this_week + timedelta(weeks=offset)

    def slots_for(self, start: date) -> list[str]:
        slots = []
        for day in range(7):
            when = start + timedelta(days=day)
            for meal in self.settings["slots"].get(str(when.weekday()), []):
                slots.append(f"{when.isoformat()}|{meal}")
        return slots

    def _draft(self, start: date) -> dict[str, Any]:
        return self.drafts.setdefault(start.isoformat(), {"slots": {}, "overrides": {}, "checked": [], "reasons": {}, "notice": None})

    async def _save_drafts(self) -> None:
        oldest = (self.week_start(0) - timedelta(weeks=1)).isoformat()
        self.drafts = {week: draft for week, draft in self.drafts.items() if week >= oldest}
        await self._drafts_store.async_save({"weeks": self.drafts})

    async def _ensure_recipes(self, force: bool = False) -> None:
        async with self._recipes_lock:
            now = dt_util.utcnow()
            if not force and self.recipes.recipes and self._recipes_read and now - self._recipes_read < _RECIPES_FRESH:
                return
            await self.recipes.refresh(self.mealie)
            self._recipes_read = now
            await self._recipes_store.async_save(self.recipes.as_dict())

    async def _load_saved(self, start: date, draft: dict[str, Any]) -> None:
        """Bring in what Mealie already has planned that week."""
        end = start + timedelta(days=6)
        entries = await self.mealie.mealplans(start.isoformat(), end.isoformat())
        seen: set[str] = set()
        for entry in entries:
            recipe_id = entry.get("recipeId") or (entry.get("recipe") or {}).get("id")
            if not recipe_id or not entry.get("date"):
                continue
            key = f"{entry['date']}|{entry.get('entryType') or 'dinner'}"
            if key in seen:
                continue  # A second entry in the same slot is left to Mealie.
            seen.add(key)
            slot = draft["slots"].setdefault(key, {"recipe": None, "locked": False})
            unchanged = slot.get("recipe") in (None, slot.get("saved_recipe"))
            slot["mealie_id"] = entry.get("id")
            slot["saved_recipe"] = recipe_id
            if unchanged:
                slot["recipe"] = recipe_id
        # Entries deleted in Mealie are no longer saved.
        for key, slot in draft["slots"].items():
            if key not in seen and slot.get("mealie_id"):
                if slot.get("recipe") == slot.get("saved_recipe"):
                    slot["recipe"] = None
                slot["mealie_id"] = None
                slot["saved_recipe"] = None

    def _week_offers(self, start: date) -> OfferIndex:
        return OfferIndex(self.book.in_period(start, start + timedelta(days=6)))

    def _candidates(self, index: OfferIndex) -> list[planner.Candidate]:
        rules = self.settings["rules"]
        found = []
        for recipe in self.recipes.recipes.values():
            score, sale = shopping.sale_score(recipe, index)
            found.append(planner.Candidate(recipe["id"], recipe.get("name") or "", rules_mod.flags(recipe, rules), score, sale))
        return found

    async def _recent(self, start: date) -> set[str]:
        weeks = int(self.settings.get("recent_weeks", 2))
        if weeks <= 0:
            return set()
        entries = await self.mealie.mealplans((start - timedelta(weeks=weeks)).isoformat(), (start - timedelta(days=1)).isoformat())
        return {entry.get("recipeId") for entry in entries if entry.get("recipeId")}

    async def async_week(self, start: date) -> dict[str, Any]:
        await self._ensure_recipes()
        draft = self._draft(start)
        await self._load_saved(start, draft)
        await self._save_drafts()
        return await self.async_view(start)

    async def async_generate(self, start: date, *, mode: str | None = None, seed: int | None = None, replace_saved: bool = False) -> dict[str, Any]:
        await self._ensure_recipes(force=True)
        draft = self._draft(start)
        await self._load_saved(start, draft)
        slots = self.slots_for(start)
        for key in slots:
            draft["slots"].setdefault(key, {"recipe": None, "locked": False})
        rules = self.settings["rules"]
        index = self._week_offers(start)
        candidates = self._candidates(index)
        if not candidates:
            raise PlannerError("В Mealie няма рецепти.", "no_recipes")
        recent = await self._recent(start)
        seed = seed if seed is not None else randrange(1 << 30)

        # What stays: slots the user locked, and what is already saved in Mealie.
        keep = {
            key for key in slots
            if draft["slots"][key].get("recipe") and (
                draft["slots"][key].get("locked") or (not replace_saved and draft["slots"][key].get("saved_recipe"))
            )
        }
        fixed = {key: draft["slots"][key]["recipe"] for key in keep}
        mode = mode if mode in (MODE_AI, MODE_LOCAL) else self.mode
        if self.ai is None:
            mode = MODE_LOCAL
        notice = None
        reasons: dict[str, str] = {}
        if mode == MODE_AI and self.ai is not None:
            try:
                chosen, reasons = await self._ai_choose(slots, candidates, rules, fixed, recent)
                fixed_ai = {**fixed, **chosen}
                assigned = planner.plan_week(slots, candidates, rules, fixed=fixed_ai, recent=recent, seed=seed)
                assigned = planner.repair(slots, assigned, candidates, rules, keep=keep, recent=recent, seed=seed)
            except PlannerError as exc:
                _LOGGER.warning("AI planning failed, planning locally: %s", exc)
                notice = "ai_failed"
                mode = MODE_LOCAL
        if mode != MODE_AI or notice:
            assigned = planner.plan_week(slots, candidates, rules, fixed=fixed, recent=recent, seed=seed)
        for key in slots:
            if key in keep:
                continue
            draft["slots"][key]["recipe"] = assigned.get(key)
        draft["reasons"] = {key: value for key, value in reasons.items() if assigned.get(key)}
        draft["notice"] = notice
        draft["mode"] = mode
        draft["generated_at"] = dt_util.utcnow().isoformat()
        await self._save_drafts()
        return await self.async_view(start)

    async def _ai_choose(self, slots, candidates, rules, fixed, recent) -> tuple[dict[str, str], dict[str, str]]:
        # Only the most useful candidates go to the AI: rule matches first, then sale.
        pool = sorted(
            (candidate for candidate in candidates if candidate.id not in recent or candidate.id in fixed.values()),
            key=lambda candidate: (-len(candidate.flags), -candidate.score),
        )[:_AI_CANDIDATES]
        prompt, short = planner.ai_prompt(slots, pool, rules, fixed)
        answer, tokens = await self.ai.chat_json(planner.AI_SYSTEM, prompt, schema=planner.AI_SCHEMA, name="plan", max_tokens=8000)
        self.book.add_usage(tokens)
        await self._offers_store.async_save(self.book.as_dict())
        return planner.read_ai_plan(answer, short, slots, fixed)

    async def async_update_slot(
        self, start: date, slot: str, *, set_recipe: bool, recipe_id: str | None, locked: bool | None
    ) -> dict[str, Any]:
        """Change, clear or lock one slot; the products follow on the next view."""
        draft = self._draft(start)
        entry = draft["slots"].setdefault(slot, {"recipe": None, "locked": False})
        if set_recipe:
            if recipe_id and self.recipes.by_id(recipe_id) is None:
                raise PlannerError("Няма такава рецепта.", "not_found")
            entry["recipe"] = recipe_id
            draft.get("reasons", {}).pop(slot, None)
        if locked is not None:
            entry["locked"] = bool(locked)
        await self._save_drafts()
        return await self.async_view(start)

    async def async_move_slot(self, start: date, source: str, target: str) -> dict[str, Any]:
        """Swap two slots' recipes; saved entries stay where they are until saving."""
        draft = self._draft(start)
        one = draft["slots"].setdefault(source, {"recipe": None, "locked": False})
        other = draft["slots"].setdefault(target, {"recipe": None, "locked": False})
        one["recipe"], other["recipe"] = other.get("recipe"), one.get("recipe")
        reasons = draft.setdefault("reasons", {})
        reasons[source], reasons[target] = reasons.get(target), reasons.get(source)
        draft["reasons"] = {key: value for key, value in reasons.items() if value}
        await self._save_drafts()
        return await self.async_view(start)

    async def async_save(self, start: date) -> dict[str, Any]:
        """Write the slots that changed to Mealie's meal planner."""
        draft = self._draft(start)
        written = removed = 0
        for key, slot in sorted(draft["slots"].items()):
            if slot.get("recipe") == slot.get("saved_recipe"):
                continue
            day, _, meal = key.partition("|")
            if slot.get("mealie_id"):
                await self.mealie.delete_mealplan(slot["mealie_id"])
                slot["mealie_id"] = None
                slot["saved_recipe"] = None
                removed += 1
            if slot.get("recipe"):
                created = await self.mealie.add_mealplan(day, meal, slot["recipe"])
                slot["mealie_id"] = (created or {}).get("id")
                slot["saved_recipe"] = slot["recipe"]
                written += 1
        await self._save_drafts()
        view = await self.async_view(start)
        view["saved"] = {"written": written, "removed": removed}
        return view

    async def async_view(self, start: date) -> dict[str, Any]:
        draft = self._draft(start)
        rules = self.settings["rules"]
        index = self._week_offers(start)
        keys = sorted(set(self.slots_for(start)) | {key for key, slot in draft["slots"].items() if slot.get("recipe") or slot.get("mealie_id")})
        slots = []
        planned_flags = []
        for key in keys:
            slot = draft["slots"].get(key, {})
            recipe = self.recipes.by_id(slot.get("recipe"))
            info = None
            if recipe:
                recipe_flags = rules_mod.flags(recipe, rules)
                planned_flags.append(recipe_flags)
                score, sale = shopping.sale_score(recipe, index)
                info = {"id": recipe["id"], "slug": recipe.get("slug"), "name": recipe.get("name"), "image": recipe.get("image"), "flags": recipe_flags, "sale": sale, "score": score}
            elif slot.get("recipe"):
                info = {"id": slot["recipe"], "name": "?", "flags": [], "sale": [], "score": 0}
            day, _, meal = key.partition("|")
            slots.append({
                "key": key,
                "date": day,
                "meal": meal,
                "recipe": info,
                "locked": bool(slot.get("locked")),
                "saved": slot.get("saved_recipe") is not None and slot.get("recipe") == slot.get("saved_recipe"),
                "changed": slot.get("recipe") != slot.get("saved_recipe"),
                "reason": (draft.get("reasons") or {}).get(key),
            })
        items = self._basket(start, draft, index)
        return {
            "week": start.isoformat(),
            "end": (start + timedelta(days=6)).isoformat(),
            "slots": slots,
            "rules": rules_mod.check(planned_flags, rules),
            "basket": items,
            "notice": draft.get("notice"),
            "mode": draft.get("mode"),
            "mealie_url": self.mealie.url,
            "group": await self.mealie.group(),
            "lists": self.lists_info(),
            "zones": {chain: self.zone(chain) for chain in CHAINS},
        }

    # --- The week's products --------------------------------------------------
    def _basket(self, start: date, draft: dict[str, Any], index: OfferIndex) -> list[dict[str, Any]]:
        recipes = [self.recipes.by_id(slot.get("recipe")) for slot in draft["slots"].values()]
        recipes = [recipe for recipe in recipes if recipe]
        items = shopping.basket(recipes, index, draft.get("overrides"), set(draft.get("checked") or []))
        list_items = self._list_items()
        zones = {item["store"] for item in list_items if item.get("store")}
        shopping.apply_home_shops(
            items,
            list_items,
            {chain: self.zone(chain) for chain in CHAINS},
            {zone: self._zone_name(zone) for zone in zones},
            draft.get("overrides"),
        )
        shopping.prune(draft, items)
        return items

    def _list_items(self) -> list[dict[str, Any]]:
        """Every item on every HomeBasket Lists list, bought ones included."""
        api = self._lists_api()
        if api is None:
            return []
        return [item for board in api.lists for item in board.get("items") or []]

    def _zone_name(self, zone: str) -> str:
        states = getattr(self.hass, "states", None)
        state = states.get(zone) if states is not None else None
        if state is not None and state.attributes.get("friendly_name"):
            return str(state.attributes["friendly_name"])
        return zone.split(".", 1)[-1].replace("_", " ").title()

    async def async_alternatives(self, start: date, key: str) -> list[dict[str, Any]]:
        draft = self._draft(start)
        index = self._week_offers(start)
        item = next((item for item in self._basket(start, draft, index) if item["key"] == key), None)
        if item is None:
            raise PlannerError("Продуктът вече не е нужен за седмицата.", "not_found")
        return shopping.alternatives(item, index)

    async def async_choose(self, start: date, key: str, offer_id: str | None) -> dict[str, Any]:
        draft = self._draft(start)
        overrides = draft.setdefault("overrides", {})
        if offer_id is None:
            overrides.pop(key, None)
        else:
            overrides[key] = offer_id
        await self._save_drafts()
        return await self.async_view(start)

    async def async_check(self, start: date, keys: list[str], checked: bool) -> dict[str, Any]:
        draft = self._draft(start)
        current = set(draft.get("checked") or [])
        current = current | set(keys) if checked else current - set(keys)
        draft["checked"] = sorted(current)
        await self._save_drafts()
        return await self.async_view(start)

    # --- HomeBasket Lists -----------------------------------------------------
    def _lists_api(self):
        api = self.hass.data.get(LISTS_API)
        if api is None or getattr(api, "api_version", 0) < 1 or not hasattr(api, "async_add_item"):
            return None
        return api

    def lists_info(self) -> dict[str, Any]:
        api = self._lists_api()
        if api is None:
            return {"available": False, "lists": []}
        lists = [{"entry_id": item["entry_id"], "name": item["name"]} for item in api.lists]
        chosen = self.options.get(OPT_LIST_ENTRY)
        if chosen not in {item["entry_id"] for item in lists}:
            chosen = lists[0]["entry_id"] if len(lists) == 1 else None
        return {"available": bool(lists), "lists": lists, "entry_id": chosen}

    async def async_add_to_list(self, items: list[dict[str, Any]], entry_id: str | None = None) -> dict[str, Any]:
        """Put products on the HomeBasket Lists list, each with its shop, or none."""
        api = self._lists_api()
        if api is None:
            raise PlannerError("HomeBasket Lists не е инсталиран.", "no_lists")
        entry_id = entry_id or self.lists_info().get("entry_id")
        added = 0
        for item in items:
            offer = item.get("offer")
            chain = offer.get("chain") if offer else None
            # On offer: that shop. Otherwise the shop the lists keep it under.
            zone = self.zone(chain) if offer else item.get("home_zone")
            # "No shop" picked by hand, or an offer from a shop with no zone
            # (the note names it): nothing else should fill the shop in.
            no_shop = (item.get("picked") and not offer) or (offer and not zone)
            fields: dict[str, Any] = {"type": "food"}
            if item.get("quantity"):
                fields["quantity"] = float(item["quantity"])
            if item.get("unit"):
                fields["unit"] = str(item["unit"])
            if zone:
                fields["store"] = zone
            note = _note(offer) if offer else None
            if offer and not zone:
                note = f"{note} (няма зона за {CHAIN_NAMES.get(chain, chain)})"
            if item.get("recipes"):
                recipes = ", ".join(item["recipes"][:3])
                note = f"{note} · {recipes}" if note else recipes
            if note:
                fields["note"] = note
            result = await api.async_add_item(item["name"], entry_id=entry_id, **fields)
            if result is None:
                raise PlannerError("Изберете списък в настройките на Mealie Planner.", "no_list")
            added += 1
            # Without a shop, HomeBasket Lists picks one from what HomeBasket
            # knows of the product, which is kept unless said otherwise above.
            if no_shop and result.get("outcome") == "added":
                await self._clear_guessed_store(result)
        return {"added": added}

    async def _clear_guessed_store(self, result: dict[str, Any]) -> None:
        """HomeBasket Lists guesses a shop for items without one; "no shop" means none."""
        item = result.get("item") or {}
        if not item.get("store"):
            return
        runtime = self.hass.data.get("homebasket_lists", {}).get(result.get("entry_id"))
        update = getattr(runtime, "async_update_item", None)
        if update is None:
            return
        try:
            await update(item["uid"], store=None)
        except Exception:  # noqa: BLE001 - a guessed shop is not worth failing over
            _LOGGER.debug("Could not clear the guessed shop", exc_info=True)

    async def async_add_offer(self, offer_id: str, entry_id: str | None = None) -> dict[str, Any]:
        offer = self.book.offers.get(offer_id)
        if offer is None:
            raise PlannerError("Промоцията вече я няма.", "not_found")
        return await self.async_add_to_list([{"name": offer.get("food") or offer["name"], "offer": offer}], entry_id)

    def picker(self, start: date, slot: str, query: str | None) -> list[dict[str, Any]]:
        """Recipes for one slot: what the rules still need first, then what is on sale."""
        rules = self.settings["rules"]
        index = self._week_offers(start)
        draft = self._draft(start)
        planned = [self.recipes.by_id(entry.get("recipe")) for key, entry in draft["slots"].items() if key != slot]
        report = rules_mod.check([rules_mod.flags(recipe, rules) for recipe in planned if recipe], rules)
        needed = {line["id"] for line in report if line["state"] in ("missing", "short")}
        recipes = self.recipes.search(query, limit=60) if query else list(self.recipes.recipes.values())
        ranked = []
        for recipe in recipes:
            recipe_flags = rules_mod.flags(recipe, rules)
            score, sale = shopping.sale_score(recipe, index)
            ranked.append({
                "id": recipe["id"], "name": recipe.get("name"), "slug": recipe.get("slug"),
                "image": recipe.get("image"), "flags": recipe_flags, "sale": sale, "score": score,
                "needed": len(needed & set(recipe_flags)),
            })
        if not query:
            ranked.sort(key=lambda item: (-item["needed"], -item["score"], item["name"] or ""))
        return ranked[:60]


def _shop_session(hass: HomeAssistant):
    """A session for the shops' sites, which send headers too long for the shared one."""
    try:
        return async_create_clientsession(
            hass, auto_cleanup=False, max_line_size=MAX_HEADER, max_field_size=MAX_HEADER
        )
    except TypeError:  # an aiohttp without these settings
        return async_create_clientsession(hass, auto_cleanup=False)


def _effort(value: str | None) -> str | None:
    """The reasoning effort to send, or None to send none."""
    return None if value in (None, "", "default") else value


def _note(offer: dict[str, Any]) -> str:
    price = f"{offer['price']:.2f}".replace(".", ",")
    text = f"{CHAIN_NAMES.get(offer['chain'], offer['chain'])} · {price} €"
    if offer.get("discount_pct"):
        text += f" (−{offer['discount_pct']}%)"
    if offer.get("valid_to"):
        day = date.fromisoformat(offer["valid_to"])
        text += f" до {day.day:02d}.{day.month:02d}"
    return text
