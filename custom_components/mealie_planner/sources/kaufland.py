"""Kaufland's offers, from the data behind its "актуални предложения" page.

The page carries every offer of every category in one JSON object inside a
<script> that mentions "OfferTemplate"; the category tabs and the "show more"
buttons only reveal what is already there. Each offer has its own dates.
"""

from __future__ import annotations

from datetime import date
import json
import logging
import re
from typing import Any

from aiohttp import ClientSession

from ..const import KAUFLAND
from .common import SourceError, fetch_text, make_offer
from .html import parse

_LOGGER = logging.getLogger(__name__)

URL = "https://www.kaufland.bg/aktualni-predlozheniya/oferti.html"
SOURCE_ID = f"{KAUFLAND}:web"


_PRICE_KEYS = ("formattedPrice", "price", "priceFormatted", "currentPrice")


def _is_offer(item: Any) -> bool:
    return isinstance(item, dict) and bool(item.get("title")) and any(item.get(key) for key in _PRICE_KEYS)


def _embedded_json(root) -> list[Any]:
    """Every JSON value assigned or embedded in the page's scripts."""
    decoder = json.JSONDecoder()
    found = []
    for script in root.select("script"):
        text = script.raw_text()
        if script.get("type") in ("application/json", "application/ld+json"):
            starts = [text.find("{"), text.find("[")]
        else:
            # "window.x = {...}", "x: {...}", "JSON.parse" aside: values after = or (.
            starts = [match.end() - 1 for match in re.finditer(r"[=(]\s*\{", text)]
        for start in sorted(s for s in starts if s >= 0)[:50]:
            try:
                value, _ = decoder.raw_decode(text, start)
            except ValueError:
                continue
            found.append(value)
    return found


def _categories(value: Any, name: str | None = None, into: list | None = None) -> list[dict[str, Any]]:
    """Lists of offers anywhere in a JSON value, each with the nearest category name."""
    into = [] if into is None else into
    if isinstance(value, dict):
        here = value.get("displayName") or value.get("categoryName") or value.get("name") or name
        offers = value.get("offers")
        if isinstance(offers, list) and any(_is_offer(item) for item in offers):
            into.append({"displayName": here if isinstance(here, str) else None, "offers": offers})
        for key, child in value.items():
            if key != "offers":
                _categories(child, here if isinstance(here, str) else name, into)
    elif isinstance(value, list):
        if value and all(_is_offer(item) for item in value[:5]):
            into.append({"displayName": name, "offers": value})
            return into
        for child in value:
            _categories(child, name, into)
    return into


def _offer_data(html: str) -> dict[str, Any] | None:
    root = parse(html)
    data = _template_data(root)
    if data is not None:
        return data
    # The page's data moved: look for lists of offers in any embedded JSON.
    categories: list[dict[str, Any]] = []
    for value in _embedded_json(root):
        _categories(value, None, categories)
    return {"cycles": [{"categories": categories}]} if categories else None


def _template_data(root) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for script in root.select("script"):
        text = script.raw_text()
        if "OfferTemplate" not in text:
            continue
        for match in re.finditer(r'\{"component"', text):
            try:
                data, _ = decoder.raw_decode(text, match.start())
            except ValueError:
                continue
            if isinstance(data, dict) and data.get("props", {}).get("offerData"):
                return data["props"]["offerData"]
    return None


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def parse_offers(html: str, today: date | None = None) -> list[dict[str, Any]]:
    """Every offer on the page; the same offer listed in two categories counts once."""
    data = _offer_data(html)
    if data is None:
        raise SourceError("Kaufland: no offer data on the page")
    offers: dict[str, dict[str, Any]] = {}
    for cycle in data.get("cycles") or []:
        for category in cycle.get("categories") or []:
            category_name = category.get("displayName") or category.get("name")
            for raw in category.get("offers") or []:
                if not _is_offer(raw):
                    continue
                title = raw.get("title") or ""
                subtitle = raw.get("subtitle") or ""
                start = raw.get("dateFrom") or cycle.get("dateFrom")
                end = raw.get("dateTo") or cycle.get("dateTo")
                offer = make_offer(
                    KAUFLAND,
                    source_id=SOURCE_ID,
                    name=f"{title} {subtitle}",
                    brand=None,
                    price=next((raw.get(key) for key in _PRICE_KEYS if raw.get(key)), None),
                    old_price=raw.get("formattedOldPrice") or raw.get("oldPrice"),
                    quantity=raw.get("unit"),
                    valid_from=start,
                    valid_to=end,
                    image=raw.get("listImage"),
                    url=URL,
                    source_category=category_name,
                    conditions=_text(raw.get("loyaltyText")) or _text(raw.get("basePrice")),
                    key_parts=(raw.get("klNr") or raw.get("offerId") or f"{title}|{subtitle}", start, end),
                )
                if offer is not None and offer["id"] not in offers:
                    offers[offer["id"]] = offer
    return list(offers.values())


async def fetch(session: ClientSession, today: date) -> list[dict[str, Any]]:
    return parse_offers(await fetch_text(session, URL), today)
