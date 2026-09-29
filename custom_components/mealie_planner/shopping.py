"""The week's products: what the planned recipes need, and where it is on sale.

Recomputed from the plan on every change, so it always matches the week.
The user's own choices, a product picked by hand and what is ticked, are
kept for as long as the ingredient is still needed.
"""

from __future__ import annotations

from typing import Any

from .classify import classify
from .offers import OfferIndex
from .text import normalize, overlap, stems

NO_SHOP = "none"
_WATER = {"вода", "топла вода", "студена вода", "гореща вода", "хладка вода", "water"}


def ingredient_key(name: str, unit: str | None) -> str:
    return " ".join(stems(name)[:5]) + "|" + normalize(unit)


def _price_order(offer: dict[str, Any]) -> tuple:
    # Unit prices are only comparable within the same base (kg, l, piece).
    return (offer.get("unit_price") is None, offer.get("unit_price") or 0, offer.get("price") or 0)


def aggregate(recipes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The ingredients of the planned recipes, added up by food and unit."""
    items: dict[str, dict[str, Any]] = {}
    for recipe in recipes:
        for line in recipe.get("ingredients") or []:
            name = (line.get("food") or line.get("text") or "").strip()
            if not name or normalize(name) in _WATER or not stems(name):
                continue
            key = ingredient_key(name, line.get("unit"))
            item = items.get(key)
            if item is None:
                item = items[key] = {
                    "key": key,
                    "name": name,
                    "food": line.get("food"),
                    "unit": line.get("unit"),
                    "quantity": 0.0,
                    "unknown_quantity": False,
                    "recipes": [],
                }
            if line.get("quantity"):
                item["quantity"] += float(line["quantity"])
            else:
                item["unknown_quantity"] = True
            if recipe.get("name") and recipe["name"] not in item["recipes"]:
                item["recipes"].append(recipe["name"])
    for item in items.values():
        item["quantity"] = round(item["quantity"], 2) or None
    return sorted(items.values(), key=lambda item: normalize(item["name"]))


def basket(
    recipes: list[dict[str, Any]],
    index: OfferIndex,
    overrides: dict[str, str] | None = None,
    checked: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Each needed ingredient with its offer and shop, or none.

    `index` holds the offers valid during the planned week. The cheapest match
    wins unless the user picked another offer, or no shop, by hand.
    """
    overrides = overrides or {}
    checked = checked or set()
    by_id = {offer["id"]: offer for offer in index.offers}
    result = []
    for item in aggregate(recipes):
        found = sorted(index.match(item["name"]), key=_price_order)
        choice = overrides.get(item["key"])
        if choice == NO_SHOP:
            offer = None
        elif choice in by_id:
            offer = by_id[choice]
        else:
            offer = found[0] if found else None
        result.append(
            {
                **item,
                "offer": offer,
                "shop": offer["chain"] if offer else None,
                "matches": len(found),
                "picked": item["key"] in overrides and (choice == NO_SHOP or choice in by_id),
                "checked": item["key"] in checked,
            }
        )
    return result


def prune(state: dict[str, Any], items: list[dict[str, Any]]) -> None:
    """Forget choices for ingredients the week no longer needs."""
    keys = {item["key"] for item in items}
    state["overrides"] = {key: value for key, value in (state.get("overrides") or {}).items() if key in keys}
    state["checked"] = [key for key in state.get("checked") or [] if key in keys]


def alternatives(item: dict[str, Any], index: OfferIndex, limit: int = 40) -> list[dict[str, Any]]:
    """Similar products on sale that week, closest first.

    1. the same generic food ("сьомга" from other brands, sizes and shops);
    2. products whose names share the ingredient's words;
    3. products of the same kind (other fish, when the ingredient is fish).
    Within each group the lowest unit price comes first.
    """
    name = item["name"]
    current = (item.get("offer") or {}).get("id")
    same_food = {offer["id"] for offer in index.match(name)}
    kind = (item.get("offer") or {}).get("category") or classify(name)[1]
    groups: dict[str, list[dict[str, Any]]] = {"food": [], "name": [], "category": []}
    for offer in index.offers:
        if offer["id"] == current:
            continue
        if offer["id"] in same_food:
            groups["food"].append(offer)
        elif overlap(name, offer.get("name")) >= 0.5:
            groups["name"].append(offer)
        elif kind and offer.get("category") == kind:
            groups["category"].append(offer)
    ranked = []
    for group, members in groups.items():
        for offer in sorted(members, key=_price_order):
            ranked.append({**offer, "similarity": group})
    return ranked[:limit]


def sale_score(recipe: dict[str, Any], index: OfferIndex) -> tuple[float, list[str]]:
    """How much of a recipe is on sale: one point per ingredient, more for deeper discounts."""
    score = 0.0
    names: list[str] = []
    for line in recipe.get("ingredients") or []:
        name = line.get("food") or line.get("text")
        if not name:
            continue
        found = index.match(name)
        if found:
            best = max((offer.get("discount_pct") or 0) for offer in found)
            score += 1 + best / 100
            names.append(name)
    return round(score, 2), names
