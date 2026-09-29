"""The week's products: shops, recalculation after an edit, similar products,
and handing them to HomeBasket Lists.

    python3 tests/test_shopping.py
"""

from __future__ import annotations

import asyncio
from datetime import date
import types

import support
from support import check, done

from mealie_planner import shopping
from mealie_planner.offers import OfferBook, OfferIndex
from mealie_planner.service import PlannerService
from mealie_planner.sources.common import make_offer


def offer(chain, name, price, start="2026-10-01", end="2026-10-11", quantity=None, old=None):
    return make_offer(chain, source_id=f"{chain}:web", name=name, price=price, old_price=old,
                      quantity=quantity, valid_from=start, valid_to=end)


OFFERS = [
    offer("lidl", "Сьомга филе", 12.99, quantity="500 г", old=15.99),       # 25.98 €/kg
    offer("kaufland", "Сьомга норвежка", 21.99, quantity="1 кг", old=27.99),  # 21.99 €/kg: cheaper per kg
    offer("billa", "Пъстърва цяла", 7.49, quantity="1 кг"),
    offer("billa", "Домати розови", 2.29, quantity="1 кг"),
    offer("lidl", "Домати чери", 1.99, quantity="250 г", start="2026-09-20", end="2026-09-30"),  # ended
    offer("kaufland", "Боб зрял", 1.79, quantity="1 кг"),
]
by_name = {o["name"]: o for o in OFFERS}

salmon = {"id": "s", "name": "Сьомга на фурна", "ingredients": [
    {"food": "сьомга", "quantity": 500, "unit": "г"}, {"food": "лимони", "quantity": 1, "unit": None},
    {"food": "вода", "quantity": 1, "unit": "л"}]}
salad = {"id": "d", "name": "Салата", "ingredients": [
    {"food": "домати", "quantity": 300, "unit": "г"}, {"food": None, "text": "сол", "quantity": None, "unit": None}]}
beans = {"id": "b", "name": "Боб", "ingredients": [
    {"food": "боб", "quantity": 500, "unit": "г"}, {"food": "домати", "quantity": 200, "unit": "г"}]}

week_offers = OfferBook({"offers": {o["id"]: o for o in OFFERS}}).in_period(date(2026, 10, 5), date(2026, 10, 11))
index = OfferIndex(week_offers)

# --- Adding up and choosing shops ---------------------------------------------------
items = {item["name"]: item for item in shopping.basket([salad, beans], index)}
check("same food and unit added up", items["домати"]["quantity"], 500.0)
check("both recipes listed", items["домати"]["recipes"], ["Салата", "Боб"])
check("offer valid in the week wins", items["домати"]["offer"]["name"], "Домати розови")
check("its shop", items["домати"]["shop"], "billa")
check("no offer, no shop", (items["сол"]["offer"], items["сол"]["shop"]), (None, None))

items = {item["name"]: item for item in shopping.basket([salmon], index)}
check("water is not shopping", "вода" in items, False)
check("cheapest per kg", items["сьомга"]["offer"]["name"], "Сьомга норвежка")

# The user's own pick stands, and "no shop" is a pick too.
key = items["сьомга"]["key"]
picked = {i["name"]: i for i in shopping.basket([salmon], index, {key: by_name["Сьомга филе"]["id"]})}
check("hand-picked offer", (picked["сьомга"]["offer"]["name"], picked["сьомга"]["picked"]), ("Сьомга филе", True))
none = {i["name"]: i for i in shopping.basket([salmon], index, {key: shopping.NO_SHOP})}
check("hand-picked no shop", (none["сьомга"]["shop"], none["сьомга"]["picked"]), (None, True))

# Similar products: same food, then similar names, then the same kind.
alts = shopping.alternatives(items["сьомга"], index)
check("other salmon first, then other fish", [(a["name"], a["similarity"]) for a in alts],
      [("Сьомга филе", "food"), ("Пъстърва цяла", "category")])
check("ended offers are not offered", "Домати чери" in [a["name"] for a in shopping.alternatives(items["лимони"], index)], False)

