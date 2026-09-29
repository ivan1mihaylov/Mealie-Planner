"""Choosing the week's recipes.

The rules come first: every required rule gets its minimum, then every
preferred one, and only then do offers decide. No rule's maximum is passed.
Within a rule, the recipe with the most ingredients on sale wins, with a
seeded bit of chance so "again" gives another week.

The AI planner proposes; the same rules then check and repair its proposal,
so the rules stay binding whichever planner runs.
"""

from __future__ import annotations

import json
import logging
from random import Random
from typing import Any, Callable

from .rules import PREFERRED, REQUIRED

_LOGGER = logging.getLogger(__name__)

# How much chance may reorder recipes with close sale scores.
_JITTER = 0.75


class Candidate:
    __slots__ = ("id", "name", "flags", "score", "sale")

    def __init__(self, recipe_id: str, name: str, flags: list[str], score: float = 0.0, sale: list[str] | None = None) -> None:
        self.id = recipe_id
        self.name = name
        self.flags = flags
        self.score = score
        self.sale = sale or []


class _Week:
    """The plan being built, with the counts the rules need."""

    def __init__(self, slots: list[str], candidates: dict[str, Candidate], rules: list[dict[str, Any]], assigned: dict[str, str]) -> None:
        self.slots = slots
        self.candidates = candidates
        self.rules = {rule["id"]: rule for rule in rules}
        self.assigned = {slot: recipe for slot, recipe in assigned.items() if slot in slots}
        self.counts = {rule_id: 0 for rule_id in self.rules}
        for recipe_id in self.assigned.values():
            self._count(recipe_id, 1)

    def _count(self, recipe_id: str, step: int) -> None:
        candidate = self.candidates.get(recipe_id)
        for flag in candidate.flags if candidate else []:
            if flag in self.counts:
                self.counts[flag] += step

    @property
    def used(self) -> set[str]:
        return set(self.assigned.values())

    def free(self) -> list[str]:
        return [slot for slot in self.slots if slot not in self.assigned]

    def fits(self, candidate: Candidate) -> bool:
        """Whether adding it keeps every rule at or below its maximum."""
        for flag in candidate.flags:
            rule = self.rules.get(flag)
            if rule and rule.get("max") is not None and self.counts[flag] >= rule["max"]:
                return False
        return True

    def put(self, slot: str, recipe_id: str) -> None:
        if slot in self.assigned:
            self._count(self.assigned[slot], -1)
        self.assigned[slot] = recipe_id
        self._count(recipe_id, 1)

    def remove(self, slot: str) -> None:
        if slot in self.assigned:
            self._count(self.assigned.pop(slot), -1)


def _chooser(candidates: dict[str, Candidate], recent: set[str], rng: Random):
    noise = {recipe_id: rng.random() * _JITTER for recipe_id in sorted(candidates)}

    def choose(week: _Week, wanted: Callable[[Candidate], bool]) -> Candidate | None:
        # Recipes cooked lately are the last resort, not forbidden.
        for allow_recent in (False, True):
            pool = [
                candidate
                for candidate in candidates.values()
                if candidate.id not in week.used
                and (allow_recent or candidate.id not in recent)
                and week.fits(candidate)
                and wanted(candidate)
            ]
            if pool:
                return max(pool, key=lambda candidate: (candidate.score + noise[candidate.id], candidate.id))
        return None

    return choose


def plan_week(
    slots: list[str],
    candidates: list[Candidate],
    rules: list[dict[str, Any]],
    *,
    fixed: dict[str, str] | None = None,
    recent: set[str] | None = None,
    seed: int = 0,
) -> dict[str, str]:
    """Fill the free slots. `fixed` slots (locked by the user, or chosen by AI) stay."""
    rng = Random(seed)
    table = {candidate.id: candidate for candidate in candidates}
    week = _Week(slots, table, rules, fixed or {})
    choose = _chooser(table, recent or set(), rng)
    free = week.free()
    rng.shuffle(free)

    for kind in (REQUIRED, PREFERRED):
        for rule in (rule for rule in rules if rule["kind"] == kind):
            while week.counts[rule["id"]] < rule["min"] and free:
                candidate = choose(week, lambda c, rule_id=rule["id"]: rule_id in c.flags)
                if candidate is None:
                    break
                week.put(free.pop(0), candidate.id)

    while free:
        candidate = choose(week, lambda c: True)
        if candidate is None:
            break
        week.put(free.pop(0), candidate.id)
    return week.assigned


