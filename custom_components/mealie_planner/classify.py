"""Tell what an offer is from its name, without AI.

Each entry maps word beginnings to a generic food and a category. The first
entry that matches wins, so the more specific ones come first ("риба тон"
before "риба", "кисело мляко" before "мляко").
"""

from __future__ import annotations

from .text import normalize

# (words that must all start a word of the name, food, category)
_TABLE: list[tuple[tuple[str, ...], str, str]] = [
    # Fish and seafood
    (("риба", "тон$"), "риба тон", "fish"),
    (("тон$",), "риба тон", "fish"),
    (("сьомг",), "сьомга", "fish"),
    (("скумри",), "скумрия", "fish"),
    (("пъстърв",), "пъстърва", "fish"),
    (("ципур",), "ципура", "fish"),
    (("лаврак",), "лаврак", "fish"),
    (("хек$",), "хек", "fish"),
    (("треск",), "треска", "fish"),
    (("пангасиус",), "пангасиус", "fish"),
    (("херинг",), "херинга", "fish"),
    (("сардин",), "сардини", "fish"),
    (("цаца",), "цаца", "fish"),
    (("шаран",), "шаран", "fish"),
    (("аншоа",), "аншоа", "fish"),
    (("минтай",), "минтай", "fish"),
    (("хайвер",), "хайвер", "fish"),
    (("скарид",), "скариди", "fish"),
    (("калмар",), "калмари", "fish"),
    (("миди",), "миди", "fish"),
    (("октопод",), "октопод", "fish"),
    (("риба",), "риба", "fish"),
    (("рибн",), "риба", "fish"),
    (("рибе",), "риба", "fish"),
    # Legumes
    (("зрял", "боб"), "боб", "legumes"),
    (("боб$",), "боб", "legumes"),
    (("фасул",), "боб", "legumes"),
    (("леща",), "леща", "legumes"),
    (("нахут",), "нахут", "legumes"),
    (("зелен", "фасул"), "зелен фасул", "vegetables"),
    (("грах$",), "грах", "legumes"),
    (("соя$",), "соя", "legumes"),
    # Meat
    (("кайма",), "кайма", "meat"),
    (("пилешк", "гърд"), "пилешко филе", "meat"),
    (("пилешк", "филе"), "пилешко филе", "meat"),
    (("пилешк",), "пилешко месо", "meat"),
    (("пиле",), "пиле", "meat"),
    (("пуешк",), "пуешко месо", "meat"),
    (("свинск",), "свинско месо", "meat"),
    (("телешк",), "телешко месо", "meat"),
    (("говежд",), "телешко месо", "meat"),
    (("агнешк",), "агнешко месо", "meat"),
    (("кренвирш",), "кренвирши", "meat"),
    (("надениц",), "наденица", "meat"),
    (("кебапч",), "кебапчета", "meat"),
    (("кюфте",), "кюфтета", "meat"),
    (("шунк",), "шунка", "meat"),
    (("салам",), "салам", "meat"),
    (("бекон",), "бекон", "meat"),
    (("луканк",), "луканка", "meat"),
    (("суджук",), "суджук", "meat"),
    (("пастърм",), "пастърма", "meat"),
    (("карначе",), "карначе", "meat"),
    (("дроб",), "дроб", "meat"),
    # Dairy and eggs
    (("кисело", "мляко"), "кисело мляко", "dairy"),
    (("прясно", "мляко"), "прясно мляко", "dairy"),
    (("мляко",), "мляко", "dairy"),
    (("кашкавал",), "кашкавал", "dairy"),
    (("сирене",), "сирене", "dairy"),
    (("извара",), "извара", "dairy"),
    (("моцарел",), "моцарела", "dairy"),
    (("пармезан",), "пармезан", "dairy"),
    (("крема", "сирене"), "крема сирене", "dairy"),
    (("сметана",), "сметана", "dairy"),
    (("готварска", "сметана"), "сметана", "dairy"),
    (("масло$",), "масло", "dairy"),
    (("йогурт",), "йогурт", "dairy"),
    (("айрян",), "айрян", "dairy"),
    (("яйц",), "яйца", "dairy"),
    # Vegetables
    (("картоф",), "картофи", "vegetables"),
    (("домат",), "домати", "vegetables"),
    (("краставиц",), "краставици", "vegetables"),
    (("зелен", "лук$"), "зелен лук", "vegetables"),
    (("лук$",), "лук", "vegetables"),
    (("чесън",), "чесън", "vegetables"),
    (("морков",), "моркови", "vegetables"),
    (("зеле$",), "зеле", "vegetables"),
    (("чушк",), "чушки", "vegetables"),
    (("черен", "пипер"), "черен пипер", "pantry"),
    (("пипер",), "чушки", "vegetables"),
    (("тиквичк",), "тиквички", "vegetables"),
    (("тиква",), "тиква", "vegetables"),
    (("патладжан",), "патладжан", "vegetables"),
    (("спанак",), "спанак", "vegetables"),
    (("марул",), "маруля", "vegetables"),
    (("салата", "айсберг"), "маруля", "vegetables"),
    (("броколи",), "броколи", "vegetables"),
    (("карфиол",), "карфиол", "vegetables"),
    (("гъби",), "гъби", "vegetables"),
    (("печурк",), "гъби", "vegetables"),
    (("праз",), "праз", "vegetables"),
    (("целина",), "целина", "vegetables"),
    (("цвекло",), "цвекло", "vegetables"),
    (("копър",), "копър", "vegetables"),
    (("магданоз",), "магданоз", "vegetables"),
    (("царевиц",), "царевица", "vegetables"),
    (("авокадо",), "авокадо", "vegetables"),
    # Fruit
    (("ябълк",), "ябълки", "fruit"),
    (("банан",), "банани", "fruit"),
    (("портокал",), "портокали", "fruit"),
    (("мандарин",), "мандарини", "fruit"),
    (("лимон",), "лимони", "fruit"),
    (("грейпфрут",), "грейпфрут", "fruit"),
    (("грозде",), "грозде", "fruit"),
    (("круш",), "круши", "fruit"),
    (("праскови",), "праскови", "fruit"),
    (("ягоди",), "ягоди", "fruit"),
    (("киви",), "киви", "fruit"),
    (("диня",), "диня", "fruit"),
    (("пъпеш",), "пъпеш", "fruit"),
    (("сливи",), "сливи", "fruit"),
    (("боровинк",), "боровинки", "fruit"),
    # Bakery
    (("хляб",), "хляб", "bakery"),
    (("питк",), "питка", "bakery"),
    (("франзел",), "франзела", "bakery"),
    (("кифл",), "кифла", "bakery"),
    (("кроасан",), "кроасан", "bakery"),
    (("баниц",), "баница", "bakery"),
    (("тесто",), "тесто", "bakery"),
    (("кори", "баница"), "кори за баница", "bakery"),
    # Pantry
    (("брашно",), "брашно", "pantry"),
    (("ориз",), "ориз", "pantry"),
    (("булгур",), "булгур", "pantry"),
    (("спагети",), "паста", "pantry"),
    (("макарон",), "паста", "pantry"),
    (("паста$",), "паста", "pantry"),
    (("фиде",), "фиде", "pantry"),
    (("захар",), "захар", "pantry"),
    (("олио",), "олио", "pantry"),
    (("зехтин",), "зехтин", "pantry"),
    (("оцет",), "оцет", "pantry"),
    (("сол$",), "сол", "pantry"),
    (("доматено", "пюре"), "доматено пюре", "pantry"),
    (("лютениц",), "лютеница", "pantry"),
    (("кетчуп",), "кетчуп", "pantry"),
    (("майонез",), "майонеза", "pantry"),
    (("горчиц",), "горчица", "pantry"),
    (("овесен",), "овесени ядки", "pantry"),
    (("мюсли",), "мюсли", "pantry"),
    (("мед$",), "мед", "pantry"),
    (("подправк",), "подправки", "pantry"),
    (("консерв",), "консерви", "pantry"),
    # Drinks
    (("бира$",), "бира", "drinks"),
    (("вино$",), "вино", "drinks"),
    (("минерална", "вода"), "вода", "drinks"),
    (("вода",), "вода", "drinks"),
    (("сок$",), "сок", "drinks"),
    (("нектар",), "сок", "drinks"),
    (("кафе",), "кафе", "drinks"),
    (("чай$",), "чай", "drinks"),
    (("ракия",), "ракия", "drinks"),
    (("уиски",), "уиски", "drinks"),
    (("водка",), "водка", "drinks"),
    (("газирана",), "газирана напитка", "drinks"),
    (("тоник",), "тоник", "drinks"),
    (("напитк",), "напитка", "drinks"),
    # Sweets and snacks count as other food
    (("шоколад",), "шоколад", "other_food"),
    (("бисквит",), "бисквити", "other_food"),
    (("вафл",), "вафли", "other_food"),
    (("сладолед",), "сладолед", "frozen"),
    (("чипс",), "чипс", "other_food"),
    (("ядки",), "ядки", "other_food"),
    (("орехи",), "орехи", "other_food"),
    (("бонбон",), "бонбони", "other_food"),
    (("торта$",), "торта", "other_food"),
    (("кекс$",), "кекс", "other_food"),
    (("пица$",), "пица", "frozen"),
    (("замразен",), "", "frozen"),
    # Not food
    (("препарат",), "", "non_food"),
    (("перилн",), "", "non_food"),
    (("омекотител",), "", "non_food"),
    (("шампоан",), "", "non_food"),
    (("душ", "гел"), "", "non_food"),
    (("паста", "зъби"), "", "non_food"),
    (("четка",), "", "non_food"),
    (("тоалетн", "хартия"), "", "non_food"),
    (("салфетк",), "", "non_food"),
    (("кърпи",), "", "non_food"),
    (("пелени",), "", "non_food"),
    (("почиств",), "", "non_food"),
    (("дезодорант",), "", "non_food"),
    (("крем", "лице"), "", "non_food"),
    (("храна", "котки"), "", "non_food"),
    (("храна", "кучета"), "", "non_food"),
    (("котешк",), "", "non_food"),
    (("кучешк",), "", "non_food"),
    (("тенджер",), "", "non_food"),
    (("тиган",), "", "non_food"),
    (("възглавниц",), "", "non_food"),
    (("чорап",), "", "non_food"),
    (("тениск",), "", "non_food"),
    (("обувк",), "", "non_food"),
    (("бормашин",), "", "non_food"),
    (("инструмент",), "", "non_food"),
    (("играчк",), "", "non_food"),
    (("лампа",), "", "non_food"),
    (("батери",), "", "non_food"),
]

