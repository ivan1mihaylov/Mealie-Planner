"""Find the printed brochures a chain publishes, to be read by AI once each.

A brochure page is searched for, in turn:

- Schwarz leaflet viewer links (Lidl and Kaufland both use it). Its flyer
  API gives the page images, often a PDF, and the dates.
- Publitas viewer links, whose data file lists the page images.
- Plain PDF links.

Nothing here spends AI; it only says what there is to read.
"""

from __future__ import annotations

from datetime import date
import hashlib
import json
import logging
import re
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientSession

from ..text import iso, parse_dates
from .common import SourceError, fetch_text
from .html import parse

_LOGGER = logging.getLogger(__name__)

_SCHWARZ_API = "https://endpoints.leaflets.schwarz/v4/flyer"
_SCHWARZ_LINK = re.compile(
    r"(?:/l/[a-z]{2}/[^/\"']+/([^/?#\"']+)(?:/view)?|leaflets\.kaufland\.com/[^/\"']+/([^/?#\"']+)|flyer_identifier=([^&\"']+))",
    re.IGNORECASE,
)
_PUBLITAS_LINK = re.compile(r"https?://view\.publitas\.com/[^\"'\s<>]+", re.IGNORECASE)
_PDF_LINK = re.compile(r"https?://[^\"'\s<>]+?\.pdf(?:\?[^\"'\s<>]*)?", re.IGNORECASE)


def brochure_id(chain: str, key: str) -> str:
    return f"{chain}:brochure:{hashlib.sha1(key.encode()).hexdigest()[:12]}"


def find_links(html: str, base: str) -> dict[str, list[str]]:
    """Leaflet identifiers, Publitas URLs and PDF URLs mentioned on a page."""
    root = parse(html)
    hrefs = [urljoin(base, node.get("href")) for node in root.select("a") if node.get("href")]
    text = "\n".join(hrefs) + "\n" + html
    schwarz = []
    for match in _SCHWARZ_LINK.finditer(text):
        ident = next((group for group in match.groups() if group), None)
        if ident and ident not in ("view", "page") and not ident.isdigit():
            schwarz.append(ident)
    publitas = [url.rstrip("/\\") for url in _PUBLITAS_LINK.findall(text)]
    pdfs = [url.replace("\\/", "/") for url in _PDF_LINK.findall(text)]
    return {
        "schwarz": list(dict.fromkeys(schwarz)),
        "publitas": list(dict.fromkeys(publitas)),
        "pdf": list(dict.fromkeys(pdfs)),
    }


def embedded_pages(html: str, base: str) -> list[str]:
    """Pages shown inside a page: iframes and embeds, where brochure viewers live."""
    root = parse(html)
    urls = []
    for node in root.select("iframe") + root.select("embed") + root.select("object"):
        src = node.get("src") or node.get("data-src") or node.get("data")
        if src and not src.startswith(("about:", "javascript:", "data:")):
            url = urljoin(base, src)
            # Consent, analytics and chat frames never hold a brochure.
            if not re.search(r"google|facebook|youtube|doubleclick|consent|cookie|recaptcha|hotjar|chat", url, re.I):
                urls.append(url)
    return list(dict.fromkeys(urls))


def _walk(data: Any):
    if isinstance(data, dict):
        yield data
        for value in data.values():
            yield from _walk(value)
    elif isinstance(data, list):
        for value in data:
            yield from _walk(value)


def parse_schwarz(chain: str, ident: str, data: dict[str, Any], today: date) -> dict[str, Any] | None:
    """A brochure from the Schwarz flyer API's answer."""
    flyer = data.get("flyer") if isinstance(data.get("flyer"), dict) else data
    pages: list[str] = []
    for page in flyer.get("pages") or []:
        if not isinstance(page, dict):
            continue
        image = page.get("zoom") or page.get("image") or page.get("imageUrl")
        if isinstance(image, dict):
            image = image.get("url")
        if image:
            pages.append(image)
    pdf = flyer.get("pdfUrl") or flyer.get("pdf") or flyer.get("downloadUrl")
    start = flyer.get("offerStartDate") or flyer.get("startDate") or flyer.get("validFrom")
    end = flyer.get("offerEndDate") or flyer.get("endDate") or flyer.get("validTo")
    title = flyer.get("title") or flyer.get("name") or ident
    if not (start and end):
        dates = parse_dates(title, today)
        start = start or (dates[0] if dates else None)
        end = end or (dates[1] if len(dates) > 1 else None)
    if not pages and not pdf:
        return None
    return {
        "id": brochure_id(chain, ident),
        "chain": chain,
        "title": title,
        "valid_from": iso(start),
        "valid_to": iso(end),
        "pages": pages,
        "pdf": pdf,
    }


