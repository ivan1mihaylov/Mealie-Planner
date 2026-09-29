"""The offer cache: a brochure is read once, and each offer leaves on its own date.

    python3 tests/test_offers_cache.py
"""

from __future__ import annotations

from datetime import date

import support
from support import check, done

from mealie_planner.offers import OfferBook
from mealie_planner.sources.common import make_offer


def offer(chain, source, name, price, start, end, **extra):
    return make_offer(chain, source_id=source, name=name, price=price, valid_from=start, valid_to=end, **extra)


brochure = {"id": "lidl:brochure:abc", "chain": "lidl", "title": "Брошура", "valid_from": "2026-09-28", "valid_to": "2026-10-04", "pages": ["p1"], "pdf": None}
mixed = [
    offer("lidl", brochure["id"], "Сьомга филе", 9.99, "2026-09-28", "2026-10-04"),
    offer("lidl", brochure["id"], "Картофи", 0.99, "2026-10-02", "2026-10-03"),  # само в петък и събота
    offer("lidl", brochure["id"], "Домати", 1.49, "2026-09-28", "2026-09-30"),
]

book = OfferBook()
check("unknown brochure", book.knows(brochure["id"]), False)
book.add_brochure(brochure, mixed, "2026-09-28T06:00:00", {"prompt": 1000, "completion": 200})
check("known after reading", book.knows(brochure["id"]), True)
check("tokens counted", book.usage, {"prompt": 1000, "completion": 200})

# Each offer ends on its own date, not the brochure's.
book.purge(date(2026, 10, 1))
check("only the tomatoes ended", sorted(o["name"] for o in book.offers.values()), ["Картофи", "Сьомга филе"])
book.purge(date(2026, 10, 4))
check("potatoes ended on the 3rd", sorted(o["name"] for o in book.offers.values()), ["Сьомга филе"])
check("brochure still known while an offer is left", book.knows(brochure["id"]), True)
book.purge(date(2026, 10, 5))
check("all ended", book.offers, {})
check("brochure forgotten after its last offer", brochure["id"] in book.sources, False)

# A brochure that failed is tried again.
book = OfferBook()
book.add_brochure(brochure, [], "2026-09-28T06:00:00", error="HTTP 500")
check("failed brochure is not known", book.knows(brochure["id"]), False)

# The planned week sees only offers whose own dates overlap it.
book = OfferBook()
book.add_brochure(brochure, mixed, "2026-09-28T06:00:00")
names = sorted(o["name"] for o in book.in_period(date(2026, 10, 3), date(2026, 10, 9)))
check("week of the 3rd", names, ["Картофи", "Сьомга филе"])

# Web offers: a new read replaces the last one, keeping what AI said about each.
book = OfferBook()
first = [offer("kaufland", "kaufland:web", "Нещо интересно", 2.0, "2026-10-01", "2026-10-07")]
unknown = book.replace_web("kaufland", first, "t1")
check("unclassified offer is reported", len(unknown), 1)
unknown[0]["food"], unknown[0]["category"] = "сос", "pantry"
again = [offer("kaufland", "kaufland:web", "Нещо интересно", 2.0, "2026-10-01", "2026-10-07"),
         offer("kaufland", "kaufland:web", "Боб зрял", 1.5, "2026-10-01", "2026-10-07")]
unknown = book.replace_web("kaufland", again, "t2")
check("nothing to ask AI again", unknown, [])
check("AI's answer kept", book.offers[again[0]["id"]]["category"], "pantry")
book.replace_web("kaufland", [again[1]], "t3")
check("offers gone from the site leave", len(book.offers), 1)
book.replace_web("kaufland", [], "t4", error="HTTP 503")
check("a failed read keeps the last offers", len(book.offers), 1)
check("and says so", book.sources["kaufland:web"]["error"], "HTTP 503")

# A brochure offer the website already has is not added twice.
book = OfferBook()
book.replace_web("lidl", [offer("lidl", "lidl:web", "Сьомга филе", 9.99, "2026-09-28", "2026-10-04")], "t")
added = book.add_brochure(brochure, mixed, "t")
check("duplicate of a web offer merged", added, 2)

# Reading again replaces the brochure's offers.
book.forget(brochure["id"])
check("forgotten brochure has no offers", [o for o in book.offers.values() if o["source_id"] == brochure["id"]], [])

done()
