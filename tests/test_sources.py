"""Reading the shops' pages, from small pages shaped like the real ones.

The shapes follow the live sites as a maintained scraper reads them
(github.com/StefanBratanov/sofia-supermarkets-api). If a shop changes its
page, run the source check in the panel and adjust the parser and these.

    python3 tests/test_sources.py
"""

from __future__ import annotations

from datetime import date
import json

import support
from support import check, done

from mealie_planner.sources import billa, brochures, kaufland, lidl
from mealie_planner.sources.common import SourceError, describe_page
from mealie_planner.sources.html import parse

TODAY = date(2026, 10, 1)

# --- The HTML helper ------------------------------------------------------------
root = parse('<div class="a b"><p class="x">one</p><section><p class="x">two</p></section></div><p class="x">three</p>')
check("descendant", [n.text() for n in root.select("div p.x")], ["one", "two"])
check("child", [n.text() for n in root.select("div > p.x")], ["one"])
check("two classes", len(root.select("div.a.b")), 1)
check("attribute", len(parse('<div data-selector="PRODUCT"></div><div></div>').select("div[data-selector=PRODUCT]")), 1)

# --- Kaufland -------------------------------------------------------------------
offer_data = {
    "component": "OfferTemplate",
    "props": {
        "offerData": {
            "cycles": [
                {
                    "categories": [
                        {
                            "displayName": "Плодове и зеленчуци",
                            "offers": [
                                {"title": "Брей! Зелен лук", "subtitle": "Клас: I", "unit": "1 връзка",
                                 "formattedPrice": "0,51", "formattedOldPrice": "0,76",
                                 "listImage": "https://kaufland.media.schwarz/is/image/schwarz/1",
                                 "dateFrom": "2026-09-28", "dateTo": "2026-10-04"},
                                {"title": "Люта чушка", "subtitle": "", "unit": "200г в опаковка",
                                 "formattedPrice": "1,27", "formattedOldPrice": "1,84",
                                 "dateFrom": "2026-10-01", "dateTo": "2026-10-03"},
                                {"title": "Без цена"},
                            ],
                        },
                        {
                            "displayName": "Месо и риба",
                            "offers": [
                                {"title": "Сьомга филе", "subtitle": "охладена", "unit": "1 кг",
                                 "formattedPrice": "14,99", "formattedOldPrice": "19,99",
                                 "dateFrom": "2026-09-28", "dateTo": "2026-10-04"},
                            ],
                        },
                        {
                            "displayName": "Седмични предложения",
                            "offers": [
                                # The same offer shown in a second category counts once.
                                {"title": "Сьомга филе", "subtitle": "охладена", "unit": "1 кг",
                                 "formattedPrice": "14,99", "formattedOldPrice": "19,99",
                                 "dateFrom": "2026-09-28", "dateTo": "2026-10-04"},
                            ],
                        },
                    ]
                }
            ]
        }
    },
}
page = f"""<html><head><script>window.x = 1;</script>
<script>var tpl = "OfferTemplate"; window.__data = {json.dumps(offer_data, ensure_ascii=False)};</script></head>
<body><button>Покажи още</button></body></html>"""
KAUFLAND_PAGE = page
found = kaufland.parse_offers(page, TODAY)
check("kaufland: every category, duplicates once, no price skipped", len(found), 3)
by_name = {offer["name"]: offer for offer in found}
salmon = by_name["Сьомга филе охладена"]
check("kaufland: price and old price", (salmon["price"], salmon["old_price"]), (14.99, 19.99))
check("kaufland: discount", salmon["discount_pct"], 25)
check("kaufland: classified", (salmon["food"], salmon["category"]), ("сьомга", "fish"))
check("kaufland: shop category kept", salmon["source_category"], "Месо и риба")
chili = by_name["Люта чушка"]
check("kaufland: own dates per offer", (chili["valid_from"], chili["valid_to"]), ("2026-10-01", "2026-10-03"))
check("kaufland: unit price", (chili["unit_price"], chili["unit_base"]), (6.35, "kg"))
# The same data moved out of "OfferTemplate" into other embedded JSON is still found.
moved = f"""<script id="__NEXT_DATA__" type="application/json">{json.dumps({"props": {"pageProps": offer_data["props"]["offerData"]}}, ensure_ascii=False)}</script>"""
check("kaufland: offers found in other embedded JSON", sorted(o["name"] for o in kaufland.parse_offers(moved, TODAY)), sorted(by_name))
assigned = f"""<script>window.__STATE__ = {json.dumps({"page": {"blocks": [{"categoryName": "Месо и риба", "offers": [
    {"title": "Скумрия", "subtitle": "цяла", "price": "3,99 €", "dateFrom": "2026-10-01", "dateTo": "2026-10-04"}]}]}}, ensure_ascii=False)};</script>"""