def parse_publitas(chain: str, url: str, data: Any, today: date) -> dict[str, Any] | None:
    pages: list[str] = []
    for node in _walk(data):
        images = node.get("images")
        if isinstance(images, dict):
            best = images.get("at2400") or images.get("at2000") or images.get("at1600") or images.get("at1200")
            if best:
                pages.append(urljoin(url + "/", best))
    title = data.get("title") if isinstance(data, dict) else None
    pdf = data.get("downloadPdfUrl") if isinstance(data, dict) else None
    dates = parse_dates(f"{title or ''} {url}", today)
    if not pages and not pdf:
        return None
    return {
        "id": brochure_id(chain, url),
        "chain": chain,
        "title": title or url.rsplit("/", 1)[-1],
        "valid_from": iso(dates[0]) if dates else None,
        "valid_to": iso(dates[1]) if len(dates) > 1 else None,
        "pages": list(dict.fromkeys(pages)),
        "pdf": urljoin(url + "/", pdf) if pdf else None,
    }


def pdf_brochure(chain: str, url: str, today: date, title: str | None = None) -> dict[str, Any]:
    dates = parse_dates(f"{title or ''} {url}", today)
    return {
        "id": brochure_id(chain, url),
        "chain": chain,
        "title": title or url.rsplit("/", 1)[-1],
        "valid_from": iso(dates[0]) if dates else None,
        "valid_to": iso(dates[1]) if len(dates) > 1 else None,
        "pages": [],
        "pdf": url,
    }


async def find(session: ClientSession, chain: str, page_url: str, today: date) -> list[dict[str, Any]]:
    """The brochures linked from a chain's brochure page."""
    html = await fetch_text(session, page_url, expect=lambda page: any(find_links(page, page_url).values()))
    links = find_links(html, page_url)
    if not any(links.values()):
        # The brochure may sit in an embedded viewer: look inside its frames.
        for frame in embedded_pages(html, page_url)[:3]:
            try:
                inner = find_links(await fetch_text(session, frame), frame)
            except SourceError as exc:
                _LOGGER.debug("Embedded page %s skipped: %s", frame, exc)
                continue
            for kind, found_links in inner.items():
                links[kind] = list(dict.fromkeys(links[kind] + found_links))
    found: dict[str, dict[str, Any]] = {}
    for ident in links["schwarz"][:6]:
        try:
            text = await fetch_text(
                session,
                f"{_SCHWARZ_API}?flyer_identifier={ident}&region_id=0&region_code=0",
            )
            brochure = parse_schwarz(chain, ident, json.loads(text), today)
        except (SourceError, ValueError) as exc:
            _LOGGER.debug("Leaflet %s skipped: %s", ident, exc)
            continue
        if brochure:
            found[brochure["id"]] = brochure
    for url in links["publitas"][:6]:
        try:
            text = await fetch_text(session, f"{url}/data.json")
            brochure = parse_publitas(chain, url, json.loads(text), today)
        except (SourceError, ValueError) as exc:
            _LOGGER.debug("Publitas %s skipped: %s", url, exc)
            continue
        if brochure:
            found[brochure["id"]] = brochure
    if not found:
        for url in links["pdf"][:4]:
            brochure = pdf_brochure(chain, url, today)
            found[brochure["id"]] = brochure
    # Brochures that ended already are of no use.
    return [
        brochure
        for brochure in found.values()
        if not brochure["valid_to"] or date.fromisoformat(brochure["valid_to"]) >= today
    ]
