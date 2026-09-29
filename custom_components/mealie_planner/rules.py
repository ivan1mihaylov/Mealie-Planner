"""The week's rules ("1 to 2 fish recipes", "a soup if possible") and checking them.

A rule is:

    {"id", "name", "kind": "required" | "preferred", "min", "max",
     "mode": "contains" | "excludes", "tags": [], "categories": [], "foods": []}

"contains" matches a recipe with one of the tags or categories, or with an
ingredient (or a name) that mentions one of the foods. "excludes" matches a
recipe none of whose ingredients mention the foods: "без месо".
"""

from __future__ import annotations

from typing import Any
import uuid

from .text import contains, normalize

REQUIRED = "required"
PREFERRED = "preferred"

_FISH = ["риба", "рибена", "рибно", "сьомга", "скумрия", "пъстърва", "ципура", "лаврак", "риба тон", "хек",
         "треска", "пангасиус", "херинга", "сардини", "цаца", "шаран", "скариди", "калмари", "миди"]
_LEGUMES = ["боб", "фасул", "леща", "нахут", "грах", "соя"]
_MEAT = ["месо", "кайма", "пиле", "пилешко", "пилешки", "свинско", "свински", "телешко", "телешки",
         "агнешко", "пуешко", "говеждо", "бекон", "шунка", "наденица", "кренвирши", "салам",
         "луканка", "суджук", "кебапчета", "кюфтета", "дроб", "бут", "врат", "пържола"]


def presets() -> list[dict[str, Any]]:
    """The four rules from the example, ready to adjust."""
    return [
        {"id": "fish", "name": "Риба", "kind": REQUIRED, "min": 1, "max": 2, "mode": "contains",
         "tags": ["Риба"], "categories": ["Риба"], "foods": list(_FISH)},
        {"id": "legumes", "name": "Бобови", "kind": REQUIRED, "min": 1, "max": None, "mode": "contains",
         "tags": ["Бобови"], "categories": ["Бобови"], "foods": list(_LEGUMES)},
        {"id": "soup", "name": "Супа", "kind": PREFERRED, "min": 1, "max": None, "mode": "contains",
         "tags": ["Супа", "Супи"], "categories": ["Супи", "Супа", "Чорби"], "foods": []},
        {"id": "meatless", "name": "Без месо", "kind": PREFERRED, "min": 1, "max": None, "mode": "excludes",
         # Without meat means without fish too; take the fish out to allow it.
         "tags": [], "categories": [], "foods": _MEAT + [food for food in _FISH if food not in _MEAT]},
    ]


def clean_rule(rule: dict[str, Any]) -> dict[str, Any]:
    """A rule as stored: known keys only, sane numbers."""
    low = max(0, int(rule.get("min") or 0))
    high = rule.get("max")
    high = None if high in (None, "") else max(low, int(high))

    def texts(key: str) -> list[str]:
        return [str(value).strip() for value in rule.get(key) or [] if str(value).strip()]

    return {
        "id": str(rule.get("id") or uuid.uuid4().hex[:8]),
        "name": str(rule.get("name") or "").strip() or "?",
        "kind": PREFERRED if rule.get("kind") == PREFERRED else REQUIRED,
        "min": low,
        "max": high,
        "mode": "excludes" if rule.get("mode") == "excludes" else "contains",
        "tags": texts("tags"),
        "categories": texts("categories"),
        "foods": texts("foods"),
    }


def _ingredient_texts(recipe: dict[str, Any]) -> list[str]:
    return [
        " ".join(part for part in (line.get("food"), line.get("text")) if part)
        for line in recipe.get("ingredients") or []
    ]


def matches(recipe: dict[str, Any], rule: dict[str, Any]) -> bool:
    foods = rule.get("foods") or []
    texts = _ingredient_texts(recipe)
    name = recipe.get("name") or ""
    if rule.get("mode") == "excludes":
        # Nothing known about the ingredients says nothing about meat.
        if not texts:
            return False
        return not any(contains(food, text) for food in foods for text in texts + [name])
    wanted_tags = {normalize(tag) for tag in rule.get("tags") or []}
    wanted_categories = {normalize(category) for category in rule.get("categories") or []}
    if wanted_tags & {normalize(tag) for tag in recipe.get("tags") or []}:
        return True
    if wanted_categories & {normalize(category) for category in recipe.get("categories") or []}:
        return True
    return any(contains(food, text) for food in foods for text in texts + [name])


def flags(recipe: dict[str, Any], rules: list[dict[str, Any]]) -> list[str]:
    """The ids of the rules a recipe counts towards."""
    return [rule["id"] for rule in rules if matches(recipe, rule)]


def check(recipe_flags: list[list[str]], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """How a week's recipes meet the rules.

    Takes the flags of each planned recipe. Returns one line per rule, with
    "ok", or "missing" for a required rule below its minimum (an error),
    "short" for a preferred one (a warning), and "over" above a maximum.
    """
    report = []
    for rule in rules:
        count = sum(1 for flagged in recipe_flags if rule["id"] in flagged)
        if count < rule["min"]:
            state = "missing" if rule["kind"] == REQUIRED else "short"
        elif rule.get("max") is not None and count > rule["max"]:
            state = "over"
        else:
            state = "ok"
        report.append(
            {"id": rule["id"], "name": rule["name"], "kind": rule["kind"], "count": count,
             "min": rule["min"], "max": rule.get("max"), "state": state}
        )
    return report