found = kaufland.parse_offers(assigned, TODAY)
check("kaufland: a plain price key and an assigned object", [(o["name"], o["price"], o["source_category"]) for o in found], [("Скумрия цяла", 3.99, "Месо и риба")])
try:
    kaufland.parse_offers("<html></html>", TODAY)
    check("kaufland: page without data fails loudly", False, True)
except SourceError:
    check("kaufland: page without data fails loudly", True, True)

page = describe_page("<html><head><title> Access Denied </title></head><script>x</script></html>")
check("page description names a block page", (page["title"], page["scripts"], page["markers"]["Access Denied"], page["markers"]["OfferTemplate"]), ("Access Denied", 1, True, False))

# --- Lidl -----------------------------------------------------------------------
home = """<ul><li class="AHeroStageItems__Item"><a href="/c/niska-tsena-visoko-kachestvo/a10023711">Ниска цена</a></li>
<li class="AHeroStageItems__Item"><a href="/c/lidl-plus/s10021179">Lidl Plus</a></li>
<li class="AHeroStageItems__Item"><a href="/c/kontakti/s1">Контакти</a></li></ul>"""
check("lidl: offer pages only", lidl.parse_offer_links(home), [
    "https://www.lidl.bg/c/niska-tsena-visoko-kachestvo/a10023711",
    "https://www.lidl.bg/c/lidl-plus/s10021179",
])
check("lidl: offer links found without the hero block", lidl.parse_offer_links(
    '<nav><a href="/c/lidl-plus/s10021179#top">Lidl Plus</a><a href="/c/kontakti/s1">Контакти</a></nav>'),
    ["https://www.lidl.bg/c/lidl-plus/s10021179"])
tiles = """<title>НИСКА цена, ВИСОКО качество</title>
<div data-selector="PRODUCT" canonicalurl="/p/pileshko-file/p100" image="https://img/1.jpg"></div>
<div data-selector="PRODUCT" canonicalurl="/p/domati/p200"></div>"""
title, products = lidl.parse_product_tiles(tiles)
check("lidl: page title is the category", title, "НИСКА цена, ВИСОКО качество")
check("lidl: product tiles", products, [("https://www.lidl.bg/p/pileshko-file/p100", "https://img/1.jpg"), ("https://www.lidl.bg/p/domati/p200", None)])
product = """<h1 class="heading__title">Пилешко филе</h1>
<div class="ods-price__stroke-price">5,10 €</div><div class="ods-price__value">3,99 €</div>
<div class="ods-price__footer">цена за кг</div><div class="ods-price__footer">1 кг</div>
<h3 class="availability">В магазина от 02.10. до 04.10.</h3>"""
offer = lidl.parse_product(product, TODAY, url="https://www.lidl.bg/p/pileshko-file/p100", image=None, category=title)
check("lidl: product", (offer["name"], offer["price"], offer["old_price"], offer["quantity"]), ("Пилешко филе", 3.99, 5.1, "1 кг"))
check("lidl: own dates", (offer["valid_from"], offer["valid_to"]), ("2026-10-02", "2026-10-04"))
check("lidl: meat", offer["category"], "meat")
check("lidl: page without a name is skipped", lidl.parse_product("<div></div>", TODAY, url="x", image=None, category=None), None)