# The shop HomeBasket Lists keeps a product under.
on_lists = [{"summary": "Магданоз пресен", "store": "zone.pazar", "updated": "2026-09-20"},
            {"summary": "Лимони", "store": "zone.lidl", "updated": "2026-09-01"}]
check("same name", shopping.home_shop("лимони", on_lists), "zone.lidl")
check("all words in the item's name", shopping.home_shop("магданоз", on_lists), "zone.pazar")
check("nothing for an unknown product", shopping.home_shop("ориз", on_lists), None)
parsley = [{"key": "магданоз|", "name": "магданоз", "offer": None, "shop": None}]
shopping.apply_home_shops(parsley, on_lists, {"lidl": "zone.lidl"}, {"zone.pazar": "Пазар Жени"})
check("a shop that is not a chain keeps its own name", (parsley[0]["shop"], parsley[0]["shop_name"]), ("zone:zone.pazar", "Пазар Жени"))

score, sale = shopping.sale_score(salmon, index)
check("sale score counts the discount", (score, sale), (1.21, ["сьомга"]))


# --- Through the service: edits recalculate, choices are kept -----------------------
class FakeLists:
    api_version = 1

    def __init__(self):
        self.calls = []
        # Lemons and parsley only ever come from Lidl and the greengrocer's;
        # the lists keep them under those shops, bought or not.
        self.lists = [{"entry_id": "L1", "name": "Пазар", "items": [
            {"summary": "Лимони", "store": "zone.lidl", "status": "completed", "updated": "2026-09-01"},
            {"summary": "Лимони", "store": "zone.billa", "status": "completed", "updated": "2026-08-01"},
            {"summary": "Магданоз пресен", "store": "zone.pazar", "status": "needs_action", "updated": "2026-09-20"},
            {"summary": "Сол", "store": None, "status": "completed"},
        ]}]

    async def async_add_item(self, summary, *, entry_id=None, name=None, **fields):
        self.calls.append((summary, entry_id, fields))
        store = fields.get("store") or "zone.guessed"   # Lists guesses a shop when given none
        return {"entry_id": entry_id, "list": "Пазар", "outcome": "added",
                "item": {"uid": f"u{len(self.calls)}", "summary": summary, "store": store}}


class FakeRuntime:
    def __init__(self):
        self.updates = []

    async def async_update_item(self, uid, **fields):
        self.updates.append((uid, fields))


