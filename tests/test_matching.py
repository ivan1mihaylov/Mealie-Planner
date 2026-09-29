"""Bulgarian text: matching ingredients to offers, prices, pack sizes and dates.

    python3 tests/test_matching.py
"""

from __future__ import annotations

from datetime import date

import support
from support import check, done

from mealie_planner.classify import classify
from mealie_planner.offers import OfferIndex
from mealie_planner.text import contains, first_range, overlaps, parse_dates, parse_price, parse_quantity, unit_price

TODAY = date(2026, 10, 1)

# Words meet across endings.
check("домати in Домат розов", contains("домати", "Домат розов"), True)
check("картофи in Картоф бял", contains("картофи", "Картоф бял, 2 кг"), True)
check("риба тон in Филе от риба тон", contains("риба тон", "Филе от риба тон в олио"), True)
check("риба тон not in Риба ципура", contains("риба тон", "Риба ципура"), False)
check("лук is not in лукчета", contains("лук", "Лукчета"), False)
check("empty needle matches nothing", contains("", "Домати"), False)

# Prices: the euro amount wins when both are shown.
check("comma decimal", parse_price("2,49"), 2.49)
check("euro sign", parse_price("2.49 €"), 2.49)
check("lev and euro", parse_price("2,49 лв. / 1,27 €"), 1.27)
check("euro first", parse_price("1,27 € 2,49 лв."), 1.27)
check("no number", parse_price("цена"), None)

# Pack sizes and unit prices.
check("grams", parse_quantity("500 г"), (0.5, "kg"))
check("multipack", parse_quantity("4 x 125 г"), (0.5, "kg"))
check("litres", parse_quantity("1,5 л"), (1.5, "l"))
check("pieces", parse_quantity("10 бр."), (10.0, "pc"))
check("unit price per kg", unit_price(2.0, "400 г"), (5.0, "kg"))
check("за kg is one kilogram", parse_quantity("за kg"), (1.0, "kg"))
check("price per kg for loose fruit", unit_price(1.89, "за kg"), (1.89, "kg"))
check("grams in Latin letters", parse_quantity("2 x 90 g/опаковка"), (0.18, "kg"))
check("the range running today wins", first_range("05.10. - 11.10. and 28.09. - 04.10.", TODAY), [date(2026, 9, 28), date(2026, 10, 4)])
check("of several running today, the shortest", first_range("от 28.09. до 25.10. и от 28.09. до 04.10.", TODAY), [date(2026, 9, 28), date(2026, 10, 4)])
check("else the next one", first_range("01.09. - 07.09. then 05.10. - 11.10.", TODAY), [date(2026, 10, 5), date(2026, 10, 11)])
check("first real date range", first_range("3.41.23-3.41.23 и после 28.09. - 04.10.", TODAY), [date(2026, 9, 28), date(2026, 10, 4)])
check("no size, no unit price", unit_price(2.0, "опаковка"), None)

# Dates: a missing year is today's, and the first date borrows the second's.
check("two dates", parse_dates("от 29.09. до 05.10.2026", TODAY), [date(2026, 9, 29), date(2026, 10, 5)])
check("no year", parse_dates("02.10 - 04.10", TODAY), [date(2026, 10, 2), date(2026, 10, 4)])
check("across new year", parse_dates("29.12.2026 - 04.01.2027", TODAY), [date(2026, 12, 29), date(2027, 1, 4)])

# An offer's own dates against a week.
check("overlaps", overlaps("2026-10-01", "2026-10-03", date(2026, 10, 3), date(2026, 10, 9)), True)
check("ended before the week", overlaps("2026-09-25", "2026-10-02", date(2026, 10, 3), date(2026, 10, 9)), False)
check("starts after the week", overlaps("2026-10-10", None, date(2026, 10, 3), date(2026, 10, 9)), False)
check("open dates", overlaps(None, None, date(2026, 10, 3), date(2026, 10, 9)), True)

# What an offer is.
check("salmon", classify("Филе от сьомга"), ("сьомга", "fish"))
check("tonic is not tuna", classify("Тоник Schweppes")[1], "drinks")
check("green peppers are not cabbage", classify("Зелени чушки"), ("чушки", "vegetables"))
check("frozen shrimp are fish", classify("Замразени скариди"), ("скариди", "fish"))
check("olive oil is not butter", classify("Monini Маслиново масло extra virgin"), ("зехтин", "pantry"))
check("butter is still butter", classify("Deutsche Markenbutter краве масло"), ("масло", "dairy"))
check("roses are not vegetables", classify("Букет рози 50 см", "Плодове и зеленчуци")[1], "non_food")
check("an orchid is not a vegetable", classify("Цветна орхидея Фаленопсис", "Плодове и зеленчуци")[1], "non_food")
check("cauliflower is still a vegetable", classify("Цветно зеле"), ("карфиол", "vegetables"))
check("figs are fruit", classify("Смокиня"), ("смокини", "fruit"))
check("detergent", classify("Препарат за съдове")[1], "non_food")
check("shop category settles the rest", classify("Нещо непознато", "Месо и риба")[1], "fish")

# Ingredients find offers by the generic food, or by the name.
offers = [
    {"id": "1", "name": "Норвежка сьомга филе", "food": "сьомга", "category": "fish"},
    {"id": "2", "name": "Домати розови", "food": "домати", "category": "vegetables"},
    {"id": "3", "name": "Риба тон в олио", "food": "риба тон", "category": "fish"},
    {"id": "4", "name": "Картофи бели", "food": None, "category": "vegetables"},
]
index = OfferIndex(offers)
check("salmon by food", [o["id"] for o in index.match("сьомга")], ["1"])
check("tomatoes plural", [o["id"] for o in index.match("домат")], ["2"])
check("potatoes by name", [o["id"] for o in index.match("картофи")], ["4"])
check("tuna", [o["id"] for o in index.match("риба тон")], ["3"])
check("nothing for rice", index.match("ориз"), [])

done()
