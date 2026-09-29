<img src="docs/icon.png" alt="Mealie Planner" width="96" align="right">

# Mealie Planner

Plan next week's meals in Mealie from your own rules and what is on sale at
**Lidl, Kaufland and Billa**. Then choose which of the week's products go on
your shopping list, each with the shop it is on sale in.

This is a HACS custom integration with its own sidebar panel. It does not
change Mealie's UI or database: it reads your recipes, and it writes to
Mealie's meal planner only when you press **Save to Mealie**.

## What it does

1. **You set rules for the week**, for example:
   - *Required:* 1 to 2 fish recipes, 1 recipe with legumes.
   - *Preferred:* 1 soup, 1 recipe without meat.
2. **It reads the shops' offers.** The offers come from the shops' websites for
   free, and optionally from their printed brochures, which AI reads **once per
   brochure**. Offers are kept until each one ends, so browsing them never
   costs another AI call.
3. **It fills the week.** The rules come first. Then, among the recipes that
   fit the rules, the ones with more ingredients on sale win. It never goes
   over a rule's maximum, and it avoids recipes you cooked in the last few
   weeks. The week is planned either locally or by AI; either way, the result
   is checked against the rules.
4. **You adjust it.** You can change, remove, lock or swap any meal, before or
   after saving. The week's products are recalculated after every change.
5. **You pick the products.** The week's ingredients are grouped by the shop
   where they are cheapest that week. A product on no offer goes under the
   shop HomeBasket Lists keeps it under, if there is one, and otherwise under
   "no shop". Open one to
   switch to a similar product from any of the three shops. Nothing is added
   to a list until you tick products and press **Add to list**.

## The parts

Each part is installed separately; **Needs** says what it cannot work without. Mealie is the recipe manager, not one of these parts.

