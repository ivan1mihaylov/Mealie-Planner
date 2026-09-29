"""Reading brochures with AI, against a fake AI: batches, dates per offer, JSON.

    python3 tests/test_extraction.py
"""

from __future__ import annotations

import asyncio

import support
from support import check, done

from mealie_planner import extraction
from mealie_planner.ai import parse_json


class FakeAI:
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = []

    async def chat_json(self, system, content, **kwargs):
        self.calls.append(content)
        return self.answers.pop(0), {"prompt": 100, "completion": 20}


async def fake_fetch(session, url, limit=0, timeout=0):
    return b"\xff\xd8image", "image/jpeg"


extraction.fetch_bytes = fake_fetch

brochure = {"id": "lidl:brochure:x", "chain": "lidl", "title": "Брошура", "valid_from": "2026-10-05",
            "valid_to": "2026-10-11", "pages": [f"https://x/{n}.jpg" for n in range(1, 7)], "pdf": None}
first = {"offers": [
    {"name": "Сьомга филе", "food": "сьомга", "category": "fish", "price": 9.99, "old_price": 12.99, "quantity": "500 г", "page": 1},
    {"name": "Картофи", "food": "картофи", "category": "vegetables", "price": 0.79, "valid_from": "2026-10-10", "valid_to": "2026-10-11", "page": 2},
    {"name": "Прахосмукачка", "food": None, "category": "non_food", "price": 79.0, "page": 3},
]}
second = {"offers": [{"name": "Боб зрял", "category": "legumes", "price": 1.49, "page": 5}]}


async def main():
    ai = FakeAI([first, second])
    offers, tokens = await extraction.read_brochure(ai, None, brochure, max_pages=40)
    check("six pages in two calls of up to four", len(ai.calls), 2)
    check("four images in the first call", sum(1 for part in ai.calls[0] if part.get("type") == "image_url"), 4)
    check("tokens added up", tokens, {"prompt": 200, "completion": 40})
    names = {o["name"]: o for o in offers}
    check("non-food left out", sorted(names), ["Боб зрял", "Картофи", "Сьомга филе"])
    check("brochure dates when the offer has none", (names["Сьомга филе"]["valid_from"], names["Сьомга филе"]["valid_to"]), ("2026-10-05", "2026-10-11"))
    check("the offer's own dates win", (names["Картофи"]["valid_from"], names["Картофи"]["valid_to"]), ("2026-10-10", "2026-10-11"))
    check("missing food filled from the table", names["Боб зрял"]["food"], "боб")
    check("discount computed", names["Сьомга филе"]["discount_pct"], 23)

    ai = FakeAI([first])
    await extraction.read_brochure(ai, None, brochure, max_pages=3)
    check("page limit respected", sum(1 for part in ai.calls[0] if part.get("type") == "image_url"), 3)

    todo = [{"name": "Лютеница Олинеза"}, {"name": "Нещо"}]
    ai = FakeAI([{"items": [{"i": 0, "food": "лютеница", "category": "pantry"}, {"i": 7, "category": "fish"}]}])
    await extraction.name_offers(ai, todo)
    check("named by AI", (todo[0]["food"], todo[0]["category"]), ("лютеница", "pantry"))
    check("unknown stays other food, not asked again", todo[1]["category"], "other_food")


asyncio.run(main())

check("json in a code fence", parse_json('```json\n{"a": 1}\n```'), {"a": 1})
check("json after chatter", parse_json('Here you go: {"a": [1, 2]} hope it helps'), {"a": [1, 2]})
check("pdf pages counted", extraction.pdf_page_count(b"/Type /Pages /Type /Page x /Type/Page y"), 2)

done()