# --- Billa ----------------------------------------------------------------------
front = """<div class="buttons">
<div class="button"><a href="https://ssbbilla.site/catalog/sedmichna-broshura"><div class="buttonText">Седмична брошура</div></a></div>
<div class="button"><a href="https://ssbbilla.site/catalog/billa-card"><div class="buttonText">Billa Card оферти</div></a></div>
<div class="button"><a href="https://ssbbilla.site/filiali"><div class="buttonText">Филиали</div></a></div></div>"""
check("billa: categories, not card offers or shops", billa.parse_category_links(front), ["https://ssbbilla.site/catalog/sedmichna-broshura"])
catalog = """<title>Седмична брошура</title><div class="dateSpan">Валидност: 01.10.2026 - 07.10.2026</div>
<div class="productSection">
 <div class="product"><div class="actualProduct">Супер цена! Боб зрял 1 кг</div><span class="price">3.49</span><span class="price">2.49</span></div>
 <div class="product"><div class="actualProduct">Сирене краве 400 г</div>
   <span class="price">9.76</span><span class="price">4.99</span><span class="price">7.80</span><span class="price">3.99</span></div>
 <div class="product"><div class="actualProduct">Кафе с BILLA Card</div><span class="price">5.00</span><span class="price">3.00</span></div>
 <div class="product"><div class="actualProduct">Без цена</div><span class="price">-</span></div>
</div>"""
found = billa.parse_offers(catalog, TODAY)
check("billa: card-only and priceless left out", len(found), 2)
beans = found[0]
check("billa: noise removed, size split", (beans["name"], beans["quantity"]), ("Боб зрял", "1 кг"))
check("billa: two prices are old and new", (beans["price"], beans["old_price"]), (2.49, 3.49))
check("billa: page dates", (beans["valid_from"], beans["valid_to"]), ("2026-10-01", "2026-10-07"))
check("billa: four prices, the euro pair", (found[1]["price"], found[1]["old_price"]), (3.99, 4.99))
check("billa: legumes", beans["category"], "legumes")
moved_dates = catalog.replace('<div class="dateSpan">Валидност: 01.10.2026 - 07.10.2026</div>', '<p>Промоции 01.10. – 07.10.2026 г.</p>')
check("billa: dates found without the date element", {(o["valid_from"], o["valid_to"]) for o in billa.parse_offers(moved_dates, TODAY)}, {("2026-10-01", "2026-10-07")})

# Billa's weekly brochure page has no dates; its offers take the week the others show.
undated = [{"valid_from": None, "valid_to": None}, {"valid_from": "2026-10-01", "valid_to": "2026-10-07"},
           {"valid_from": "2026-10-01", "valid_to": "2026-10-07"}, {"valid_from": "2026-10-03", "valid_to": "2026-10-04"}]
check("billa: undated offers take the common week", billa.fill_dates(undated)[0], {"valid_from": "2026-10-01", "valid_to": "2026-10-07"})
check("billa: dated offers keep their own", billa.fill_dates(undated)[3]["valid_to"], "2026-10-04")
check("billa: nothing to take from, nothing changes", billa.fill_dates([{"valid_from": None, "valid_to": None}]), [{"valid_from": None, "valid_to": None}])

# --- Asking for the whole page -----------------------------------------------------
from mealie_planner.sources import common


class _Content:
    """Like aiohttp's: the body arrives in pieces, and read(n) returns only the first."""

    def __init__(self, body, piece=8 * 1024):
        self._pieces = [body[i:i + piece] for i in range(0, len(body), piece)] or [b""]

    async def read(self, n):
        return self._pieces[0][:n]

    async def iter_chunked(self, n):
        for piece in self._pieces:
            yield piece


