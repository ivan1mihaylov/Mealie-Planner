"""What every source shares: fetching pages and shaping an offer."""

from __future__ import annotations

import asyncio
import hashlib
import re
from typing import Any

from aiohttp import ClientError, ClientSession

from ..classify import classify
from ..text import discount, iso, normalize, parse_price, unit_price

# Shops serve a different page, or none, to clients that do not look like a browser.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "bg-BG,bg;q=0.9,en;q=0.6",
}

# Shop sites send cookie and security headers longer than aiohttp's default
# 8 KB limit (lidl.bg does); their own session allows more.
MAX_HEADER = 64 * 1024


def _reason(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
    return text[:300]


class SourceError(Exception):
    """A source could not be read; its chain shows the message."""


async def fetch_text(session: ClientSession, url: str, *, limit: int = 12 * 1024 * 1024, timeout: int = 30) -> str:
    try:
        async with asyncio.timeout(timeout):
            async with session.get(url, headers=HEADERS) as response:
                if response.status != 200:
                    raise SourceError(f"{url}: HTTP {response.status}")
                body = await response.content.read(limit + 1)
                if len(body) > limit:
                    raise SourceError(f"{url}: the page is too large")
                return body.decode(response.charset or "utf-8", errors="replace")
    except (TimeoutError, ClientError) as exc:
        raise SourceError(f"{url}: {_reason(exc)}") from exc


def describe_page(html: str) -> dict[str, Any]:
    """What a fetched page looks like, to tell a changed page from a blocked one."""
    lower = html.lower()
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    ranges = re.findall(r"\d{1,2}\.\d{1,2}\.(?:\d{2,4})?\s*(?:-|–|—|до)\s*\d{1,2}\.\d{1,2}\.(?:\d{2,4})?", html)
    return {
        "length": len(html),
        "date_ranges": ranges[:3],
        "title": " ".join(title.group(1).split())[:120] if title else None,
        "scripts": lower.count("<script"),
        "markers": {
            marker: marker.lower() in lower
            for marker in (
                "OfferTemplate", "window.SSR", "__NEXT_DATA__", "application/ld+json",
                "formattedPrice", "AHeroStageItems", "data-selector=\"PRODUCT\"",
                "ods-price", "productSection", "captcha", "challenge", "Access Denied",
            )
        },
    }


async def fetch_bytes(session: ClientSession, url: str, *, limit: int = 40 * 1024 * 1024, timeout: int = 90) -> tuple[bytes, str]:
    """Bytes and content type of a brochure page image or PDF."""
    try:
        async with asyncio.timeout(timeout):
            async with session.get(url, headers=HEADERS) as response:
                if response.status != 200:
                    raise SourceError(f"{url}: HTTP {response.status}")
                body = await response.content.read(limit + 1)
                if len(body) > limit:
                    raise SourceError(f"{url}: the file is too large")
                return body, response.content_type or ""
    except (TimeoutError, ClientError) as exc:
        raise SourceError(f"{url}: {_reason(exc)}") from exc


def offer_key(chain: str, *parts: Any) -> str:
    text = "|".join(normalize(str(part)) for part in parts if part not in (None, ""))
    return f"{chain}:{hashlib.sha1(text.encode()).hexdigest()[:16]}"


def make_offer(
    chain: str,
    *,
    source_id: str,
    name: str,
    price: Any,
    old_price: Any = None,
    quantity: str | None = None,
    valid_from: Any = None,
    valid_to: Any = None,
    image: str | None = None,
    url: str | None = None,
    source_category: str | None = None,
    brand: str | None = None,
    page: int | None = None,
    food: str | None = None,
    category: str | None = None,
    conditions: str | None = None,
    key_parts: tuple = (),
) -> dict[str, Any] | None:
    """One offer in the shape the cache, the panel and the planner share.

    Returns None for something that is not an offer: no name or no price.
    """
    name = " ".join(str(name or "").split())
    now = parse_price(price)
    if not name or now is None or now <= 0:
        return None
    before = parse_price(old_price)
    if before is not None and before <= now:
        before = None
    quantity = " ".join(str(quantity or "").split()) or None
    per_unit = unit_price(now, quantity or name)
    if food is None and category is None:
        food, category = classify(f"{brand or ''} {name}", source_category)
    start, end = iso(valid_from), iso(valid_to)
    return {
        "id": offer_key(chain, *(key_parts or (name, quantity, start, end))),
        "chain": chain,
        "source_id": source_id,
        "name": name,
        "brand": brand or None,
        "food": food or None,
        "category": category or None,
        "source_category": source_category or None,
        "price": now,
        "old_price": before,
        "discount_pct": discount(now, before),
        "quantity": quantity,
        "unit_price": per_unit[0] if per_unit else None,
        "unit_base": per_unit[1] if per_unit else None,
        "valid_from": start,
        "valid_to": end,
        "image": image or None,
        "url": url or None,
        "page": page,
        "conditions": conditions or None,
    }
