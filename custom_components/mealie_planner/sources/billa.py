"""Billa's offers, from ssbbilla.site, Billa's plain-HTML offers site.

The front page links to one page per category; each lists its products in
`.productSection > .product`, with the dates of the offers in `.dateSpan`.
"""

from __future__ import annotations

from datetime import date
import logging
import re
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientSession

from ..const import BILLA
from ..text import parse_dates, parse_price
from .common import SourceError, fetch_text, make_offer
from .html import parse

_LOGGER = logging.getLogger(__name__)

BASE = "https://ssbbilla.site"
SOURCE_ID = f"{BILLA}:web"

# Marketing phrases that are part of the name on the site but not of the product.
_NOISE = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"Най.*добра.*цена.*",
        r"Изпечен.*всеки.*минути",
        r"Виж още.*",
        r"(Продукт)?(,|\s)+означен.*със символа.*звезда",
        r"(Продукт)?(,|\s)+маркиран.*с.*звезда",
        r"(\*\s*)?(\*+)?цената не включва \w+алаж\s*(\.)?",
        r"(\*\s*)?(\*+)?цената е без \w+алаж\s*(\.)?",
        r"(\*\s*)?(\*+)?цена без \w+алаж\s*(\.)?",
        r"([;-]\s*)?цена на \w+алаж\s?(-)? .*$",
        r"Произход\s*-\s*България",
        r"Сега в Billa",
        r"Евтино в Billa",
        r"до\s+\d+\s+бр.+\w+ент(и)?",
        r"\*+",
        r"Специфика\s*:.*$",
        r"Супер цена",
        r"МУЛТИ ПАК (\d+\+\d+)?",
        r"(\d+(х|x)\s*)?Цена\s+за\s+\d+\s*бр\.\s*((без|с)\s+отстъпка)?\s*(\d|\.|,)+\s*(лв|€|евро)\.?",
    )
]
# Offers only for Billa Card or app holders are left out: not everyone has one.
_CARD_ONLY = re.compile(r"с (Billa|билла|била) (card|app|арр)", re.IGNORECASE)
_QUANTITY = re.compile(
    r"((?:\d+\s*[xх×]\s*)?\d+(?:[.,]\d+)?\s*(?:кг|гр|г|мл|л|бр)\.?(?:\s*(?:опаковка|пакет))?|за\s+(?:1\s+)?кг\.?|1\s*кг\.?)",
    re.IGNORECASE,
)


def parse_category_links(html: str) -> list[str]:
    root = parse(html)
    links = []
    for button in root.select(".buttons div.button"):
        label = (button.select_one("div.buttonText") or button).text()
        if re.search("billa", label, re.IGNORECASE) or re.search("филиал", label, re.IGNORECASE):
            continue
        anchor = button.select_one("a")
        if anchor is not None and anchor.get("href"):
            links.append(urljoin(BASE + "/", anchor.get("href")))
    return list(dict.fromkeys(links))


def clean_name(name: str) -> tuple[str, str | None]:
    """The name without marketing phrases, and the pack size taken out of it."""
    for pattern in _NOISE:
        name = pattern.sub("", name)
    quantity = None
    if match := _QUANTITY.search(name):
        quantity = match.group(0).strip()
        name = (name[: match.start()] + " " + name[match.end():])
    return " ".join(name.split()).strip(" ,.-!:;"), quantity


def _prices(values: list[float]) -> tuple[float | None, float | None]:
    """(price, old price) from the numbers on a product.

    The site has shown old and new prices in lev and in euro, in the order old
    lev, old euro, new lev, new euro; after the switch to the euro only the
    euro pair. Four numbers: the euro pair; two: old then new; one: the price.
    """
    if len(values) >= 4:
        old, new = values[1], values[3]
    elif len(values) == 3:
        old, new = values[0], values[2]
    elif len(values) == 2:
        old, new = values
    elif values:
        return values[0], None
    else:
        return None, None
    if old is not None and new is not None and old < new:
        old, new = new, old
    return new, old


_RANGE = re.compile(
    r"(\d{1,2}\.\d{1,2}\.(?:\d{2,4})?)\s*(?:г\.)?\s*(?:-|–|—|до)\s*(\d{1,2}\.\d{1,2}\.(?:\d{2,4})?)"
)


def page_dates(text: str, today: date) -> list[date]:
    """The first "01.10 – 07.10.2026" style range in a page's text."""
    for match in _RANGE.finditer(text):
        dates = parse_dates(f"{match.group(1)} {match.group(2)}", today)
        if len(dates) == 2 and 0 <= (dates[1] - dates[0]).days <= 31:
            return dates
    return []


def parse_offers(html: str, today: date, *, url: str = BASE) -> list[dict[str, Any]]:
    root = parse(html)
    span = root.select_one(".dateSpan")
    dates = parse_dates(span.text(), today) if span else []
    if len(dates) < 2:
        # The date element has moved: take the first date range the page shows.
        dates = page_dates(root.text(), today)
    category = root.select_one("title")
    offers = []
    for product in root.select(".productSection > .product"):
        name_node = product.select_one(".actualProduct")
        if name_node is None:
            continue
        name = name_node.text()
        if not name or _CARD_ONLY.search(name):
            continue
        values = [parse_price(node.text()) for node in product.select(".price")]
        values = [value for value in values if value is not None]
        price, old = _prices(values)
        name, quantity = clean_name(name)
        offer = make_offer(
            BILLA,
            source_id=SOURCE_ID,
            name=name,
            price=price,
            old_price=old,
            quantity=quantity,
            valid_from=dates[0] if dates else None,
            valid_to=dates[1] if len(dates) > 1 else None,
            url=url,
            source_category=category.text() if category else None,
        )
        if offer is not None:
            offers.append(offer)
    return offers


async def fetch(session: ClientSession, today: date) -> list[dict[str, Any]]:
    links = parse_category_links(await fetch_text(session, BASE))
    if not links:
        raise SourceError("Billa: no category pages on ssbbilla.site")
    offers: dict[str, dict[str, Any]] = {}
    for link in links:
        try:
            for offer in parse_offers(await fetch_text(session, link), today, url=link):
                offers.setdefault(offer["id"], offer)
        except SourceError as exc:
            _LOGGER.debug("Billa page skipped: %s", exc)
    return list(offers.values())
