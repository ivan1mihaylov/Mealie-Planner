"""The parts of Mealie's API the planner uses."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiohttp import ClientError, ClientSession

_LOGGER = logging.getLogger(__name__)


class PlannerError(Exception):
    """A failure the panel can show; the message is meant for people."""

    def __init__(self, message: str, code: str = "failed") -> None:
        super().__init__(message)
        self.code = code


class MealieClient:
    """Talk to Mealie with a long-lived API token."""

    def __init__(self, session: ClientSession, url: str, token: str) -> None:
        self._session = session
        self.url = url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}
        self._group: str | None = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        timeout: int = 30,
    ) -> Any:
        try:
            async with asyncio.timeout(timeout):
                async with self._session.request(
                    method, f"{self.url}{path}", params=params, json=json, headers=self._headers
                ) as response:
                    if response.status in (401, 403):
                        raise PlannerError("Mealie отказа API токена.", "invalid_auth")
                    if response.status >= 400:
                        detail = await response.text()
                        raise PlannerError(
                            f"Mealie върна грешка {response.status}: {detail[:200]}", "mealie_error"
                        )
                    if response.status == 204:
                        return None
                    return await response.json(content_type=None)
        except PlannerError:
            raise
        except (TimeoutError, ClientError, ValueError) as exc:
            _LOGGER.debug("Mealie request %s %s failed", method, path, exc_info=True)
            raise PlannerError("Mealie не отговаря.", "cannot_connect") from exc

    async def check(self) -> None:
        """Make sure the URL is Mealie and the token works."""
        user = await self._request("GET", "/api/users/self", timeout=15)
        if not isinstance(user, dict):
            raise PlannerError("Адресът не е Mealie API.", "cannot_connect")
        self._group = user.get("groupSlug") or self._group

    async def group(self) -> str:
        """The group slug, for links into Mealie."""
        if self._group is None:
            try:
                await self.check()
            except PlannerError:
                pass
        return self._group or "home"

    async def _all(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Read every page of a paginated list."""
        items: list[dict[str, Any]] = []
        page = 1
        while True:
            body = await self._request(
                "GET", path, params={**(params or {}), "page": page, "perPage": 100}
            )
            if not isinstance(body, dict):
                break
            items.extend(body.get("items") or [])
            total = body.get("total_pages") or body.get("totalPages") or 1
            if page >= total or not body.get("items"):
                break
            page += 1
        return items

    async def recipes(self) -> list[dict[str, Any]]:
        """Every recipe's summary: id, slug, name, tags, categories and when it changed."""
        return await self._all("/api/recipes", {"orderBy": "name", "orderDirection": "asc"})

    async def recipe(self, slug: str) -> dict[str, Any]:
        """One recipe with its ingredients."""
        return await self._request("GET", f"/api/recipes/{slug}")

    async def tags(self) -> list[dict[str, Any]]:
        return await self._all("/api/organizers/tags")

    async def categories(self) -> list[dict[str, Any]]:
        return await self._all("/api/organizers/categories")

    async def foods(self) -> list[dict[str, Any]]:
        return await self._all("/api/foods")

    async def mealplans(self, start: str, end: str) -> list[dict[str, Any]]:
        """Meal plan entries between two ISO dates, both included."""
        return await self._all(
            "/api/households/mealplans", {"start_date": start, "end_date": end}
        )

    async def add_mealplan(self, date: str, entry_type: str, recipe_id: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/households/mealplans",
            json={"date": date, "entryType": entry_type, "recipeId": recipe_id, "title": "", "text": ""},
        )

    async def delete_mealplan(self, plan_id: Any) -> None:
        try:
            await self._request("DELETE", f"/api/households/mealplans/{plan_id}")
        except PlannerError as exc:
            # Already gone is what we wanted.
            if "404" not in str(exc):
                raise