# The most specific entries are tried first: more words, then longer
# beginnings ("тоник" before "тон"), then the order of the table.
_ORDERED = sorted(_TABLE, key=lambda row: (-len(row[0]), -sum(len(p) for p in row[0])))

# A short word ending in "$" must be the whole word, give or take an ending:
# "лук" is "лук" or "лука", never "лукчета"... nor "зеле" in "зелени".
_ENDINGS = ("", "а", "и", "ът", "та", "то", "ове", "ове", "ят")


def _words(text: str) -> list[str]:
    return normalize(text).split()


def _starts(word: str, prefix: str) -> bool:
    if prefix.endswith("$"):
        stem = prefix[:-1]
        return any(word == stem + ending for ending in _ENDINGS)
    return word.startswith(prefix)


def classify(name: str | None, hint: str | None = None) -> tuple[str | None, str | None]:
    """(food, category) for an offer, or (None, None) when the table cannot tell.

    `hint` is the shop's own category ("Месо и риба"), used only to settle
    what the name leaves open.
    """
    words = _words(name or "")
    for prefixes, food, category in _ORDERED:
        if all(any(_starts(word, prefix) for word in words) for prefix in prefixes):
            if category == "frozen" and not food:
                # "замразен" says how, not what: look for what first.
                rest = classify(" ".join(w for w in words if not w.startswith("замразен")))
                if rest[1] is not None:
                    return rest
            return (food or None), category
    if hint:
        return None, category_from_hint(hint)
    return None, None


_HINTS = [
    (("риба",), "fish"),
    (("месо",), "meat"),
    (("колбас",), "meat"),
    (("плод", "зеленчу"), "vegetables"),
    (("плод",), "fruit"),
    (("зеленчу",), "vegetables"),
    (("млеч",), "dairy"),
    (("сирен",), "dairy"),
    (("хлеб",), "bakery"),
    (("хляб",), "bakery"),
    (("пекар",), "bakery"),
    (("напит",), "drinks"),
    (("алкохол",), "drinks"),
    (("замраз",), "frozen"),
    (("сладк",), "other_food"),
    (("основни",), "pantry"),
    (("бакал",), "pantry"),
    (("хигиен",), "non_food"),
    (("козмет",), "non_food"),
    (("дом",), "non_food"),
    (("нехранит",), "non_food"),
    (("градин",), "non_food"),
    (("животн",), "non_food"),
]


def category_from_hint(hint: str) -> str | None:
    words = _words(hint)
    for prefixes, category in _HINTS:
        if all(any(word.startswith(prefix) for word in words) for prefix in prefixes):
            return category
    return None