def repair(
    slots: list[str],
    assigned: dict[str, str],
    candidates: list[Candidate],
    rules: list[dict[str, Any]],
    *,
    keep: set[str] | None = None,
    recent: set[str] | None = None,
    seed: int = 0,
) -> dict[str, str]:
    """Bring a proposed week up to every required minimum.

    A slot the user locked is never changed. Another slot gives up its recipe
    only if that recipe is not needed for a required rule itself.
    """
    keep = keep or set()
    table = {candidate.id: candidate for candidate in candidates}
    week = _Week(slots, table, rules, assigned)
    choose = _chooser(table, recent or set(), Random(seed))
    required = [rule for rule in rules if rule["kind"] == REQUIRED]

    def spare(slot: str) -> bool:
        if slot in keep:
            return False
        candidate = table.get(week.assigned[slot])
        if candidate is None:
            return True
        return not any(
            flag == rule["id"] and week.counts[rule["id"]] <= rule["min"]
            for flag in candidate.flags
            for rule in required
        )

    # First, anything over a maximum goes.
    for rule in rules:
        while rule.get("max") is not None and week.counts[rule["id"]] > rule["max"]:
            over = [slot for slot, recipe in week.assigned.items() if slot not in keep and rule["id"] in table.get(recipe, Candidate("", "", [])).flags]
            if not over:
                break
            week.remove(over[-1])

    for rule in required:
        while week.counts[rule["id"]] < rule["min"]:
            candidate = choose(week, lambda c, rule_id=rule["id"]: rule_id in c.flags)
            if candidate is None:
                break
            free = week.free()
            if free:
                week.put(free[0], candidate.id)
                continue
            # Prefer giving up a recipe that serves no rule at all.
            spares = sorted(
                (slot for slot in week.assigned if spare(slot)),
                key=lambda slot: len(table[week.assigned[slot]].flags) if week.assigned[slot] in table else -1,
            )
            if not spares:
                break
            week.put(spares[0], candidate.id)
    return week.assigned


# --- The AI planner -----------------------------------------------------------

AI_SCHEMA = {
    "type": "object",
    "properties": {
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "slot": {"type": "string"},
                    "recipe": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["slot", "recipe"],
            },
        }
    },
    "required": ["plan"],
}

AI_SYSTEM = """You plan a family's meals for a week in Bulgaria.
You get the slots to fill, the rules and the candidate recipes. Each candidate has a short id,
the rules it counts towards, and its ingredients that are on sale in the shops that week.
Priorities, in order:
1. Meet every required rule's minimum and never exceed any rule's maximum.
2. Meet the preferred rules.
3. Prefer recipes with more ingredients on sale.
4. Vary the week: do not repeat a recipe, and do not put similar dishes on consecutive days.
Answer with JSON: {"plan": [{"slot": "<slot>", "recipe": "<id>", "reason": "<a few words in Bulgarian>"}]}."""


def ai_prompt(slots: list[str], candidates: list[Candidate], rules: list[dict[str, Any]], fixed: dict[str, str]) -> tuple[str, dict[str, str]]:
    """The prompt, and the short ids used in it mapped to recipe ids."""
    short = {f"r{index}": candidate.id for index, candidate in enumerate(candidates)}
    back = {recipe_id: key for key, recipe_id in short.items()}
    lines = ["Slots (date|meal type):"]
    lines += [f"- {slot}" + (f" = {back.get(fixed[slot], '?')} (fixed)" if slot in fixed else "") for slot in slots]
    lines.append("\nRules:")
    for rule in rules:
        bound = f"{rule['min']}" + (f"–{rule['max']}" if rule.get("max") is not None else "+")
        lines.append(f"- {rule['id']}: {rule['name']} — {rule['kind']}, {bound} recipes")
    lines.append("\nCandidates (id | name | rules | on sale):")
    for key, recipe_id in short.items():
        candidate = next(c for c in candidates if c.id == recipe_id)
        lines.append(f"{key} | {candidate.name} | {','.join(candidate.flags) or '-'} | {', '.join(candidate.sale[:6]) or '-'}")
    return "\n".join(lines), short


def read_ai_plan(answer: Any, short: dict[str, str], slots: list[str], fixed: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    """The AI's choices that make sense: known slot, known recipe, each once."""
    chosen: dict[str, str] = {}
    reasons: dict[str, str] = {}
    used = set(fixed.values())
    items = answer.get("plan") if isinstance(answer, dict) else answer
    for item in items or []:
        if not isinstance(item, dict):
            continue
        slot, recipe = item.get("slot"), short.get(str(item.get("recipe")))
        if slot not in slots or slot in fixed or slot in chosen or recipe is None or recipe in used:
            continue
        chosen[slot] = recipe
        used.add(recipe)
        if item.get("reason"):
            reasons[slot] = str(item["reason"])[:120]
    return chosen, reasons


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)
