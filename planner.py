"""Savings maths and ideas.

Pure functions only (no Flask, no database) so they are easy to test.
"""
import calendar
import math
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

PROPERTY_WORDS = ("house", "home", "flat", "apartment", "plot", "land", "property")


def add_months(start: date, months: int) -> date:
    """Return `start` moved forward by `months`, clamping the day (31 Jan + 1 month = 28/29 Feb)."""
    index = start.month - 1 + months
    year = start.year + index // 12
    month = index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@dataclass(frozen=True)
class Projection:
    remaining: float
    months_needed: Optional[int]
    target_date: Optional[date]
    progress_pct: float
    reached: bool


def project(price: float, saved: float, monthly: float, today: Optional[date] = None) -> Projection:
    """How many months until `saved` reaches `price` at `monthly` per month."""
    today = today or date.today()
    remaining = max(price - saved, 0.0)
    progress = 100.0 if price <= 0 else min(saved / price * 100.0, 100.0)
    if remaining == 0:
        return Projection(0.0, 0, today, 100.0, True)
    if monthly <= 0:
        return Projection(remaining, None, None, progress, False)
    months = math.ceil(round(remaining / monthly, 9))
    return Projection(remaining, months, add_months(today, months), progress, False)


@dataclass(frozen=True)
class Idea:
    title: str
    detail: str


@dataclass(frozen=True)
class EarlyPlan:
    desired_months: int
    required_monthly: float
    extra_per_month: float
    months_earlier: int
    on_track: bool
    ideas: List[Idea]


def ideas_for(name: str, extra: float, monthly: float) -> List[Idea]:
    """Pick ideas that fit the size of the gap between what is saved now and what is needed."""
    ratio = extra / monthly if monthly > 0 else float("inf")
    ideas = [
        Idea("Move the money on payday",
             "Set an automatic transfer for the day your income arrives, so saving happens before spending."),
        Idea("Trim small recurring costs",
             "List subscriptions, food delivery and impulse buys from the last three months, then cut the ones you would not miss."),
    ]
    if ratio > 0.15:
        ideas += [
            Idea("Sell what you no longer use",
                 "Phones, clothes, furniture and gadgets you have stopped using can add a one-off amount to this goal."),
            Idea("Lower your regular bills",
                 "Compare or renegotiate internet, phone, electricity and insurance plans."),
        ]
    if ratio > 0.5:
        ideas += [
            Idea("Add a second source of income",
                 "Freelance work, tutoring or extra weekend hours can close a large gap faster than cutting costs alone."),
            Idea("Send windfalls straight to this goal",
                 "Bonuses, gifts and refunds go into this goal before they reach everyday spending."),
            Idea("Check a cheaper route",
                 "A used or refurbished version, a smaller model or a later purchase date can close a big gap."),
        ]
    if any(word in name.lower() for word in PROPERTY_WORDS):
        ideas.append(
            Idea("Start with the down payment",
                 "Property purchases usually begin with a deposit. Find out how much is required and set that as your first goal."))
    return ideas


def early_plan(name: str, price: float, saved: float, monthly: float,
               desired_months: int, today: Optional[date] = None) -> EarlyPlan:
    """What it takes to reach the goal in `desired_months` instead."""
    current = project(price, saved, monthly, today)
    required = current.remaining / desired_months
    extra = max(required - monthly, 0.0)
    on_track = extra < 0.005
    months_earlier = 0
    if current.months_needed is not None:
        months_earlier = max(current.months_needed - desired_months, 0)
    ideas = [] if on_track else ideas_for(name, extra, monthly)
    return EarlyPlan(desired_months, required, extra, months_earlier, on_track, ideas)


@dataclass(frozen=True)
class Scenario:
    extra_pct: int
    monthly: float
    months_needed: Optional[int]
    target_date: Optional[date]


def what_if(price: float, saved: float, monthly: float, today: Optional[date] = None,
            steps=(10, 25, 50)) -> List[Scenario]:
    """Show how saving 10%, 25% and 50% more changes the finish date."""
    if monthly <= 0:
        return []
    rows = []
    for pct in steps:
        new_monthly = monthly * (1 + pct / 100)
        p = project(price, saved, new_monthly, today)
        rows.append(Scenario(pct, new_monthly, p.months_needed, p.target_date))
    return rows
