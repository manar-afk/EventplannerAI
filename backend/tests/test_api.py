"""Integration and route tests for EventPilot AI FastAPI app."""

from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.timeline_engine import get_current_ist_date

client = TestClient(app)


def test_healthz_endpoint():
    """Verify /healthz returns ok status and configuration details."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "gemini_model" in data


def test_spa_frontend_served():
    """Verify built SPA index.html is served at root for Cloud Run."""
    response = client.get("/")
    assert response.status_code == 200
    assert "<!doctype html>" in response.text.lower()


def test_create_plan_rejects_past_date():
    """Requirement: Reject past event dates at creation with a clear message."""
    yesterday = (get_current_ist_date() - timedelta(days=1)).isoformat()
    payload = {
        "name": "Past Anniversary Dinner",
        "event_type": "birthday",
        "event_date": yesterday,
        "location": "Bengaluru",
        "guest_count": 50,
        "total_budget": 150000,
        "style": "Contemporary",
        "theme": "Gold & White",
        "special_requirements": "None"
    }
    response = client.post("/api/plans/generate", json=payload)
    assert response.status_code == 400
    assert "past" in response.json()["detail"].lower()


def test_create_plan_validates_guest_limits():
    """Verify validation boundaries: 1-10,000 guests."""
    tomorrow = (get_current_ist_date() + timedelta(days=60)).isoformat()
    # Zero guests
    res_zero = client.post("/api/plans/generate", json={
        "name": "Invalid Guests Event",
        "event_type": "birthday",
        "event_date": tomorrow,
        "location": "Mumbai",
        "guest_count": 0,
        "total_budget": 100000
    })
    assert res_zero.status_code == 422

    # Over 10,000 guests
    res_huge = client.post("/api/plans/generate", json={
        "name": "Invalid Guests Event",
        "event_type": "community",
        "event_date": tomorrow,
        "location": "Mumbai",
        "guest_count": 10001,
        "total_budget": 100000
    })
    assert res_huge.status_code == 422


def test_create_plan_generates_valid_plan_with_fallback_or_gemini():
    """Verify end-to-end plan generation returns valid plan with valid source label."""
    future_date = (get_current_ist_date() + timedelta(days=90)).isoformat()
    payload = {
        "name": "Tarun & Priya Royal Wedding",
        "event_type": "wedding",
        "event_date": future_date,
        "location": "Jaipur, Rajasthan",
        "guest_count": 250,
        "total_budget": 2500000,
        "style": "Royal Rajasthani Heritage",
        "theme": "Marigold & Amber",
        "special_requirements": "Strictly vegetarian Jain food counters"
    }
    response = client.post("/api/plans/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Tarun & Priya Royal Wedding"
    assert data["source"] in ["gemini", "rule-based-fallback"]
    assert data["budget"]["total_budget"] == 2500000
    assert len(data["budget"]["items"]) > 0
    assert len(data["vendors"]) > 0
    assert len(data["ideas"]["food"]) > 0
    # Verify ideas incorporate user location
    assert "Jaipur" in str(data["ideas"]) or "Jaipur" in str(data["budget"]) or "Jaipur" in str(data["vendors"])


def test_recalculate_endpoint_with_guest_scaling():
    """Verify POST /api/plans/recalculate updates budget and scales per-guest items."""
    payload = {
        "total_budget": 500000,
        "guest_count": 200,
        "previous_guest_count": 100,
        "items": [
            {
                "id": "item-1",
                "name": "Catering per head",
                "category": "Catering",
                "cost_basis": "per_guest",
                "estimated_amount": 100000,
                "actual_amount": None,
                "notes": "Food"
            },
            {
                "id": "item-2",
                "name": "Hall fixed charge",
                "category": "Venue",
                "cost_basis": "fixed",
                "estimated_amount": 50000,
                "actual_amount": None,
                "notes": "Fixed venue"
            }
        ]
    }
    response = client.post("/api/plans/recalculate", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Changed items list should contain the per-guest item
    assert "Catering per head" in data["changed_items"]
    assert "Hall fixed charge" not in data["changed_items"]

    budget = data["budget"]
    # 100,000 scaled from 100 to 200 guests -> 200,000
    # Fixed item 50,000 -> 50,000
    # Total planned = 250,000
    assert budget["total_planned"] == 250000
    assert budget["total_effective"] == 250000
    assert budget["remaining_budget"] == 250000
    assert budget["is_over_budget"] is False
