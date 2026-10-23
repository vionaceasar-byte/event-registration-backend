"""
test_app.py - Automated tests for Event Registration API
"""
import os
import pytest
from fastapi.testclient import TestClient
import database
from main import app, EVENT_CAPACITY

TEST_DB = "test_event.db"


@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure a clean, isolated database for every test."""
    database.DB_FILE = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    database.init_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


client = TestClient(app)


def test_successful_registration():
    payload = {
        "name": "Rahul Sharma",
        "email": "rahul.sharma@example.com",
        "department": "Information Technology",
    }
    response = client.post("/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Rahul Sharma"
    assert data["email"] == "rahul.sharma@example.com"
    assert data["department"] == "Information Technology"
    assert "id" in data
    assert "registered_at" in data


def test_duplicate_email():
    payload = {
        "name": "Rahul Sharma",
        "email": "rahul.sharma@example.com",
        "department": "Information Technology",
    }
    client.post("/register", json=payload)
    response = client.post("/register", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Already registered"


def test_event_full():
    for i in range(EVENT_CAPACITY):
        client.post(
            "/register",
            json={
                "name": f"Student {i+1}",
                "email": f"student{i+1}@example.com",
            },
        )
    overflow = client.post(
        "/register",
        json={
            "name": "Overflow Student",
            "email": "overflow@example.com",
        },
    )
    assert overflow.status_code == 400
    assert overflow.json()["detail"] == "Event is full"


def test_invalid_input():
    # Invalid email format
    res1 = client.post("/register", json={"name": "Alice", "email": "not-an-email"})
    assert res1.status_code == 422

    # Missing required name
    res2 = client.post("/register", json={"email": "alice@example.com"})
    assert res2.status_code == 422

    # Whitespace-only name
    res3 = client.post("/register", json={"name": "   ", "email": "alice@example.com"})
    assert res3.status_code == 422


def test_registration_not_found():
    response = client.get("/registrations/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Registration not found"


def test_view_all_registrations():
    client.post(
        "/register",
        json={
            "name": "Diya Patel",
            "email": "diya@example.com",
            "department": "Computer Science",
        },
    )
    response = client.get("/registrations")
    assert response.status_code == 200
    data = response.json()
    assert data["total_registered"] == 1
    assert data["capacity"] == EVENT_CAPACITY
    assert data["seats_status"] == f"1 / {EVENT_CAPACITY} seats filled"
    assert len(data["registrations"]) == 1


def test_cancel_registration():
    res = client.post(
        "/register",
        json={
            "name": "Rohan Verma",
            "email": "rohan@example.com",
        },
    )
    reg_id = res.json()["id"]

    del_res = client.delete(f"/registrations/{reg_id}")
    assert del_res.status_code == 200
    assert "freed" in del_res.json()["message"]

    # Verify ID is now 404
    check = client.get(f"/registrations/{reg_id}")
    assert check.status_code == 404
