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


class AIClient:
    def __init__(self, session: ClientSession, base_url: str, api_key: str, model: str) -> None:
        self._session = session
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.model = model
        # Providers without json_schema support get json_object after the first refusal.
        self._schema_ok = True

    async def _post(self, body: dict[str, Any], timeout: int) -> dict[str, Any]:
        try:
            async with asyncio.timeout(timeout):
                async with self._session.post(self._url, json=body, headers=self._headers) as response:
                    text = await response.text()
                    if response.status in (401, 403):
                        raise PlannerError("AI услугата отказа ключа.", "ai_auth")
                    if response.status >= 400:
                        raise PlannerError(f"AI грешка {response.status}: {text[:300]}", "ai_error")
                    return json.loads(text)
        except PlannerError:
            raise
        except (TimeoutError, ClientError, ValueError) as exc:
            raise PlannerError("AI услугата не отговаря.", "ai_unreachable") from exc

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
        """The model's JSON answer and the tokens used."""
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
        if schema is not None and self._schema_ok:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": name, "schema": schema, "strict": False},
            }
        else:
            body["response_format"] = {"type": "json_object"}
        try:
            answer = await self._post(body, timeout)
        except PlannerError as exc:
            if exc.code != "ai_error" or "response_format" not in body:
                raise
            # Older or local models reject json_schema; ask for plain JSON instead.
            self._schema_ok = False
            body["response_format"] = {"type": "json_object"}
            try:
                answer = await self._post(body, timeout)
            except PlannerError as again:
                if again.code != "ai_error":
                    raise
                body.pop("response_format")
                answer = await self._post(body, timeout)
        usage = answer.get("usage") or {}
        tokens = {
            "prompt": int(usage.get("prompt_tokens") or 0),
            "completion": int(usage.get("completion_tokens") or 0),
        }
        try:
            message = answer["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise PlannerError("AI върна неочакван отговор.", "ai_error") from exc
        return parse_json(message), tokens

    async def check(self) -> None:
        """A tiny call to prove the URL, key and model work."""
        await self.chat_json(
            "Answer with JSON only.",
            'Return {"ok": true}.',
            schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
            max_tokens=20,
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
