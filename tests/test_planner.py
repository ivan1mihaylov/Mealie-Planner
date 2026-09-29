"""The planner: the rules come first, then the offers, and no maximum is passed.

    python3 tests/test_planner.py
"""

from __future__ import annotations

import support
from support import check, done

from mealie_planner import planner, rules as rules_mod
from mealie_planner.planner import Candidate


def recipe(rid, name, foods=(), tags=(), categories=()):
    return {"id": rid, "name": name, "tags": list(tags), "categories": list(categories),
            "ingredients": [{"food": food, "text": None} for food in foods]}


RULES = [rules_mod.clean_rule(rule) for rule in rules_mod.presets()]

# --- Matching rules -------------------------------------------------------------
fish_soup = recipe("a", "Рибена чорба", ["шаран", "лук", "морков"], categories=["Супи"])
beans = recipe("b", "Боб яхния", ["боб", "лук", "чушки"])
chicken = recipe("c", "Пиле с ориз", ["пилешко филе", "ориз"])
salad = recipe("d", "Шопска салата", ["домати", "краставици", "сирене"])
unknown = recipe("e", "Нещо", [])
check("fish soup: fish and soup", sorted(rules_mod.flags(fish_soup, RULES)), ["fish", "soup"])
check("beans: legumes and meatless", sorted(rules_mod.flags(beans, RULES)), ["legumes", "meatless"])
check("chicken: nothing", rules_mod.flags(chicken, RULES), [])
check("salad: meatless", rules_mod.flags(salad, RULES), ["meatless"])
check("no ingredients is not meatless", rules_mod.flags(unknown, RULES), [])
check("tag counts", rules_mod.matches(recipe("t", "Х", ["ориз"], tags=["Риба"]), RULES[0]), True)

report = rules_mod.check([["fish"], ["fish"], ["fish"]], RULES)
states = {line["id"]: line["state"] for line in report}
check("three fish is over the max of 2", states["fish"], "over")
check("no legumes: required missing", states["legumes"], "missing")
check("no soup: preferred short", states["soup"], "short")

# --- The local planner ------------------------------------------------------------
SLOTS = [f"2026-10-0{day}|dinner" for day in range(5, 10)]  # five dinners
candidates = [
    Candidate("fish1", "Сьомга", ["fish"], score=0.0),
    Candidate("fish2", "Скумрия", ["fish"], score=0.5),
    Candidate("fish3", "Ципура", ["fish"], score=9.0),   # lots on sale, but fish is capped at 2
    Candidate("fish4", "Пъстърва", ["fish"], score=8.0),
    Candidate("bean1", "Боб", ["legumes", "meatless"], score=0.0),
    Candidate("soup1", "Супа", ["soup"], score=0.0),
    Candidate("meat1", "Кебапчета", [], score=5.0),
    Candidate("meat2", "Пържоли", [], score=4.0),
    Candidate("meat3", "Кюфтета", [], score=3.0),
]
by_id = {c.id: c for c in candidates}


def flags_of(assigned):
    return [by_id[rid].flags for rid in assigned.values()]


for seed in range(20):
    assigned = planner.plan_week(SLOTS, candidates, RULES, seed=seed)
    report = {line["id"]: line["state"] for line in rules_mod.check(flags_of(assigned), RULES)}
    if report["fish"] != "ok" or report["legumes"] != "ok" or len(set(assigned.values())) != 5:
        break
check("20 seeds: fish 1–2, legumes met, no repeats", (report["fish"], report["legumes"], len(set(assigned.values()))), ("ok", "ok", 5))

assigned = planner.plan_week(SLOTS, candidates, RULES, seed=1)
fish = [rid for rid in assigned.values() if "fish" in by_id[rid].flags]
check("never more than two fish, however cheap", len(fish) <= 2, True)
check("the fish on sale is chosen first", "fish3" in fish, True)
check("soup, a preferred rule, is planned", "soup1" in assigned.values(), True)
check("free slots go to what is on sale", "meat1" in assigned.values(), True)

# Locked slots stay, and count towards the rules.
fixed = {SLOTS[0]: "fish1", SLOTS[1]: "fish2"}
assigned = planner.plan_week(SLOTS, candidates, RULES, fixed=fixed, seed=3)
check("locked slots kept", (assigned[SLOTS[0]], assigned[SLOTS[1]]), ("fish1", "fish2"))
check("no third fish next to two locked ones", sum("fish" in by_id[r].flags for r in assigned.values()), 2)

# Recipes cooked lately are avoided while there is anything else.
assigned = planner.plan_week(SLOTS, candidates, RULES, recent={"fish3", "fish4"}, seed=5)
check("recent fish avoided", {"fish3", "fish4"} & set(assigned.values()), set())

# With no legume recipe at all, the rest still gets planned and the report says so.
no_beans = [c for c in candidates if c.id != "bean1"]
assigned = planner.plan_week(SLOTS, no_beans, RULES, seed=2)
report = {line["id"]: line["state"] for line in rules_mod.check([by_id[r].flags for r in assigned.values()], RULES)}
check("unmet required rule reported", report["legumes"], "missing")
check("the week still full", len(assigned), 5)

# --- The AI planner's proposal is checked ------------------------------------------
prompt, short = planner.ai_prompt(SLOTS, candidates, RULES, {})
check("prompt uses short ids", "r0 | Сьомга | fish" in prompt, True)
back = {v: k for k, v in short.items()}
answer = {"plan": [
    {"slot": SLOTS[0], "recipe": back["meat1"], "reason": "евтино"},
    {"slot": SLOTS[1], "recipe": back["meat2"]},
    {"slot": SLOTS[2], "recipe": back["meat3"]},
    {"slot": SLOTS[3], "recipe": back["meat1"]},          # repeated: dropped
    {"slot": "2026-12-24|dinner", "recipe": back["fish1"]},  # no such slot: dropped
    {"slot": SLOTS[4], "recipe": "r999"},                  # no such recipe: dropped
]}
chosen, reasons = planner.read_ai_plan(answer, short, SLOTS, {})
check("only sensible choices kept", chosen, {SLOTS[0]: "meat1", SLOTS[1]: "meat2", SLOTS[2]: "meat3"})
check("reason kept", reasons, {SLOTS[0]: "евтино"})
filled = planner.plan_week(SLOTS, candidates, RULES, fixed=chosen, seed=4)
repaired = planner.repair(SLOTS, filled, candidates, RULES, seed=4)
report = {line["id"]: line["state"] for line in rules_mod.check([by_id[r].flags for r in repaired.values()], RULES)}
check("repaired: fish met", report["fish"], "ok")
check("repaired: legumes met", report["legumes"], "ok")

# Repair never touches a slot the user locked, and removes what is over a maximum.
too_much = {SLOTS[0]: "fish1", SLOTS[1]: "fish2", SLOTS[2]: "fish3", SLOTS[3]: "meat1", SLOTS[4]: "meat2"}
repaired = planner.repair(SLOTS, too_much, candidates, RULES, keep={SLOTS[0]}, seed=0)
check("locked slot kept by repair", repaired[SLOTS[0]], "fish1")
check("repaired: at most two fish", sum("fish" in by_id[r].flags for r in repaired.values()) <= 2, True)
check("repaired: legumes added", "bean1" in repaired.values(), True)

done()