class _Response:
    def __init__(self, text, status=200):
        self.status = status
        self.charset = "utf-8"
        self.content = _Content(text.encode())
        self.content_type = "text/html"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class Site:
    """Serves the whole page only to one way of asking, and a light page to the rest."""

    def __init__(self, full, light, serves_full):
        self.full, self.light, self.serves_full = full, light, serves_full
        self.asked = []

    def get(self, url, headers=None):
        agent = (headers or {}).get("User-Agent", "")
        profile = "browser" if "Chrome" in agent else "app" if "MealiePlanner" in agent else "plain"
        self.asked.append(profile)
        return _Response(self.full if profile == self.serves_full else self.light)


LIGHT = "<html><title>Всички оферти | Kaufland</title><link href='OfferTemplate-vue.css'></html>"


async def profiles():
    common.PREFERRED.clear()
    site = Site(KAUFLAND_PAGE, LIGHT, "plain")
    found = await kaufland.fetch(site, TODAY)
    check("profiles: the plain client gets the whole page first", (len(found), site.asked), (3, ["plain"]))

    common.PREFERRED.clear()
    site = Site(KAUFLAND_PAGE, LIGHT, "browser")
    found = await kaufland.fetch(site, TODAY)
    check("profiles: tried in turn until the page has the data", (len(found), site.asked), (3, ["plain", "app", "browser"]))
    check("profiles: what worked is remembered", common.PREFERRED["www.kaufland.bg"], "browser")
    site.asked.clear()
    await kaufland.fetch(site, TODAY)
    check("profiles: and asked first next time", site.asked, ["browser"])

    common.PREFERRED.clear()
    site = Site(KAUFLAND_PAGE, LIGHT, "nobody")
    try:
        await kaufland.fetch(site, TODAY)
        check("profiles: with none working, the parser still reports", False, True)
    except SourceError as exc:
        check("profiles: with none working, the parser still reports", ("no offer data" in str(exc), len(site.asked)), (True, 3))

    # A page larger than one piece is read to its end: the offers come late in it.
    common.PREFERRED.clear()
    padded = "<html>" + "<!-- -->" * 20000 + KAUFLAND_PAGE
    found = await kaufland.fetch(Site(padded, LIGHT, "plain"), TODAY)
    check("whole page: offers far past the first piece are found", (len(padded) > 100_000, len(found)), (True, 3))
    try:
        await common.fetch_text(Site(padded, LIGHT, "plain"), kaufland.URL, limit=50_000)
        check("whole page: a page over the limit is refused", False, True)
    except SourceError as exc:
        check("whole page: a page over the limit is refused", "too large" in str(exc), True)
    data, _ = await common.fetch_bytes(Site(padded, LIGHT, "plain"), "https://x/brochure.pdf")
    check("whole file: a brochure file arrives whole", len(data), len(padded.encode()))

    each = await common.fetch_each_profile(Site(KAUFLAND_PAGE, LIGHT, "app"), kaufland.URL)
    check("profiles: the source check asks every way", [(name, kaufland.is_full_page(html)) for name, html, _ in each],
          [("plain", False), ("app", True), ("browser", False)])
    common.PREFERRED.clear()


import asyncio  # noqa: E402

asyncio.run(profiles())
check("kaufland: the light page is not the whole page", kaufland.is_full_page(LIGHT), False)
check("billa: an offer page is recognised", (billa.is_offer_page(catalog), billa.is_offer_page("<html></html>")), (True, False))

# --- Lidl: dates from the page or its link, when the product has none ---------------
class Pages:
    """A site of several pages, each read whole."""

    def __init__(self, pages):
        self.pages = pages

    def get(self, url, headers=None):
        return _Response(self.pages.get(url, "<html></html>"))


