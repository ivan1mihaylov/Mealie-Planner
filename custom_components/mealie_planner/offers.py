"""The offers kept between runs: what each source gave, until each offer ends.

Every offer carries its own dates. An offer leaves the book the day after its
own `valid_to`; a brochure's record stays until its last offer has left, so a
brochure is never read twice. Nothing here talks to Home Assistant.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from .text import contains_stems, overlap, overlaps, stems

WEB = "web"
BROCHURE = "brochure"


class OfferBook:
    def __init__(self, data: dict[str, Any] | None = None) -> None:
        data = data or {}
        self.offers: dict[str, dict[str, Any]] = dict(data.get("offers") or {})
        self.sources: dict[str, dict[str, Any]] = dict(data.get("sources") or {})
        self.usage: dict[str, int] = {"prompt": 0, "completion": 0, **(data.get("usage") or {})}
        # Which way of asking got each shop site's whole page, by host.
        self.profiles: dict[str, str] = dict(data.get("profiles") or {})

    def as_dict(self) -> dict[str, Any]:
        return {"offers": self.offers, "sources": self.sources, "usage": self.usage, "profiles": self.profiles}

    def add_usage(self, tokens: dict[str, int]) -> None:
        for key in ("prompt", "completion"):
            self.usage[key] = self.usage.get(key, 0) + int(tokens.get(key, 0))

    # --- Expiry ---------------------------------------------------------------
    def purge(self, today: date) -> int:
        """Drop offers that have ended, and brochures with nothing left in them."""
        ended = [
            key
            for key, offer in self.offers.items()
            if offer.get("valid_to") and date.fromisoformat(offer["valid_to"]) < today
        ]
        for key in ended:
            del self.offers[key]
        alive = {offer["source_id"] for offer in self.offers.values()}
        for source_id, source in list(self.sources.items()):
            if source.get("kind") != BROCHURE or source_id in alive:
                continue
            end = source.get("valid_to")
            # A brochure without dates is forgotten a fortnight after it was read.
            scanned = source.get("scanned_at", "")[:10]
            if end:
                over = date.fromisoformat(end) < today
            else:
                over = bool(scanned) and (today - date.fromisoformat(scanned)).days > 14
            if over:
                del self.sources[source_id]
        return len(ended)

    # --- Web offers -----------------------------------------------------------
    def replace_web(self, chain: str, offers: list[dict[str, Any]], when: str, error: str | None = None) -> list[dict[str, Any]]:
        """Put a fresh read of a chain's offer pages in place of the last one.

        Offers seen before keep what was learned about them (food and category
        named by AI), so they are never sent to AI again. Returns the offers
        that still have no category.
        """
        source_id = f"{chain}:{WEB}"
        if error is not None:
            self.sources[source_id] = {**self.sources.get(source_id, {}), "kind": WEB, "chain": chain, "error": error, "checked_at": when}
            return []
        previous = {key: offer for key, offer in self.offers.items() if offer.get("source_id") == source_id}
        for key in previous:
            del self.offers[key]
        for offer in offers:
            before = previous.get(offer["id"])
            if before is not None and not offer.get("category") and before.get("category"):
                offer["food"] = before.get("food")
                offer["category"] = before.get("category")
            self.offers[offer["id"]] = offer
        self.sources[source_id] = {
            "kind": WEB,
            "chain": chain,
            "title": "web",
            "count": len(offers),
            "checked_at": when,
            "error": None,
        }
        return [offer for offer in offers if not offer.get("category")]

    def web_offers_by_url(self, chain: str) -> dict[str, dict[str, Any]]:
        source_id = f"{chain}:{WEB}"
        return {offer["url"]: offer for offer in self.offers.values() if offer.get("source_id") == source_id and offer.get("url")}

    # --- Brochures ------------------------------------------------------------
    def knows(self, brochure_id: str) -> bool:
        source = self.sources.get(brochure_id)
        return source is not None and not source.get("error")

    def add_brochure(
        self,
        brochure: dict[str, Any],
        offers: list[dict[str, Any]],
        when: str,
        tokens: dict[str, int] | None = None,
        error: str | None = None,
    ) -> int:
        """Record a read brochure. Offers already known from the chain's web pages are merged."""
        tokens = tokens or {"prompt": 0, "completion": 0}
        self.add_usage(tokens)
        for key in [key for key, offer in self.offers.items() if offer.get("source_id") == brochure["id"]]:
            del self.offers[key]
        added = 0
        web = [offer for offer in self.offers.values() if offer["chain"] == brochure["chain"] and offer["source_id"].endswith(f":{WEB}")]
        for offer in offers:
            if any(_same_offer(offer, other) for other in web):
                continue
            self.offers[offer["id"]] = offer
            added += 1
        self.sources[brochure["id"]] = {
            "kind": BROCHURE,
            "chain": brochure["chain"],
            "title": brochure.get("title"),
            "valid_from": brochure.get("valid_from"),
            "valid_to": brochure.get("valid_to"),
            "pages": len(brochure.get("pages") or []) or None,
            "pdf": brochure.get("pdf"),
            "url": brochure.get("url"),
            # Kept whole so a rescan can read it again without finding it first.
            "brochure": brochure,
            "count": added,
            "tokens": tokens,
            "scanned_at": when,
            "error": error,
        }
        return added

    def forget(self, source_id: str) -> None:
        """Drop a brochure and its offers, so it is read again."""
        self.sources.pop(source_id, None)
        for key in [key for key, offer in self.offers.items() if offer.get("source_id") == source_id]:
            del self.offers[key]

    def fill_page_images(self) -> None:
        """Give brochure offers without a picture their page, where it is known."""
        for offer in self.offers.values():
            if offer.get("image") or not offer.get("page"):
                continue
            pages = ((self.sources.get(offer.get("source_id")) or {}).get("brochure") or {}).get("pages") or []
            if 1 <= offer["page"] <= len(pages):
                offer["image"] = pages[offer["page"] - 1]

    # --- Reading --------------------------------------------------------------
    def current(self, today: date) -> list[dict[str, Any]]:
        """Offers that have not ended, including ones that start later."""
        return [
            offer
            for offer in self.offers.values()
            if not offer.get("valid_to") or date.fromisoformat(offer["valid_to"]) >= today
        ]

    def in_period(self, start: date, end: date) -> list[dict[str, Any]]:
        """Offers whose own dates overlap the period; non-food is left out."""
        return [
            offer
            for offer in self.offers.values()
            if offer.get("category") != "non_food" and overlaps(offer.get("valid_from"), offer.get("valid_to"), start, end)
        ]

    def status(self) -> dict[str, list[dict[str, Any]]]:
        by_chain: dict[str, list[dict[str, Any]]] = {}
        for source_id, source in self.sources.items():
            shown = {key: value for key, value in source.items() if key != "tokens"}
            by_chain.setdefault(source.get("chain", "?"), []).append({"id": source_id, **shown})
        return by_chain


