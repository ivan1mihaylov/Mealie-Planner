"""A local index of Mealie's recipes: names, tags, categories and ingredients.

A recipe's details are fetched again only when Mealie says it changed.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .mealie import MealieClient, PlannerError
from .text import contains, normalize

_LOGGER = logging.getLogger(__name__)
_PARALLEL = 4


def _names(items: Any) -> list[str]:
    return [item.get("name") for item in items or [] if isinstance(item, dict) and item.get("name")]


def summarize(detail: dict[str, Any]) -> dict[str, Any]:
    """What the planner keeps of a recipe."""
    ingredients = []
    for line in detail.get("recipeIngredient") or []:
        if not isinstance(line, dict):
            continue
        food = (line.get("food") or {}).get("name") if isinstance(line.get("food"), dict) else None
        unit_data = line.get("unit") if isinstance(line.get("unit"), dict) else {}
        unit = unit_data.get("abbreviation") or unit_data.get("name") if unit_data else None
        text = line.get("note") or line.get("originalText") or line.get("display") or ""
        if not food and not text.strip():
            continue
        # A section heading ("За соса") has a title and nothing else.
        if not food and line.get("title") and not line.get("quantity"):
            continue
        quantity = line.get("quantity")
        ingredients.append(
            {
                "food": food,
                "text": text.strip() or None,
                "quantity": float(quantity) if isinstance(quantity, (int, float)) and quantity else None,
                "unit": unit or None,
            }
        )
    return {
        "id": detail.get("id"),
        "slug": detail.get("slug"),
        "name": detail.get("name"),
        "tags": _names(detail.get("tags")),
        "categories": _names(detail.get("recipeCategory")),
        "updated": _updated(detail),
        "servings": detail.get("recipeServings") or detail.get("recipeYieldQuantity"),
        "image": bool(detail.get("image")),
        "ingredients": ingredients,
    }


def _updated(recipe: dict[str, Any]) -> str | None:
    return recipe.get("dateUpdated") or recipe.get("updatedAt") or recipe.get("updateAt")


class RecipeIndex:
    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.recipes: dict[str, dict[str, Any]] = dict((data or {}).get("recipes") or {})

    def as_dict(self) -> dict[str, Any]:
        return {"recipes": self.recipes}

    def by_id(self, recipe_id: str | None) -> dict[str, Any] | None:
        if recipe_id is None:
            return None
        return self.recipes.get(recipe_id)

    async def refresh(self, mealie: MealieClient) -> int:
        """Bring the index up to date; returns how many recipes were read in full."""
        summaries = await mealie.recipes()
        seen: set[str] = set()
        todo: list[dict[str, Any]] = []
        for summary in summaries:
            recipe_id = summary.get("id")
            if not recipe_id:
                continue
            seen.add(recipe_id)
            known = self.recipes.get(recipe_id)
            if known is None or known.get("updated") != _updated(summary) or not _updated(summary):
                todo.append(summary)
        for recipe_id in list(self.recipes):
            if recipe_id not in seen:
                del self.recipes[recipe_id]

        semaphore = asyncio.Semaphore(_PARALLEL)

        async def read(summary: dict[str, Any]) -> None:
            async with semaphore:
                try:
                    detail = await mealie.recipe(summary["slug"])
                except PlannerError as exc:
                    _LOGGER.debug("Recipe %s skipped: %s", summary.get("slug"), exc)
                    return
            if isinstance(detail, dict):
                self.recipes[summary["id"]] = summarize(detail)

        # Recipes without a change date would be read on every run; read
        # those only when they are new.
        todo = [s for s in todo if _updated(s) or s["id"] not in self.recipes]
        await asyncio.gather(*(read(summary) for summary in todo))
        return len(todo)

    def search(self, query: str, limit: int = 30) -> list[dict[str, Any]]:
        wanted = normalize(query)
        found = [
            recipe
            for recipe in self.recipes.values()
            if wanted in normalize(recipe.get("name")) or contains(query, recipe.get("name"))
        ]
        found.sort(key=lambda recipe: (not normalize(recipe.get("name")).startswith(wanted), recipe.get("name") or ""))
        return found[:limit]
