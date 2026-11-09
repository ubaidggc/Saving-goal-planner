import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.test_client() as client:
        yield client


def add_goal(client, **overrides):
    data = {"name": "Laptop", "currency": "PKR", "price": "120000", "saved": "0", "monthly": "10000"}
    data.update(overrides)
    return client.post("/goals", data=data)


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_create_goal_and_see_months(client):
    response = add_goal(client)
    assert response.status_code == 302
    page = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "Laptop" in page and "12" in page and "months to go" in page


def test_invalid_price_is_rejected_and_input_kept(client):
    response = add_goal(client, price="-5", name="Bike")
    assert response.status_code == 400
    body = response.get_data(as_text=True)
    assert "Enter a price greater than zero." in body
    assert 'value="Bike"' in body


def test_non_numeric_monthly_is_rejected(client):
    assert add_goal(client, monthly="abc").status_code == 400


def test_deposit_updates_saved(client):
    location = add_goal(client).headers["Location"]
    client.post(location + "/deposit", data={"amount": "20000"})
    page = client.get(location).get_data(as_text=True)
    assert "20,000" in page and "10 months to go" in page


def test_early_plan_page_shows_extra_and_ideas(client):
    location = add_goal(client).headers["Location"]
    page = client.get(location + "?months=6").get_data(as_text=True)
    assert "10,000" in page and "more each month" in page
    assert "Ways to find the extra money" in page


def test_unknown_goal_is_404(client):
    assert client.get("/goals/999").status_code == 404


def test_delete_goal(client):
    location = add_goal(client).headers["Location"]
    client.post(location + "/delete")
    assert client.get(location).status_code == 404
