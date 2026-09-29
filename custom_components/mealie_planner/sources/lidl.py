"""Lidl's offers, from the offer pages linked on lidl.bg's front page.

The front page's hero links lead to offer pages ("НИСКА цена, ВИСОКО
качество", Lidl Plus…); their product tiles lead to product pages, which carry
the name, the prices, the pack size and that product's own dates.
"""

from __future__ import annotations

import asyncio
from datetime import date
import logging
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientSession

from ..const import LIDL
from ..text import parse_dates
from .common import SourceError, fetch_text, make_offer
from .html import parse

_LOGGER = logging.getLogger(__name__)

BASE = "https://www.lidl.bg"
SOURCE_ID = f"{LIDL}:web"
# The front page links to much more than offers; these are the offer pages.
_ACCEPT = ("niska-tsena-visoko-kachestvo", "lidl-plus", "promo", "oferti", "aktualni")
_PARALLEL = 4
_MAX_PRODUCTS = 400


def parse_offer_links(html: str) -> list[str]:
    root = parse(html)
    links = []
    for anchor in root.select("li.AHeroStageItems__Item > a"):
        href = anchor.get("href")
        if href and any(word in href for word in _ACCEPT):
            links.append(urljoin(BASE, href))
    return list(dict.fromkeys(links))


def parse_product_tiles(html: str) -> tuple[str, list[tuple[str, str | None]]]:
    """The page's title, used as the category, and its products' (URL, image)."""
    root = parse(html)
    title = root.select_one("title")
    tiles = []
    for tile in root.select("div[data-selector=PRODUCT]"):
        url = tile.get("canonicalurl") or tile.get("data-canonicalurl")
        if url:
            tiles.append((urljoin(BASE, url), tile.get("image") or None))
    return (title.text() if title else ""), list(dict.fromkeys(tiles))


def parse_product(html: str, today: date, *, url: str, image: str | None, category: str | None) -> dict[str, Any] | None:
    root = parse(html)
    name = root.select_one("h1.heading__title")
    if name is None:
        return None
    prices = [node.text() for node in root.select("div.ods-price__value")]
    # Two prices mean lev and euro; take the one marked as euro, or the last.
    price = next((text for text in prices if "€" in text or "EUR" in text.upper()), prices[-1] if prices else None)
    olds = [node.text() for node in root.select("div.ods-price__stroke-price")]
    old = next((text for text in olds if "€" in text or "EUR" in text.upper()), olds[-1] if olds else None)
    footers = root.select("div.ods-price__footer")
    quantity = footers[-1].text() if footers else None
    availability = root.select_one("h3.availability")
    dates = parse_dates(availability.text(), today) if availability else []
    return make_offer(
        LIDL,
        source_id=SOURCE_ID,
        name=name.text(),
        price=price,
        old_price=old,
        quantity=quantity,
        valid_from=dates[0] if dates else None,
        valid_to=dates[1] if len(dates) > 1 else None,
        image=image,
        url=url,
        source_category=category,
        key_parts=(url, dates[0] if dates else None),
    )


async def fetch(session: ClientSession, today: date, known: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """All offers; product pages already known (by URL) are not fetched again."""
    known = known or {}
    pages = parse_offer_links(await fetch_text(session, BASE))
    if not pages:
        raise SourceError("Lidl: no offer pages linked from the front page")
    products: list[tuple[str, str | None, str]] = []
    for page in pages:
        try:
            title, tiles = parse_product_tiles(await fetch_text(session, page))
        except SourceError as exc:
            _LOGGER.debug("Lidl page skipped: %s", exc)
            continue
        products.extend((url, image, title) for url, image in tiles)
    products = list({url: (url, image, title) for url, image, title in products}.values())[:_MAX_PRODUCTS]

    semaphore = asyncio.Semaphore(_PARALLEL)
    results: list[dict[str, Any]] = []

    async def one(url: str, image: str | None, title: str) -> None:
        if url in known:
            results.append(known[url])
            return
        async with semaphore:
            try:
                offer = parse_product(await fetch_text(session, url), today, url=url, image=image, category=title)
            except SourceError as exc:
                _LOGGER.debug("Lidl product skipped: %s", exc)
                return
        if offer is not None:
            results.append(offer)

    await asyncio.gather(*(one(*product) for product in products))
    return results
