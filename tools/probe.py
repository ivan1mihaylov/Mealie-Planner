"""Check what each shop's source finds right now, without Home Assistant or AI.

The panel has the same check under Offers → "Check the sources". This script
is for a computer with Python and aiohttp:

    pip install aiohttp
    python3 tools/probe.py            # all shops
    python3 tools/probe.py kaufland   # one shop

It prints, per source, how many offers or brochures it found, a few samples
and any error, so a changed shop page shows up before the planner misses it.
"""

from __future__ import annotations

import asyncio
from datetime import date
import json
from pathlib import Path
import sys
import types

COMPONENT = Path(__file__).resolve().parent.parent / "custom_components" / "mealie_planner"
package = types.ModuleType("mealie_planner")
package.__path__ = [str(COMPONENT)]
sys.modules["mealie_planner"] = package

import aiohttp  # noqa: E402

from mealie_planner.const import DEFAULT_BROCHURE_URLS  # noqa: E402
from mealie_planner.sources import billa, brochures, kaufland, lidl  # noqa: E402
from mealie_planner.sources.common import SourceError  # noqa: E402

WEB = {"kaufland": kaufland.fetch, "lidl": lidl.fetch, "billa": billa.fetch}


async def main(chains: list[str]) -> None:
    today = date.today()
    async with aiohttp.ClientSession() as session:
        for chain in chains:
            print(f"\n=== {chain}: website offers")
            try:
                found = await WEB[chain](session, today)
                dated = sum(1 for offer in found if offer.get("valid_to"))
                classified = sum(1 for offer in found if offer.get("category"))
                print(f"{len(found)} offers, {dated} with their own dates, {classified} classified without AI")
                for offer in found[:3]:
                    print(json.dumps(offer, ensure_ascii=False, indent=1))
            except SourceError as exc:
                print(f"ERROR {exc}")
            url = DEFAULT_BROCHURE_URLS[chain]
            print(f"\n=== {chain}: brochures on {url}")
            try:
                found = await brochures.find(session, chain, url, today)
                print(f"{len(found)} brochures")
                for brochure in found:
                    pages = len(brochure.get("pages") or [])
                    print(f"- {brochure['title']} {brochure['valid_from']}–{brochure['valid_to']}: {pages} pages, pdf: {brochure.get('pdf') or '-'}")
            except SourceError as exc:
                print(f"ERROR {exc}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or list(WEB)))
