from datetime import date

import planner


TODAY = date(2026, 11, 8)


def test_months_round_up():
    p = planner.project(price=100_000, saved=0, monthly=30_000, today=TODAY)
    assert p.months_needed == 4
    assert p.target_date == date(2027, 3, 8)
    assert not p.reached


def test_exact_division_does_not_add_a_month():
    assert planner.project(90_000, 0, 30_000, TODAY).months_needed == 3


def test_saved_counts_toward_price():
    p = planner.project(100_000, 40_000, 20_000, TODAY)
    assert p.remaining == 60_000
    assert p.months_needed == 3
    assert round(p.progress_pct) == 40


def test_goal_already_reached():
    p = planner.project(50_000, 60_000, 10_000, TODAY)
    assert p.reached and p.months_needed == 0 and p.progress_pct == 100


def test_zero_monthly_has_no_date():
    p = planner.project(50_000, 0, 0, TODAY)
    assert p.months_needed is None and p.target_date is None


def test_add_months_clamps_day_and_crosses_years():
    assert planner.add_months(date(2027, 1, 31), 1) == date(2027, 2, 28)
    assert planner.add_months(date(2026, 11, 8), 3) == date(2027, 2, 8)


def test_early_plan_calculates_extra_per_month():
    plan = planner.early_plan("Laptop", 120_000, 0, 10_000, desired_months=6, today=TODAY)
    assert plan.required_monthly == 20_000
    assert plan.extra_per_month == 10_000
    assert plan.months_earlier == 6  # 12 months now, 6 months wanted
    assert not plan.on_track
    assert plan.ideas


def test_early_plan_when_already_on_track_gives_no_ideas():
    plan = planner.early_plan("Bike", 60_000, 0, 20_000, desired_months=6, today=TODAY)
    assert plan.on_track and plan.ideas == []


def test_bigger_gaps_get_more_ideas():
    small = planner.ideas_for("Phone", extra=1_000, monthly=10_000)
    large = planner.ideas_for("Phone", extra=8_000, monthly=10_000)
    assert len(large) > len(small)


def test_property_goals_get_down_payment_idea():
    titles = [i.title for i in planner.ideas_for("House in Lahore", 5_000, 10_000)]
    assert "Start with the down payment" in titles


def test_what_if_shortens_timeline():
    rows = planner.what_if(120_000, 0, 10_000, TODAY)
    assert [r.months_needed for r in rows] == [11, 10, 8]
