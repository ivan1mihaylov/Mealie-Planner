"""An OpenAI-compatible chat client: OpenAI, OpenRouter, Ollama, LocalAI…

Only what the planner needs: JSON answers, with images or a PDF attached, and
a count of the tokens spent.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from typing import Any

from aiohttp import ClientError, ClientSession

from .mealie import PlannerError

_LOGGER = logging.getLogger(__name__)


# Parameters a service may refuse, in the order they are given up.
_OPTIONAL = ("reasoning_effort", "temperature")
_NAMED = re.compile(r"unsupported (?:parameter|value)[:\s]+['\"]?([\w.]+)", re.IGNORECASE)


class AIClient:
    def __init__(
        self, session: ClientSession, base_url: str, api_key: str, model: str, effort: str | None = None
    ) -> None:
        self._session = session
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.model = model
        self.effort = effort or None
        # What this service turned out to accept, learned from its refusals
        # and kept for the rest of the run: current OpenAI models want
        # max_completion_tokens and may take no temperature; Ollama and older
        # servers want max_tokens; some have no json_schema.
        self._token_param = "max_completion_tokens"
        self._tried_token_params = {"max_completion_tokens"}
        self._dropped: set[str] = set()
        self._format = 0  # 0 json_schema, 1 json_object, 2 none

    async def _post(self, body: dict[str, Any], timeout: int) -> dict[str, Any]:
        try:
            async with asyncio.timeout(timeout):
                async with self._session.post(self._url, json=body, headers=self._headers) as response:
                    text = await response.text()
                    if response.status in (401, 403):
                        raise PlannerError("AI услугата отказа ключа.", "ai_auth")
                    if response.status >= 400:
                        raise PlannerError(f"AI грешка {response.status}: {text[:500]}", "ai_error")
                    return json.loads(text)
        except PlannerError:
            raise
        except (TimeoutError, ClientError, ValueError) as exc:
            raise PlannerError("AI услугата не отговаря.", "ai_unreachable") from exc

    def _body(self, system: str, content: Any, schema: dict[str, Any] | None, name: str, budget: int) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            self._token_param: budget,
        }
        if "temperature" not in self._dropped:
            body["temperature"] = 0.2
        if self.effort and "reasoning_effort" not in self._dropped:
            body["reasoning_effort"] = self.effort
        if self._format == 0 and schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": name, "schema": schema, "strict": False},
            }
        elif self._format <= 1:
            body["response_format"] = {"type": "json_object"}
        return body

    def _adapt(self, message: str, body: dict[str, Any]) -> bool:
        """Change what is sent after a refusal; False when there is nothing left to change."""
        text = message.lower()
        named = _NAMED.search(message)
        refused = named.group(1).lower() if named else None
        # The token limit: switch to the other name, once.
        for param in ("max_completion_tokens", "max_tokens"):
            if param in body and (refused == param or (refused is None and param in text)):
                other = "max_tokens" if param == "max_completion_tokens" else "max_completion_tokens"
                if other not in self._tried_token_params:
                    self._tried_token_params.add(other)
                    self._token_param = other
                    return True
        for param in _OPTIONAL:
            if param in body and (refused == param or (refused is None and param in text)):
                self._dropped.add(param)
                return True
        # Anything else is taken as the answer format: step down from
        # json_schema to json_object to none, as before.
        if "response_format" in body:
            self._format += 1
            return True
        return False

    async def chat_json(
        self,
        system: str,
        content: list[dict[str, Any]] | str,
        *,
        schema: dict[str, Any] | None = None,
        name: str = "answer",
        max_tokens: int = 4000,
        timeout: int = 180,
    ) -> tuple[Any, dict[str, int]]:
        """The model's JSON answer and the tokens used.

        `max_tokens` is the budget for the whole answer. Reasoning models spend
        part of it thinking; an answer cut off before any text is asked again
        once with twice the budget.
        """
        budget = max_tokens
        grown = False
        tokens = {"prompt": 0, "completion": 0}
        for _ in range(10):
            body = self._body(system, content, schema, name, budget)
            try:
                answer = await self._post(body, timeout)
            except PlannerError as exc:
                if exc.code != "ai_error" or not self._adapt(str(exc), body):
                    raise
                _LOGGER.debug("AI refused a parameter, asking again: %s", exc)
                continue
            usage = answer.get("usage") or {}
            tokens["prompt"] += int(usage.get("prompt_tokens") or 0)
            tokens["completion"] += int(usage.get("completion_tokens") or 0)
            try:
                choice = answer["choices"][0]
                message = choice["message"].get("content") or ""
            except (KeyError, IndexError, TypeError, AttributeError) as exc:
                raise PlannerError("AI върна неочакван отговор.", "ai_error") from exc
            if not message.strip() and choice.get("finish_reason") == "length" and not grown:
                budget *= 2
                grown = True
                continue
            return parse_json(message), tokens
        raise PlannerError("AI не прие заявката.", "ai_error")

    async def check(self) -> None:
        """A tiny call to prove the URL, key and model work."""
        await self.chat_json(
            "Answer with JSON only.",
            'Return {"ok": true}.',
            schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
            # Room for a reasoning model to think; only what is used is billed.
            max_tokens=2000,
            timeout=30,
        )


def parse_json(text: str) -> Any:
    """JSON from a model's answer, tolerating code fences and chatter around it."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except ValueError:
        pass
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    if start >= 0:
        try:
            value, _ = json.JSONDecoder().raw_decode(text, start)
            return value
        except ValueError:
            pass
    raise PlannerError("AI не върна валиден JSON.", "ai_error")


def image_part(data: bytes, content_type: str) -> dict[str, Any]:
    kind = content_type if content_type.startswith("image/") else "image/jpeg"
    encoded = base64.b64encode(data).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{kind};base64,{encoded}", "detail": "high"}}


def pdf_part(data: bytes, filename: str = "brochure.pdf") -> dict[str, Any]:
    encoded = base64.b64encode(data).decode()
    return {"type": "file", "file": {"filename": filename, "file_data": f"data:application/pdf;base64,{encoded}"}}
