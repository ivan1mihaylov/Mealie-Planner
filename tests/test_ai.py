"""The AI client adapts to what a service accepts, against a fake service.

Current OpenAI models (GPT-6 Luna) want max_completion_tokens and may refuse
temperature; Ollama and older servers want max_tokens; some have no
json_schema. Each refusal is learned once.

    python3 tests/test_ai.py
"""

from __future__ import annotations

import asyncio
import json

import support
from support import check, done

from mealie_planner.ai import AIClient
from mealie_planner.mealie import PlannerError

SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}}


def answer(content='{"ok": true}', finish="stop", prompt=10, completion=5):
    return 200, {"choices": [{"message": {"content": content}, "finish_reason": finish}],
                 "usage": {"prompt_tokens": prompt, "completion_tokens": completion}}


def refuse(message, status=400):
    return status, {"error": {"message": message}}


class Response:
    def __init__(self, status, body):
        self.status = status
        self._text = json.dumps(body)

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class Service:
    """Answers in turn with the scripted replies, and keeps what was sent."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.sent = []

    def post(self, url, json=None, headers=None):
        self.sent.append(json)
        return Response(*self.replies.pop(0))


async def main():
    # GPT-6 Luna: everything accepted as sent.
    service = Service(answer())
    client = AIClient(service, "https://api.openai.com/v1", "key", "gpt-6-luna", effort="low")
    result, tokens = await client.chat_json("s", "u", schema=SCHEMA, max_tokens=100)
    body = service.sent[0]
    check("answer read", result, {"ok": True})
    check("tokens counted", tokens, {"prompt": 10, "completion": 5})
    check("model", body["model"], "gpt-6-luna")
    check("max_completion_tokens sent", (body.get("max_completion_tokens"), "max_tokens" in body), (100, False))
    check("reasoning effort sent", body["reasoning_effort"], "low")
    check("json_schema asked for", body["response_format"]["type"], "json_schema")

    # No effort chosen: none sent.
    service = Service(answer())
    await AIClient(service, "u", "k", "m").chat_json("s", "u", schema=SCHEMA)
    check("no effort, nothing sent", "reasoning_effort" in service.sent[0], False)

    # An older server that only knows max_tokens: learned once, kept.
    service = Service(refuse("Unsupported parameter: 'max_completion_tokens'. Use 'max_tokens'."), answer(), answer())
    client = AIClient(service, "http://ollama:11434/v1", "", "llava")
    await client.chat_json("s", "u", schema=SCHEMA, max_tokens=100)
    await client.chat_json("s", "u", schema=SCHEMA, max_tokens=100)
    check("retried with max_tokens", (service.sent[1].get("max_tokens"), "max_completion_tokens" in service.sent[1]), (100, False))
    check("and starts with it next time", service.sent[2].get("max_tokens"), 100)
    check("three calls, one refusal", len(service.sent), 3)

    # A model that allows only its own temperature, and no reasoning effort.
    service = Service(
        refuse("Unsupported value: 'temperature' does not support 0.2 with this model. Only the default (1) value is supported."),
        refuse("Unrecognized request argument supplied: reasoning_effort"),
        answer(),
    )
    client = AIClient(service, "u", "k", "m", effort="low")
    await client.chat_json("s", "u", schema=SCHEMA)
    last = service.sent[-1]
    check("temperature dropped", "temperature" in last, False)
    check("reasoning effort dropped", "reasoning_effort" in last, False)
    check("the rest kept", (last["response_format"]["type"], "max_completion_tokens" in last), ("json_schema", True))

    # No json_schema: json_object, then nothing, as before.
    service = Service(refuse("Invalid value for response_format"), refuse("response_format json_object is not supported"), answer())
    client = AIClient(service, "u", "k", "m")
    await client.chat_json("s", "u", schema=SCHEMA)
    check("json_object tried second", service.sent[1]["response_format"]["type"], "json_object")
    check("no format last", "response_format" in service.sent[2], False)

    # A reasoning model that thought through its whole budget: asked again with twice as much.
    service = Service(answer(content="", finish="length", completion=100), answer(completion=40))
    client = AIClient(service, "u", "k", "gpt-6-luna", effort="medium")
    result, tokens = await client.chat_json("s", "u", schema=SCHEMA, max_tokens=100)
    check("budget doubled", service.sent[1]["max_completion_tokens"], 200)
    check("both calls counted", tokens, {"prompt": 20, "completion": 140})
    check("answer read after the retry", result, {"ok": True})

    service = Service(answer(content="", finish="length"), answer(content="", finish="length"))
    try:
        await AIClient(service, "u", "k", "m").chat_json("s", "u", max_tokens=10)
        check("only one retry for the budget", False, True)
    except PlannerError:
        check("only one retry for the budget", len(service.sent), 2)

    # A wrong key is a wrong key, not a parameter to drop.
    service = Service(refuse("Incorrect API key", status=401))
    try:
        await AIClient(service, "u", "bad", "m").chat_json("s", "u")
        check("bad key", False, True)
    except PlannerError as exc:
        check("bad key", (exc.code, len(service.sent)), ("ai_auth", 1))

    # An error nothing can fix is raised once the format fallbacks are spent.
    service = Service(*[refuse("model not found")] * 5)
    try:
        await AIClient(service, "u", "k", "nope").chat_json("s", "u", schema=SCHEMA)
        check("unfixable error raised", False, True)
    except PlannerError as exc:
        check("unfixable error raised", (exc.code, len(service.sent)), ("ai_error", 3))


asyncio.run(main())
done()
