"""Savings goal planner: add something you want to buy and see how long it takes to save for it."""
import math
import os
from datetime import datetime, timezone

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

import planner

db = SQLAlchemy()


class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(5), nullable=False, default="PKR")
    price = db.Column(db.Float, nullable=False)
    saved = db.Column(db.Float, nullable=False, default=0.0)
    monthly = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


def parse_amount(raw, *, allow_zero):
    """Turn form text into a safe number, or None when it is not valid."""
    try:
        value = float(str(raw).replace(",", "").strip())
    except ValueError:
        return None
    if not math.isfinite(value) or value > 1e12:
        return None
    if value < 0 or (value == 0 and not allow_zero):
        return None
    return value


def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    # Locally this is SQLite. On AWS, set DATABASE_URL to your RDS connection string.
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///goals.db")
    app.config.update(config or {})
    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.template_filter("money")
    def money(value):
        return f"{value:,.0f}" if abs(value - round(value)) < 0.005 else f"{value:,.2f}"

    @app.template_filter("month_year")
    def month_year(value):
        return value.strftime("%b %Y")

    def all_rows():
        goals = db.session.scalars(db.select(Goal).order_by(Goal.created_at.desc())).all()
        return [(g, planner.project(g.price, g.saved, g.monthly)) for g in goals]

    def get_goal(goal_id):
        goal = db.session.get(Goal, goal_id)
        if goal is None:
            abort(404)
        return goal

    @app.get("/")
    def index():
        return render_template("index.html", rows=all_rows(), form={})

    @app.post("/goals")
    def create_goal():
        name = (request.form.get("name") or "").strip()
        currency = (request.form.get("currency") or "PKR").strip().upper()[:5] or "PKR"
        price = parse_amount(request.form.get("price"), allow_zero=False)
        saved = parse_amount(request.form.get("saved") or "0", allow_zero=True)
        monthly = parse_amount(request.form.get("monthly"), allow_zero=False)

        errors = []
        if not name or len(name) > 100:
            errors.append("Enter a goal name of up to 100 characters.")
        if price is None:
            errors.append("Enter a price greater than zero.")
        if saved is None:
            errors.append("Enter the amount already saved, or leave it at zero.")
        if monthly is None:
            errors.append("Enter a monthly saving greater than zero.")
        if errors:
            for message in errors:
                flash(message, "error")
            return render_template("index.html", rows=all_rows(), form=request.form), 400

        goal = Goal(name=name, currency=currency, price=price, saved=saved, monthly=monthly)
        db.session.add(goal)
        db.session.commit()
        return redirect(url_for("goal_detail", goal_id=goal.id))

    @app.get("/goals/<int:goal_id>")
    def goal_detail(goal_id):
        goal = get_goal(goal_id)
        proj = planner.project(goal.price, goal.saved, goal.monthly)
        months = request.args.get("months", type=int)
        plan = None
        if months is not None:
            if 1 <= months <= 600 and not proj.reached:
                plan = planner.early_plan(goal.name, goal.price, goal.saved, goal.monthly, months)
            elif not proj.reached:
                flash("Enter a number of months between 1 and 600.", "error")
        scenarios = [] if proj.reached else planner.what_if(goal.price, goal.saved, goal.monthly)
        return render_template("goal.html", goal=goal, proj=proj, plan=plan,
                               scenarios=scenarios, months=months)

    @app.post("/goals/<int:goal_id>/deposit")
    def deposit(goal_id):
        goal = get_goal(goal_id)
        amount = parse_amount(request.form.get("amount"), allow_zero=False)
        if amount is None:
            flash("Enter an amount greater than zero.", "error")
        else:
            goal.saved += amount
            db.session.commit()
            flash("Savings updated.", "ok")
        return redirect(url_for("goal_detail", goal_id=goal.id))

    @app.post("/goals/<int:goal_id>/delete")
    def delete_goal(goal_id):
        goal = get_goal(goal_id)
        db.session.delete(goal)
        db.session.commit()
        return redirect(url_for("index"))

    @app.get("/health")
    def health():
        """Used later by a load balancer or monitoring to check the app and its database."""
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception:
            app.logger.exception("Health check failed")
            return {"status": "unavailable"}, 503
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
