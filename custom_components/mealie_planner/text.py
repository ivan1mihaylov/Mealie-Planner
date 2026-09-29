"""Bulgarian text helpers: matching foods to offers, prices, quantities, dates.

Nothing here talks to Home Assistant, so it can be tested on its own.
"""

from __future__ import annotations

from datetime import date
import re

_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
_SPACES = re.compile(r"\s+")

# Longest first, so "ите" wins over "е". A stem keeps at least three letters.
_SUFFIXES = sorted(
    ("ите", "ата", "ята", "ове", "еве", "ища", "ия", "ът", "ят", "та", "те", "то",
     "ки", "ци", "и", "а", "я", "о", "е", "у"),
    key=len,
    reverse=True,
)

# Words that say nothing about what a product is.
_STOPWORDS = {
    "и", "с", "със", "от", "за", "в", "във", "на", "по", "без", "или", "до", "бр",
    "г", "гр", "кг", "мл", "л", "пакет", "опаковка", "различни", "видове", "вид",
    "избрани", "цена", "пресен", "прясна", "прясно", "пресни", "свеж", "свежа",
    "свежо", "клас", "произход", "българия", "качество", "ниска", "висока",
    "the", "and", "of", "with", "for", "fresh",
}


def normalize(text: str | None) -> str:
    """Lowercase, without punctuation, one space between words."""
    value = str(text or "").lower().replace("ё", "е").replace("ѝ", "и")
    value = _PUNCTUATION.sub(" ", value)
    return _SPACES.sub(" ", value).strip()


def stem(word: str) -> str:
    """A light Bulgarian stemmer: enough to meet "домати" and "домат" halfway."""
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def stems(text: str | None) -> list[str]:
    """The meaningful word stems of a text, in order."""
    found = []
    for word in normalize(text).split():
        if word in _STOPWORDS or word.isdigit() or len(word) < 2:
            continue
        if re.fullmatch(r"\d+([.,]\d+)?[a-zа-я]*", word):
            continue
        found.append(stem(word))
    return found


def _same(one: str, other: str) -> bool:
    if one == other:
        return True
    shorter, longer = sorted((one, other), key=len)
    return len(shorter) >= 4 and longer.startswith(shorter)


def contains(needle: str | None, haystack: str | None) -> bool:
    """Whether every word of `needle` appears in `haystack`.

    "риба тон" is in "Филе от риба тон в олио"; "картофи" is in "Картоф бял".
    """
    return contains_stems(stems(needle), stems(haystack))


def contains_stems(wanted: list[str], have: list[str]) -> bool:
    if not wanted:
        return False
    return all(any(_same(word, other) for other in have) for word in wanted)


def overlap(one: str | None, other: str | None) -> float:
    """Share of the words of the shorter text that are also in the longer one."""
    first, second = stems(one), stems(other)
    if not first or not second:
        return 0.0
    if len(first) > len(second):
        first, second = second, first
    hits = sum(1 for word in first if any(_same(word, item) for item in second))
    return hits / len(first)


# --- Prices -------------------------------------------------------------------
_NUMBER = re.compile(r"(\d+(?:[  ]\d{3})*(?:[.,]\d{1,2})?)")


def parse_price(text) -> float | None:
    """A price from shop text: "2,49", "2.49 €", "1,27 € / 2,49 лв.".

    When both euro and lev amounts are shown, the euro one wins.
    """
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)
    value = str(text)
    euro = re.search(r"(\d+(?:[.,]\d{1,2})?)\s*(?:€|eur|евро)", value, re.IGNORECASE)
    if euro is None:
        euro = re.search(r"(?:€|eur)\s*(\d+(?:[.,]\d{1,2})?)", value, re.IGNORECASE)
    match = euro or _NUMBER.search(value)
    if match is None:
        return None
    number = match.group(1).replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        return round(float(number), 2)
    except ValueError:
        return None


def discount(price: float | None, old_price: float | None) -> int | None:
    if not price or not old_price or old_price <= price:
        return None
    return round((old_price - price) / old_price * 100)