| | What it is | Needs |
| --- | --- | --- |
| **[HomeBasket](https://github.com/ivan1mihaylov/HomeBasket)** | Scanning, and the products it learns: names, barcodes, pictures, everything the databases know. | Nothing else. Puts scans on a HomeBasket Lists list when that is installed, otherwise on a to-do list. |
| **[HomeBasket Card](https://github.com/ivan1mihaylov/HomeBasket-Card)** | Scanning with a phone, for when there is no scanner on a shelf — and the place to look after the products themselves. | **HomeBasket** (required). |
| **[HomeBasket Lists](https://github.com/ivan1mihaylov/HomeBasket-Lists)** | Shopping lists and tasks, using what HomeBasket knows. | Nothing else. HomeBasket is optional: with it, items get products and pictures, and a list can scan. |
| **[Mealie Discover](https://github.com/ivan1mihaylov/Mealie-Discover)** | Finds recipes on the web and adds them to Mealie. | **Mealie** (required), and at least one of SearXNG, a YouTube key or Social to Mealie. |
| **Mealie Planner** | This: plans the week in Mealie from your rules and the Lidl, Kaufland and Billa offers, and lists the week's products by shop. | **Mealie** (required). HomeBasket Lists is optional, for putting the products on a list; AI is optional. |

Mealie Planner uses HomeBasket Lists through the public interface HomeBasket
already uses (`hass.data["homebasket_lists_api"]`). HomeBasket Lists is
optional: without it, planning and offers still work, and only the **Add to
list** buttons are disabled.

## Install from HACS

1. HACS → three-dot menu → **Custom repositories** → add
   `https://github.com/ivan1mihaylov/Mealie-Planner` as **Integration**.
2. Install Mealie Planner, then restart Home Assistant.
3. Settings → Devices & services → Add integration → **Mealie Planner**.
4. Enter the Mealie URL and a Mealie API token. On Home Assistant OS, a running
   Mealie add-on is detected and its URL filled in.
5. Optionally, enter the AI settings (see below).
6. Open **Mealie Planner** from the sidebar.

To change the connection later: Settings → Devices & services → Mealie
Planner → three-dot menu → **Reconfigure**.

### Mealie

Create a long-lived API token in Mealie under your profile → API Tokens. Enter
a URL reachable **from Home Assistant Core**, for example
`http://<mealie-host>:9000`. Recipe links and pictures in the panel use the
same URL, so a URL your browser can also reach works best.

### AI (optional)

Mealie keeps its OpenAI key to itself, so Mealie Planner has its own. Use the
same kind of settings Mealie uses:

| Field | OpenAI | Ollama or another OpenAI-compatible service |
| --- | --- | --- |
| AI base URL | `https://api.openai.com/v1` (default) | e.g. `http://<host>:11434/v1` |
| AI API key | your key | whatever the service wants, often empty |
| AI model | `gpt-6-luna` (default), or another model that reads images | a vision model, e.g. `llava` or `qwen2.5vl` |

The key is checked with a tiny request before it is saved. It stays in Home
Assistant's config entry and is never sent to the browser.

**Which model:** `gpt-6-luna` is the default. It is OpenAI's smallest GPT-6
model, reads images, and costs $0.10 per million tokens in and $0.50 out, which
is less than `gpt-4o-mini`. An install set up with `gpt-4o-mini` keeps it; to
switch, open **Reconfigure** and enter `gpt-6-luna`.

**Reasoning effort** (in the options) sets how long a reasoning model such as
Luna thinks before answering. *Low*, the default, is enough to read prices off
a page. Higher settings cost more and are slower. *The service's default*
sends no setting, for services that have none.

The integration adapts to what each service accepts. It learns from the
service's first refusal whether to use `max_completion_tokens` (current OpenAI
models) or `max_tokens` (Ollama and older servers), and whether to send a
temperature, a reasoning effort or a JSON schema, then keeps sending what
works.

**What AI is used for, and what it costs:**

- **Brochures:** each brochure is read once, 4 pages per request. The number of
  pages read is capped by the options (default 40). The Offers tab shows the
  tokens spent per brochure and in total.
- **Offers the keyword table cannot place:** only their names are sent, 80 per
  request, once per offer.
- **Planning in AI mode:** one request per "Plan the week", with a short table
  of candidate recipes rather than whole recipes.

Without AI, offers come from the websites only and the week is planned
locally.

## Options

Settings → Devices & services → Mealie Planner → **Configure**:

- **Plan the week:** locally, or with AI.
- **Websites:** which shops' websites to read offers from.
- **Brochures:** which shops' printed brochures AI reads.
- **Zone of Lidl / Kaufland / Billa:** HomeBasket Lists identifies shops by
  their `zone.*` entities. Zones named after a shop are suggested
  automatically. A product on sale in a shop without a zone goes to the list
  with no shop, and its note names the shop.
- **HomeBasket Lists list:** which list products go to, when there is more
  than one.
- **The week starts on:** Monday by default.
- **Most brochure pages read by AI:** the cost cap. The default is 80, since
  Lidl's weekly brochure has about 70 pages.
- **Brochure of each shop to read:** text from the title of the brochures AI
  reads. For Lidl it is "Седмични предложения", its weekly brochure, rather
  than the ones that run for months. `*` reads all of a shop's brochures.
- **Brochure page of each shop:** where brochures are looked for, if a shop
  moves them.

Rules, which meals to plan each day (breakfast, lunch, dinner, side…), and how
many weeks back to avoid repeating recipes are set in the panel under
**Settings**. Only administrators can change them.

## Rules

A rule has:

- a name;
- whether it is **required** or **preferred**;
- a minimum and an optional maximum per week;
- either **contains** or **does not contain**, followed by what it looks for:
  - Mealie **tags** and **categories**;
  - **foods**, matched against each ingredient and the recipe's name.
    Bulgarian word endings are handled, so "домати" finds "домат".

**Ready-made rules** adds the four from the example, in Bulgarian:
- *Риба:* 1–2, required.
- *Бобови:* at least 1, required.
- *Супа:* 1, preferred.
- *Без месо:* 1, preferred. It excludes fish too; remove the fish from its list
  to allow fish.

Order matters: required rules are filled first, in the order they are listed.
The panel shows each rule as met (✓), not met (!) or "if possible" (…), and
warns when an edit breaks a rule. The edit is still allowed, because the week
is yours.

## Where offers come from

| Shop | Website (free) | Brochure (AI, once) |
| --- | --- | --- |
| Kaufland | kaufland.bg "Актуални предложения": every category in one page load, each offer with its own dates | Kaufland's leaflet viewer |
| Lidl | the offer pages linked from lidl.bg, then each product's page, with its own dates | Lidl's leaflet viewer |
| Billa | ssbbilla.site, Billa's plain offers site, with the week's dates | the weekly brochure on billa.bg |

- **Brochure offers have pictures.** AI also says where each product's picture
  is on its brochure page; that part of the page is cut out and kept in
  `/config/mealie_planner/pictures/`, and deleted when the offer ends. Offers
  without such a box show their whole page.
- **Each offer carries its own validity.** One brochure can mix
  week-long offers with "Friday and Saturday only" ones. Offers leave when
  their own date passes.
- **Planning only counts offers valid in the planned week.** The products
  show each offer's dates.
- **The shops are checked** 2 minutes after Home Assistant starts and every
  morning at 06:07. You can also press **Check for new** on the Offers tab.
  Only brochures not read before are sent to AI.
- **Add brochure** takes the URL of a PDF, an image or a page that links to a
  brochure, and reads it the same way.
- **Check the sources** on the Offers tab shows what each source finds right
  now, without keeping anything or spending AI. Use it when a shop changes its
  website. When a source fails, gives offers without dates or finds no
  brochures, it asks for the page in every way it knows and shows what each
  got. It also saves each answer in `/config/mealie_planner_debug/`. Send
  those files in an issue so the parser can be fixed.
- **How pages are asked for.** A page is read to its end; Kaufland's is over
  2 MB. It is asked for as a plain client first. If the page lacks what its
  parser needs, it is asked for again under an honest name (`MealiePlanner`)
  and then with a browser's headers, for sites that answer differently by
  client. The way that worked is remembered per site.

## Products and the shopping list

- The products are the ingredients of the planned recipes, added up by food
  and unit. Water is left out.
- Each product is matched against the offers valid that week, by the generic
  food ("сьомга") and by the product name. The lowest price per kg or litre
  wins.
- A product on no offer takes the shop HomeBasket Lists keeps it under. This
  is for things only one shop sells: put them under that shop on a list once,
  and they are filed there from then on.
  - Items on any list count, bought ones included. The same name comes first,
    then an item whose name contains the ingredient's words, and the most
    recently changed item wins.
  - A shop that is not Lidl, Kaufland or Billa, such as a market or a
    greengrocer's zone, gets a group of its own.
  - When the lists know no shop for the product, it is added without one, and
    HomeBasket Lists fills one in from what HomeBasket knows of the product,
    as it does for anything added without a shop.
  - Choosing **No shop** on a product by hand always leaves it without one.
- Tapping a product shows:
  - its offer: price, old price, price per kg, dates, conditions and brochure
    page;
  - **similar products**: the same food, then similar names, then the same
    kind (other fish).

  Choose one to change the offer and the shop, or choose **No shop**.
- Your choices and ticks are kept while the week still needs that product.
- **Add to list** adds each ticked product to HomeBasket Lists, with:
  - the quantity and unit;
  - the zone of its shop: the offer's, else the one the lists keep it under,
    else none;
  - a note such as `Lidl · 3,49 € (−30%) до 05.10 · Сьомга на фурна`.

## Languages

Bulgarian and English: the panel follows Home Assistant's language, and the
setup and options are translated.

## Limitations

- **The shops' websites change.** The parsers follow the pages as they are
  today. If a shop shows "Error" or 0 offers on the Offers tab, run **Check
  the sources**, or `tools/probe.py`, and open an issue with its output.
- **Brochure reading depends on the AI model.** Small local models miss or
  misread prices more often than `gpt-6-luna` and larger models. PDFs are
  sent as files, which OpenAI accepts; other providers may need brochures
  with page images.
- **Matching is word-based.** "мляко" also matches "кисело мляко" offers; the
  similar-products list is there to correct it.
- **Tested with sample pages and fake AI answers.** Live runs need your Mealie
  instance and network access to the shops.

## Development

The tests need nothing installed; they stand in for Home Assistant:

```
for t in tests/test_*.py; do python3 "$t" || break; done
```

`tools/probe.py` runs the shop sources against the live sites (needs
`pip install aiohttp`).

## Releases

`manifest.json` carries the version. Update it, then run **Actions → Release**
with the matching version. The workflow creates a `vX.Y.Z` GitHub Release for
HACS. **Validate** runs HACS, hassfest, syntax checks and the tests on every
push and pull request.

## License

MIT. See [LICENSE](LICENSE).
