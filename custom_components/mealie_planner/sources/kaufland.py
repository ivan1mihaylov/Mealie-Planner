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


def _offer_data(html: str) -> dict[str, Any] | None:
    root = parse(html)
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
                if not raw.get("title") or not raw.get("formattedPrice"):
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
                    price=raw.get("formattedPrice"),
                    old_price=raw.get("formattedOldPrice"),
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
