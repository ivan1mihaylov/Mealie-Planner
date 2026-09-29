"""Reading brochures with AI, once per brochure, and naming what the table could not."""

from __future__ import annotations

import logging
import re
from typing import Any

from aiohttp import ClientSession

from .ai import AIClient, image_part, pdf_part
from .classify import classify
from .const import CATEGORIES, CHAIN_NAMES
from .mealie import PlannerError
from .sources.common import SourceError, fetch_bytes, make_offer
from .text import iso

_LOGGER = logging.getLogger(__name__)

_IMAGES_PER_CALL = 4
_PDF_PAGES_PER_CALL = 12
_NAMES_PER_CALL = 80

OFFER_SCHEMA = {
    "type": "object",
    "properties": {
        "offers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "brand": {"type": ["string", "null"]},
                    "food": {"type": ["string", "null"]},
                    "category": {"type": "string", "enum": list(CATEGORIES)},
                    "price": {"type": "number"},
                    "old_price": {"type": ["number", "null"]},
                    "quantity": {"type": ["string", "null"]},
                    "valid_from": {"type": ["string", "null"]},
                    "valid_to": {"type": ["string", "null"]},
                    "conditions": {"type": ["string", "null"]},
                    "page": {"type": ["integer", "null"]},
                },
                "required": ["name", "category", "price"],
            },
        }
    },
    "required": ["offers"],
}

SYSTEM = f"""You read Bulgarian supermarket brochures and list every product offer on the pages you are given.
For each offer return:
- name: the product name as printed, in Bulgarian, without the price or marketing words.
- brand: the brand, or null.
- food: a short generic Bulgarian noun for what the product is, as a cook would write it in a recipe ("сьомга", "картофи", "кайма", "кисело мляко", "боб"), or null for things that are not food.
- category: one of {", ".join(CATEGORIES)}.
- price: the promotional price in euro (€) as a number. If only a lev price is printed, convert it at 1.95583 lev per euro.
- old_price: the regular price in euro, or null.
- quantity: the pack size as printed ("500 г", "1 кг", "4 x 125 г"), or null.
- valid_from / valid_to: the dates THIS offer is valid, as YYYY-MM-DD. Offers on the same page can have different dates ("само в събота", "от четвъртък"); use the brochure's dates only when the offer has none of its own.
- conditions: limits such as "с Lidl Plus", "при покупка на 2 бр.", or null.
- page: the page number.
Leave out anything that is not an offer. Return JSON only."""


def _to_offers(raw: Any, chain: str, brochure: dict[str, Any], default_page: int | None) -> list[dict[str, Any]]:
    items = raw.get("offers") if isinstance(raw, dict) else raw
    offers = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        category = item.get("category") if item.get("category") in CATEGORIES else None
        food = (item.get("food") or "").strip().lower() or None
        if category is None or food is None:
            guessed_food, guessed_category = classify(f"{item.get('brand') or ''} {item.get('name') or ''}")
            food = food or guessed_food
            category = category or guessed_category
        if category == "non_food":
            continue
        offer = make_offer(
            chain,
            source_id=brochure["id"],
            name=item.get("name") or "",
            brand=item.get("brand"),
            price=item.get("price"),
            old_price=item.get("old_price"),
            quantity=item.get("quantity"),
            valid_from=iso(item.get("valid_from")) or brochure.get("valid_from"),
            valid_to=iso(item.get("valid_to")) or brochure.get("valid_to"),
            page=item.get("page") or default_page,
            food=food,
            category=category or "other_food",
            conditions=item.get("conditions"),
            url=brochure.get("url") or brochure.get("pdf"),
            key_parts=(brochure["id"], item.get("name"), item.get("quantity"), item.get("price"), item.get("page")),
        )
        if offer is not None:
            offers.append(offer)
    return offers


def _intro(chain: str, brochure: dict[str, Any], pages: str) -> str:
    return (
        f"Brochure of {CHAIN_NAMES.get(chain, chain)} “{brochure.get('title') or ''}”, "
        f"valid {brochure.get('valid_from') or '?'} to {brochure.get('valid_to') or '?'}. {pages}"
    )


def pdf_page_count(data: bytes) -> int:
    """Pages in a PDF, counted from its page objects; good enough to split the work."""
    return max(1, len(re.findall(rb"/Type\s*/Page(?!s)", data)))


