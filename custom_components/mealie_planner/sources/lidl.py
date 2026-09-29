"""Lidl's offers, from the offer pages linked on lidl.bg's front page.

The front page's hero links lead to offer pages ("НИСКА цена, ВИСОКО
качество", Lidl Plus…); their product tiles lead to product pages, which carry
the name, the prices, the pack size and that product's own dates.
"""

from __future__ import annotations

import asyncio
from datetime import date
import logging
import re
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientSession

from ..const import LIDL
from ..text import date_ranges, first_range, parse_dates
from .common import SourceError, fetch_text, make_offer
from .html import parse

_LOGGER = logging.getLogger(__name__)

BASE = "https://www.lidl.bg"
SOURCE_ID = f"{LIDL}:web"
# The front page links to much more than offers; these are the offer pages.
_ACCEPT = ("niska-tsena-visoko-kachestvo", "lidl-plus", "promo", "oferti", "aktualni")
_PARALLEL = 4
_MAX_PRODUCTS = 400


def parse_offer_pages(html: str, today: date) -> dict[str, list[date]]:
    """Offer pages linked from the front page, each with the dates its link shows.

    An offer page is a category link ("/c/") with a known offer word in it, or
    with a date range in its text ("28.09. - 04.10."), as the weekly ones have.
    """
    root = parse(html)
    pages: dict[str, list[date]] = {}
    for selector in ("li.AHeroStageItems__Item > a", "a"):
        for anchor in root.select(selector):
            href = anchor.get("href")
            if not href or "/c/" not in href:
                continue
            dates = first_range(anchor.text(), today)
            if dates or any(word in href for word in _ACCEPT):
                url = urljoin(BASE, href.split("#")[0])
                if url not in pages or (dates and not pages[url]):
                    pages[url] = dates
        if pages:
            break
    if not any(pages.values()):
        # The front page is built from data in its scripts: find the weekly
        # offer pages there, as the category link nearest each date range.
        for position, dates in date_ranges(html, today):
            start = max(0, position - 400)
            window = html[start: position + 400]
            here = position - start
            links = [(abs(match.start() - here), match.group(1)) for match in _CATEGORY_LINK.finditer(window)]
            if links:
                url = urljoin(BASE, min(links)[1])
                pages[url] = pages.get(url) or dates
    return pages


_CATEGORY_LINK = re.compile(r"(?:https?:)?(?://www\.lidl\.bg)?(/c/[a-z0-9\-]+/[as]\d+)")


def parse_offer_links(html: str, today: date | None = None) -> list[str]:
    return list(parse_offer_pages(html, today or date.today()))


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


def page_dates(html: str, today: date) -> list[date]:
    """The week an offer page is for, from the range it shows, in its text or its data."""
    return first_range(html, today)


def with_dates(offer: dict[str, Any], dates: list[date]) -> dict[str, Any]:
    """An offer without dates of its own takes its page's."""
    if offer.get("valid_from") or offer.get("valid_to") or len(dates) < 2:
        return offer
    return {**offer, "valid_from": dates[0].isoformat(), "valid_to": dates[1].isoformat()}


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
    """All offers; product pages already known (by URL) are not fetched again.

    Product pages no longer say when an offer runs. A product takes the dates
    of the offer page it is on, else of that page's link on the front page,
    else the first range the front page shows.
    """
    known = known or {}
    front = await fetch_text(session, BASE, expect=lambda html: bool(parse_offer_pages(html, today)))
    pages = parse_offer_pages(front, today)
    if not pages:
        raise SourceError("Lidl: no offer pages linked from the front page")
    front_dates = first_range(front, today)
    products: dict[str, tuple[str | None, str, list[date]]] = {}
    for page, link_dates in pages.items():
        try:
            html = await fetch_text(session, page, expect=lambda html: "PRODUCT" in html)
        except SourceError as exc:
            _LOGGER.debug("Lidl page skipped: %s", exc)
            continue
        title, tiles = parse_product_tiles(html)
        dates = page_dates(html, today) or link_dates or front_dates
        for url, image in tiles:
            products.setdefault(url, (image, title, dates))
    chosen = list(products.items())[:_MAX_PRODUCTS]

    semaphore = asyncio.Semaphore(_PARALLEL)
    results: list[dict[str, Any]] = []

    async def one(url: str, image: str | None, title: str, dates: list[date]) -> None:
        if url in known:
            results.append(with_dates(known[url], dates))
            return
        async with semaphore:
            try:
                html = await fetch_text(session, url, expect=lambda html: "heading__title" in html)
                offer = parse_product(html, today, url=url, image=image, category=title)
            except SourceError as exc:
                _LOGGER.debug("Lidl product skipped: %s", exc)
                return
        if offer is not None:
            results.append(with_dates(offer, dates))

    await asyncio.gather(*(one(url, *details) for url, details in chosen))
    return results