async def main():
    lists, runtime = FakeLists(), FakeRuntime()
    hass = types.SimpleNamespace(data={"homebasket_lists_api": lists, "homebasket_lists": {"L1": runtime}})
    entry = types.SimpleNamespace(
        data={"mealie_url": "http://mealie:9000", "mealie_token": "t"},
        options={"zone_lidl": "zone.lidl", "zone_billa": "zone.billa", "list_entry": "L1"},
    )
    service = PlannerService(hass, entry)

    async def group():
        return "home"

    service.mealie.group = group
    service.recipes.recipes = {r["id"]: r for r in (salmon, salad, beans)}
    service.book = OfferBook({"offers": {o["id"]: o for o in OFFERS}})
    week = date(2026, 10, 5)
    service.settings["slots"] = {str(day): ["dinner"] for day in range(7)}

    view = await service.async_update_slot(week, "2026-10-05|dinner", set_recipe=True, recipe_id="s", locked=None)
    view = await service.async_update_slot(week, "2026-10-06|dinner", set_recipe=True, recipe_id="d", locked=None)
    basket = {i["name"]: i for i in view["basket"]}
    check("basket follows the plan", sorted(basket), ["домати", "лимони", "сол", "сьомга"])

    await service.async_choose(week, basket["сьомга"]["key"], by_name["Сьомга филе"]["id"])
    view = await service.async_check(week, [basket["домати"]["key"]], True)

    # Changing a meal recalculates at once: the salad's products go, the beans' come.
    view = await service.async_update_slot(week, "2026-10-06|dinner", set_recipe=True, recipe_id="b", locked=None)
    basket = {i["name"]: i for i in view["basket"]}
    check("recalculated after the edit", sorted(basket), ["боб", "домати", "лимони", "сьомга"])
    check("hand-picked product kept", basket["сьомга"]["offer"]["name"], "Сьомга филе")
    check("tick kept while still needed", basket["домати"]["checked"], True)
    check("new ingredient arrives unticked", basket["боб"]["checked"], False)
    check("no longer needed is forgotten", "сол" in {k.split("|")[0] for k in service._draft(week)["checked"]}, False)

    # Moving a meal to another day keeps the products.
    view = await service.async_move_slot(week, "2026-10-06|dinner", "2026-10-08|dinner")
    check("moved", [s["recipe"]["id"] for s in view["slots"] if s["recipe"]], ["s", "b"])

    # Not on sale: the shop HomeBasket Lists keeps the product under.
    check("lemons: the most recent shop on the lists", (basket["лимони"]["shop"], basket["лимони"]["home_zone"]), ("lidl", "zone.lidl"))
    check("on offer: the offer's shop, not the lists'", basket["сьомга"]["home_zone"], None)

    # To HomeBasket Lists: each with its shop's zone, or none.
    wanted = [basket["сьомга"], basket["домати"], basket["лимони"], basket["боб"]]
    result = await service.async_add_to_list(wanted)
    check("four added", result, {"added": 4})
    calls = {summary: fields for summary, _, fields in lists.calls}
    check("list from the options", {entry for _, entry, _ in lists.calls}, {"L1"})
    check("lidl offer goes to zone.lidl", calls["сьомга"]["store"], "zone.lidl")
    check("note says shop, price and end", calls["сьомга"]["note"].startswith("Lidl · 12,99 € (−19%) до 11.10"), True)
    check("quantity and unit", (calls["сьомга"]["quantity"], calls["сьомга"]["unit"]), (500.0, "г"))
    check("billa offer goes to zone.billa", calls["домати"]["store"], "zone.billa")
    check("kaufland has no zone: none, and the note says so", ("store" in calls["боб"], "Kaufland" in calls["боб"]["note"]), (False, True))
    check("no offer: the shop from the lists", calls["лимони"]["store"], "zone.lidl")
    check("only the zoneless offer's guessed shop is cleared", [uid for uid, fields in runtime.updates], ["u4"])

    # "No shop" picked by hand stays no shop, whatever the lists say.
    view = await service.async_choose(week, basket["лимони"]["key"], "none")
    lemons = {i["name"]: i for i in view["basket"]}["лимони"]
    check("hand-picked no shop wins over the lists", (lemons["shop"], lemons["home_zone"]), (None, None))
    lists.calls.clear()
    runtime.updates.clear()
    await service.async_add_to_list([lemons])
    check("added without a shop", "store" in lists.calls[0][2], False)
    check("and the guess Lists made is cleared", runtime.updates, [("u1", {"store": None})])


async def without_homebasket():
    """Planning, products and offers work with neither HomeBasket nor its lists."""
    hass = types.SimpleNamespace(data={})
    entry = types.SimpleNamespace(data={"mealie_url": "http://mealie:9000", "mealie_token": "t"}, options={})
    service = PlannerService(hass, entry)

    async def group():
        return "home"

    service.mealie.group = group
    service.recipes.recipes = {r["id"]: r for r in (salmon, salad)}
    service.book = OfferBook({"offers": {o["id"]: o for o in OFFERS}})
    week = date(2026, 10, 5)
    view = await service.async_update_slot(week, "2026-10-05|dinner", set_recipe=True, recipe_id="s", locked=None)
    basket = {i["name"]: i for i in view["basket"]}
    check("alone: no lists offered", view["lists"], {"available": False, "lists": []})
    check("alone: products still by shop", basket["сьомга"]["shop"], "kaufland")
    check("alone: no shop from lists", basket["лимони"]["home_zone"], None)
    check("alone: offers still listed", len(service.offers_view()["offers"]) > 0, True)
    try:
        await service.async_add_to_list([basket["сьомга"]])
        check("alone: adding says why it cannot", False, True)
    except Exception as exc:  # noqa: BLE001
        check("alone: adding says why it cannot", getattr(exc, "code", None), "no_lists")


asyncio.run(main())
asyncio.run(without_homebasket())
done()