async def read_brochure(
    ai: AIClient, session: ClientSession, brochure: dict[str, Any], max_pages: int
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """All offers in a brochure, and the tokens spent reading it."""
    chain = brochure["chain"]
    used = {"prompt": 0, "completion": 0}
    offers: list[dict[str, Any]] = []

    def add(tokens: dict[str, int]) -> None:
        used["prompt"] += tokens["prompt"]
        used["completion"] += tokens["completion"]

    pages = brochure.get("pages") or []
    if pages:
        pages = pages[:max_pages]
        for first in range(0, len(pages), _IMAGES_PER_CALL):
            batch = pages[first:first + _IMAGES_PER_CALL]
            content: list[dict[str, Any]] = [
                {"type": "text", "text": _intro(chain, brochure, f"Pages {first + 1}–{first + len(batch)}, in order.")}
            ]
            for url in batch:
                try:
                    data, kind = await fetch_bytes(session, url, limit=8 * 1024 * 1024)
                except SourceError as exc:
                    _LOGGER.debug("Brochure page skipped: %s", exc)
                    continue
                content.append(image_part(data, kind))
            if len(content) == 1:
                continue
            raw, tokens = await ai.chat_json(SYSTEM, content, schema=OFFER_SCHEMA, name="offers", max_tokens=16000)
            add(tokens)
            offers.extend(_to_offers(raw, chain, brochure, first + 1))
        return offers, used

    if brochure.get("pdf"):
        data, _ = await fetch_bytes(session, brochure["pdf"])
        total = min(pdf_page_count(data), max_pages)
        part = pdf_part(data)
        for first in range(1, total + 1, _PDF_PAGES_PER_CALL):
            last = min(total, first + _PDF_PAGES_PER_CALL - 1)
            content = [
                {"type": "text", "text": _intro(chain, brochure, f"Read only pages {first}–{last} of the attached PDF.")},
                part,
            ]
            raw, tokens = await ai.chat_json(SYSTEM, content, schema=OFFER_SCHEMA, name="offers", max_tokens=24000, timeout=300)
            add(tokens)
            offers.extend(_to_offers(raw, chain, brochure, None))
        return offers, used

    raise PlannerError("Брошурата няма страници за четене.", "no_pages")


NAMES_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "i": {"type": "integer"},
                    "food": {"type": ["string", "null"]},
                    "category": {"type": "string", "enum": list(CATEGORIES)},
                },
                "required": ["i", "category"],
            },
        }
    },
    "required": ["items"],
}

NAMES_SYSTEM = f"""You classify Bulgarian supermarket products.
For each numbered product name return:
- food: a short generic Bulgarian noun a cook would write in a recipe ("сьомга", "картофи", "кашкавал"), or null if it is not food;
- category: one of {", ".join(CATEGORIES)}.
Return JSON only."""


async def name_offers(ai: AIClient, offers: list[dict[str, Any]]) -> dict[str, int]:
    """Fill in food and category for offers the keyword table could not place.

    Changes the offers in place. Only names are sent, in large batches, so this
    is cheap; the answers are stored with the offers and never asked again.
    """
    used = {"prompt": 0, "completion": 0}
    todo = [offer for offer in offers if not offer.get("category")]
    for first in range(0, len(todo), _NAMES_PER_CALL):
        batch = todo[first:first + _NAMES_PER_CALL]
        lines = "\n".join(f"{i}. {offer['name']}" for i, offer in enumerate(batch))
        raw, tokens = await ai.chat_json(NAMES_SYSTEM, lines, schema=NAMES_SCHEMA, name="products", max_tokens=12000)
        used["prompt"] += tokens["prompt"]
        used["completion"] += tokens["completion"]
        for item in (raw.get("items") if isinstance(raw, dict) else raw) or []:
            try:
                offer = batch[int(item["i"])]
            except (KeyError, IndexError, TypeError, ValueError):
                continue
            if item.get("category") in CATEGORIES:
                offer["category"] = item["category"]
            if item.get("food"):
                offer["food"] = str(item["food"]).strip().lower()
    # Whatever is still unknown is at least not unknown twice.
    for offer in todo:
        offer["category"] = offer.get("category") or "other_food"
    return used

