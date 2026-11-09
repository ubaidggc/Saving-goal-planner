# Savings Goal Planner

Add something you want to buy (a house, a laptop, anything), say how much you can save each month, and see how many months it takes. If you want to get there sooner, enter a target number of months and the app shows how much extra to save each month, with ideas that fit the size of the gap.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                    # http://127.0.0.1:5000
pytest                           # run the tests
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///goals.db` | Database connection string. Point it at RDS when deployed. |
| `SECRET_KEY` | dev value | Set a long random value in any real deployment. |

## Endpoints

- `GET /` list goals and add a new one
- `GET /goals/<id>` projection, deposits, "reach it sooner" plan, what-if table
- `GET /health` returns `{"status": "ok"}` when the app can reach its database (for load balancer and monitoring checks)

## Project layout

- `planner.py` savings maths and ideas (no Flask, fully unit tested)
- `app.py` routes and database model
- `templates/`, `static/` interface
- `tests/` unit and route tests

## Known limits

- No user accounts: all goals are shared by everyone who opens the app.
- No CSRF protection yet (add Flask-WTF before exposing it publicly).
- Ideas are rule-based, not personalised financial advice.