# --- Quantities ---------------------------------------------------------------
_QUANTITY = re.compile(
    r"(?:(\d+)\s*[xх×]\s*)?(\d+(?:[.,]\d+)?)\s*(кг|kg|гр|г|g|мл|ml|л|l|бр|pcs)\b\.?",
    re.IGNORECASE,
)
_BASE = {
    "кг": ("kg", 1.0), "kg": ("kg", 1.0), "гр": ("kg", 0.001), "г": ("kg", 0.001),
    "g": ("kg", 0.001), "мл": ("l", 0.001), "ml": ("l", 0.001), "л": ("l", 1.0),
    "l": ("l", 1.0), "бр": ("pc", 1.0), "pcs": ("pc", 1.0),
}


def parse_quantity(text: str | None) -> tuple[float, str] | None:
    """The amount in a pack as (amount, "kg" | "l" | "pc"): "4 x 125 г" is (0.5, "kg")."""
    if not text:
        return None
    match = _QUANTITY.search(str(text))
    if match is None:
        # "за kg", "цена за кг": a price per kilogram or litre.
        per = re.search(r"(?:^|\bза\s*|/\s*)(1\s*)?(kg|кг|l|л)\b\.?", str(text), re.IGNORECASE)
        if per:
            return (1.0, "kg" if per.group(2).lower() in ("kg", "кг") else "l")
        return None
    count = int(match.group(1)) if match.group(1) else 1
    amount = float(match.group(2).replace(",", "."))
    base, factor = _BASE[match.group(3).lower()]
    total = count * amount * factor
    return (round(total, 4), base) if total > 0 else None


def unit_price(price: float | None, quantity: str | None) -> tuple[float, str] | None:
    """Price per kg, litre or piece."""
    parsed = parse_quantity(quantity)
    if price is None or parsed is None:
        return None
    amount, base = parsed
    return round(price / amount, 2), base


# --- Dates --------------------------------------------------------------------
_DATE = re.compile(r"(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?")


def parse_dates(text: str | None, today: date) -> list[date]:
    """Dates in "от 29.09. до 05.10.2026" style text; a missing year is guessed."""
    found: list[date] = []
    for day, month, year in _DATE.findall(str(text or "")):
        try:
            if year:
                value = int(year) + (2000 if len(year) == 2 else 0)
                found.append(date(value, int(month), int(day)))
                continue
            guess = date(today.year, int(month), int(day))
            # An offer page in late December can speak of early January.
            if (guess - today).days < -180:
                guess = date(today.year + 1, int(month), int(day))
            elif (guess - today).days > 180:
                guess = date(today.year - 1, int(month), int(day))
            found.append(guess)
        except ValueError:
            continue
    # "29.09. - 05.10.2026": the first date borrows the year of the second.
    if len(found) >= 2 and found[0] > found[1] and found[0].year == found[1].year:
        try:
            found[0] = found[0].replace(year=found[1].year - 1)
        except ValueError:
            pass
    return found


_RANGE = re.compile(
    r"(\d{1,2}\.\d{1,2}\.(?:\d{2,4})?)\s*(?:г\.)?\s*(?:-|–|—|до)\s*(\d{1,2}\.\d{1,2}\.(?:\d{2,4})?)"
)


def date_ranges(text: str | None, today: date) -> list[tuple[int, list[date]]]:
    """Every real "28.09. - 04.10." style range in a text, with where it starts."""
    found = []
    for match in _RANGE.finditer(str(text or "")):
        dates = parse_dates(f"{match.group(1)} {match.group(2)}", today)
        if len(dates) == 2 and 0 <= (dates[1] - dates[0]).days <= 62:
            found.append((match.start(), dates))
    return found


def first_range(text: str | None, today: date) -> list[date]:
    """The range a text is about: the one running today, else the next, else the first."""
    ranges = [dates for _, dates in date_ranges(text, today)]
    if not ranges:
        return []
    for dates in ranges:
        if dates[0] <= today <= dates[1]:
            return dates
    upcoming = [dates for dates in ranges if dates[0] > today]
    return min(upcoming) if upcoming else ranges[0]


def iso(value: date | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    text = str(value)[:10]
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None


def overlaps(valid_from: str | None, valid_to: str | None, start: date, end: date) -> bool:
    """Whether an offer's own dates overlap [start, end]; open ends count as open."""
    begin = date.fromisoformat(valid_from) if valid_from else None
    finish = date.fromisoformat(valid_to) if valid_to else None
    if begin is not None and begin > end:
        return False
    if finish is not None and finish < start:
        return False
    return True
