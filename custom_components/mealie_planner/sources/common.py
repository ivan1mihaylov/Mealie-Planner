"""What every source shares: fetching pages and shaping an offer."""

from __future__ import annotations

import asyncio
import hashlib
import re
from typing import Any, Callable
from urllib.parse import urlsplit

from aiohttp import ClientError, ClientSession

from ..classify import classify
from ..text import discount, iso, normalize, parse_price, unit_price

_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
_LANGUAGE = "bg-BG,bg;q=0.9,en;q=0.6"

# Ways of asking for a page, tried in this order until one gets the whole
# page. Shops with bot protection serve a stripped page to some clients: a
# client that claims to be Chrome but does not connect like Chrome is a
# typical one. The plain client, as the scraper this follows uses, is first.
PROFILES: dict[str, dict[str, str]] = {
    # aiohttp's own identity.
    "plain": {"Accept": _ACCEPT, "Accept-Language": _LANGUAGE},
    # An honest name for this integration.
    "app": {
        "User-Agent": "Mozilla/5.0 (compatible; MealiePlanner/0.1; +https://github.com/ivan1mihaylov/Mealie-Planner)",
        "Accept": _ACCEPT,
        "Accept-Language": _LANGUAGE,
    },
    # A current Chrome, with the headers Chrome sends for a page.
    "browser": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept": _ACCEPT,
        "Accept-Language": _LANGUAGE,
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    },
}

# The profile that last got a site's whole page, by host. Kept by the
# service between runs, so a check starts with what worked.
PREFERRED: dict[str, str] = {}


def _host(url: str) -> str:
    return urlsplit(url).hostname or ""


def _order(url: str) -> list[str]:
    first = PREFERRED.get(_host(url))
    return ([first] if first in PROFILES else []) + [name for name in PROFILES if name != first]


# Shop sites send cookie and security headers longer than aiohttp's default
# 8 KB limit (lidl.bg does); their own session allows more.
MAX_HEADER = 64 * 1024


def _reason(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
    return text[:300]


class SourceError(Exception):
    """A source could not be read; its chain shows the message."""


async def _get(session: ClientSession, url: str, headers: dict[str, str], limit: int, timeout: int) -> str:
    try:
        async with asyncio.timeout(timeout):
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise SourceError(f"{url}: HTTP {response.status}")
                body = await response.content.read(limit + 1)
                if len(body) > limit:
                    raise SourceError(f"{url}: the page is too large")
                return body.decode(response.charset or "utf-8", errors="replace")
    except (TimeoutError, ClientError) as exc:
        raise SourceError(f"{url}: {_reason(exc)}") from exc


async def fetch_text(
    session: ClientSession,
    url: str,
    *,
    expect: Callable[[str], bool] | None = None,
    limit: int = 12 * 1024 * 1024,
    timeout: int = 30,
) -> str:
    """A page's text, asked for the way that gets the whole page.

    `expect` says whether a page is the whole one. Profiles are tried in turn
    until one passes, and the one that did is tried first next time. With
    none passing, the last page is returned for the parser to report on.
    """
    last: str | None = None
    error: SourceError | None = None
    for name in _order(url) if expect else _order(url)[:1]:
        try:
            html = await _get(session, url, PROFILES[name], limit, timeout)
        except SourceError as exc:
            error = exc
            continue
        if expect is None or expect(html):
            PREFERRED[_host(url)] = name
            return html
        last = html
    if last is not None:
        return last
    raise error or SourceError(f"{url}: no answer")


async def fetch_each_profile(session: ClientSession, url: str) -> list[tuple[str, str | None, str | None]]:
    """(profile, page, error) for every profile, to see which gets what."""
    results = []
    for name, headers in PROFILES.items():
        try:
            results.append((name, await _get(session, url, headers, 12 * 1024 * 1024, 30), None))
        except SourceError as exc:
            results.append((name, None, str(exc)))
    return results


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
            async with session.get(url, headers=PROFILES[_order(url)[0]]) as response:
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