LIDL_FRONT = """<html><a href="/c/sedmichni-predlozheniya/a100">Седмични предложения 28.09. - 04.10.</a>
<a href="/c/lidl-plus/s10021179">Lidl Plus</a><a href="/c/kontakti/s1">Контакти</a></html>"""
LIDL_WEEK = """<title>Седмични предложения</title><div data-selector="PRODUCT" canonicalurl="/p/krusi/p1"></div>"""
LIDL_PLUS = """<title>Lidl Plus</title><p>Валидно 29.09. - 01.10.</p><div data-selector="PRODUCT" canonicalurl="/p/krenvirsi/p2"></div>"""
PEARS = """<h1 class="heading__title">Круши</h1><div class="ods-price__value">1,89 €</div><div class="ods-price__footer">за kg</div>"""
SAUSAGES = """<h1 class="heading__title">Кренвирши</h1><div class="ods-price__value">1,15 €</div>"""

check("lidl: offer pages found by the dates in their links", lidl.parse_offer_pages(LIDL_FRONT, TODAY), {
    "https://www.lidl.bg/c/sedmichni-predlozheniya/a100": [date(2026, 9, 28), date(2026, 10, 4)],
    "https://www.lidl.bg/c/lidl-plus/s10021179": [],
})


async def lidl_dates():
    common.PREFERRED.clear()
    site = Pages({
        "https://www.lidl.bg": LIDL_FRONT,
        "https://www.lidl.bg/c/sedmichni-predlozheniya/a100": LIDL_WEEK,
        "https://www.lidl.bg/c/lidl-plus/s10021179": LIDL_PLUS,
        "https://www.lidl.bg/p/krusi/p1": PEARS,
        "https://www.lidl.bg/p/krenvirsi/p2": SAUSAGES,
    })
    found = {o["name"]: o for o in await lidl.fetch(site, TODAY)}
    check("lidl: a product takes its link's dates", (found["Круши"]["valid_from"], found["Круши"]["valid_to"]), ("2026-09-28", "2026-10-04"))
    check("lidl: or its own page's", (found["Кренвирши"]["valid_from"], found["Кренвирши"]["valid_to"]), ("2026-09-29", "2026-10-01"))
    check("lidl: loose fruit has a price per kg", (found["Круши"]["unit_price"], found["Круши"]["unit_base"]), (1.89, "kg"))
    known = {"https://www.lidl.bg/p/krusi/p1": {**found["Круши"], "valid_from": None, "valid_to": None}}
    again = {o["name"]: o for o in await lidl.fetch(site, TODAY, known)}
    check("lidl: a product known without dates gets them too", again["Круши"]["valid_to"], "2026-10-04")
    common.PREFERRED.clear()


asyncio.run(lidl_dates())

# Lidl's real front page (Sept 2026): the dates are on the brochure links
# ("/l/bg/broshura/…"), a four-week one next to this week's; menu links and
# Lidl Plus carry none, and the dates also sit in the page's script data.
REAL_FRONT = """<nav><a href="/c/hrani-i-napitki/s10068374">Храни и напитки</a></nav>
<a href="https://www.lidl.bg/l/bg/broshura/28-09-25-10/ar/0" class="flyer" data-track-name="от 28.09. до 25.10.">
  <div class="flyer__name"> от 28.09. до 25.10. </div><span class="flyer__title">Кошница с грижа</span></a>
<a href="https://www.lidl.bg/l/bg/broshura/28-09-04-10/ar/0" class="flyer" data-track-name="от 28.09. до 04.10.">
  <div class="flyer__name"> от 28.09. до 04.10. </div><span class="flyer__title">Седмични предложения</span></a>
<a href="/c/lidl-plus/s10021179">Lidl Plus</a><script>{"period":"28.09. - 04.10."}</script>"""
PLUS_PAGE = """<title>Lidl Plus</title><div data-selector="PRODUCT" canonicalurl="/p/krenvirsi/p2"></div>"""
check("lidl: brochure and menu links are not offer pages", lidl.parse_offer_pages(REAL_FRONT, TODAY),
      {"https://www.lidl.bg/c/lidl-plus/s10021179": []})