def _same_offer(one: dict[str, Any], other: dict[str, Any]) -> bool:
    return (
        abs((one.get("price") or 0) - (other.get("price") or 0)) < 0.011
        and overlap(one.get("name"), other.get("name")) >= 0.75
    )


class OfferIndex:
    """Offers prepared for matching many ingredients quickly.

    Two words can only match when they share their first three letters, so
    offers are bucketed by that and only a bucket is compared.
    """

    def __init__(self, offers: list[dict[str, Any]]) -> None:
        self.offers = offers
        self._food = [stems(offer.get("food")) for offer in offers]
        self._name = [stems(offer.get("name")) for offer in offers]
        self._by_food: dict[str, set[int]] = {}
        self._by_name: dict[str, set[int]] = {}
        for index in range(len(offers)):
            for word in self._food[index]:
                self._by_food.setdefault(word[:3], set()).add(index)
            for word in self._name[index]:
                self._by_name.setdefault(word[:3], set()).add(index)
        self._memo: dict[str, list[dict[str, Any]]] = {}

    def match(self, name: str | None) -> list[dict[str, Any]]:
        """Offers for an ingredient: by the generic food, or by the product name."""
        if not name:
            return []
        if name in self._memo:
            return self._memo[name]
        wanted = stems(name)
        found: list[int] = []
        if wanted:
            first = wanted[0][:3]
            pool = set(self._by_food.get(first, ())) | set(self._by_name.get(first, ()))
            for word in wanted:
                pool |= self._by_food.get(word[:3], set())
            for index in sorted(pool):
                food = self._food[index]
                if food and (contains_stems(wanted, food) or contains_stems(food, wanted)):
                    found.append(index)
                elif contains_stems(wanted, self._name[index]):
                    found.append(index)
        result = [self.offers[index] for index in found]
        self._memo[name] = result
        return result


def matching(name: str, offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Offers for one ingredient, without building an index to keep."""
    return OfferIndex(offers).match(name)