async def lidl_real_front():
    common.PREFERRED.clear()
    site = Pages({
        "https://www.lidl.bg": REAL_FRONT,
        "https://www.lidl.bg/c/lidl-plus/s10021179": PLUS_PAGE,
        "https://www.lidl.bg/p/krenvirsi/p2": SAUSAGES,
    })
    found = {o["name"]: o for o in await lidl.fetch(site, TODAY)}
    check("lidl: only the Lidl Plus products", sorted(found), ["Кренвирши"])
    check("lidl: they take this week, not the four-week brochure's dates",
          (found["Кренвирши"]["valid_from"], found["Кренвирши"]["valid_to"]), ("2026-09-28", "2026-10-04"))
    common.PREFERRED.clear()


asyncio.run(lidl_real_front())

check("brochure: viewers inside frames are looked into", brochures.embedded_pages(
    '<iframe src="https://viewer.example/billa/week"></iframe><iframe src="https://www.google.com/recaptcha/x"></iframe>'
    '<iframe data-src="/embed/brochure"></iframe>', "https://www.billa.bg/promocii"),
    ["https://viewer.example/billa/week", "https://www.billa.bg/embed/brochure"])

# Which brochures AI reads: Lidl's weekly one, not the months-long others.
LIDL_BROCHURES = [{"title": "Кошница с грижа"}, {"title": "Заслужава си"}, {"title": "Седмични предложения"}]
check("brochure: only the titled one is read", brochures.titled(LIDL_BROCHURES, "Седмични предложения"), [{"title": "Седмични предложения"}])
check("brochure: part of the title, any case", len(brochures.titled(LIDL_BROCHURES, "седмични")), 1)
check("brochure: * reads them all", len(brochures.titled(LIDL_BROCHURES, "*")), 3)
check("brochure: no title reads them all", len(brochures.titled(LIDL_BROCHURES, "")), 3)

# --- Brochures ------------------------------------------------------------------
links = brochures.find_links(
    """<a href="/l/bg/broshura/ot-29-09-do-05-10/view/flyer/page/1">Брошура</a>
    <a href="https://view.publitas.com/billa-bulgaria/broshura-01-10/">Billa</a>
    <a href="https://example.com/files/weekly.pdf">PDF</a>""",
    "https://www.lidl.bg/c/broshura/s10020060",
)
check("brochure: leaflet id", links["schwarz"], ["ot-29-09-do-05-10"])
check("brochure: publitas", links["publitas"], ["https://view.publitas.com/billa-bulgaria/broshura-01-10"])
check("brochure: pdf", links["pdf"], ["https://example.com/files/weekly.pdf"])
flyer = {"flyer": {"title": "Брошура", "offerStartDate": "2026-09-29", "offerEndDate": "2026-10-05",
                   "pdfUrl": "https://x/b.pdf", "pages": [{"image": "https://x/1.jpg", "zoom": "https://x/1z.jpg"}, {"image": "https://x/2.jpg"}]}}
brochure = brochures.parse_schwarz("lidl", "ot-29-09-do-05-10", flyer, TODAY)
check("brochure: pages, largest first", brochure["pages"], ["https://x/1z.jpg", "https://x/2.jpg"])
check("brochure: dates", (brochure["valid_from"], brochure["valid_to"]), ("2026-09-29", "2026-10-05"))
check("brochure: same id every time", brochure["id"], brochures.parse_schwarz("lidl", "ot-29-09-do-05-10", flyer, TODAY)["id"])
check("brochure: dates from the title", brochures.pdf_brochure("billa", "https://x/broshura-01.10-07.10.2026.pdf", TODAY)["valid_to"], "2026-10-07")

done()
