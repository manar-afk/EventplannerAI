"""Integration and route tests for EventPilot AI FastAPI app."""

from datetime import date, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.timeline_engine import get_current_ist_date

client = TestClient(app)


def test_healthz_endpoint():
    """Verify /healthz returns only {"status": "ok"}."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_spa_frontend_served():
    """Verify built SPA index.html is served at root with no-cache header."""
    response = client.get("/")
    assert response.status_code == 200
    assert "<!doctype html>" in response.text.lower()
    assert response.headers.get("Cache-Control") == "no-cache"


def test_spa_path_traversal_prevention():
    """Requirement: Path traversal attempt never serves backend files."""
    # Attempt to traverse into backend directory
    response = client.get("/../../backend/app/config.py")
    assert response.status_code in (200, 404)
    # If 200, it must be the SPA index.html, NEVER python code
    if response.status_code == 200:
        assert "SettingsConfigDict" not in response.text
        assert "<!doctype html>" in response.text.lower()


def test_create_plan_rejects_past_date():
    """Requirement: Reject past event dates at creation with a clear message and 400 status."""
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


def test_create_plan_whitespace_only_name_gives_422():
    """Requirement: Whitespace-only name is cleaned and fails validation with 422."""
    tomorrow = (get_current_ist_date() + timedelta(days=30)).isoformat()
    payload = {
        "name": "     ",
        "event_type": "birthday",
        "event_date": tomorrow,
        "location": "Bengaluru",
        "guest_count": 50,
        "total_budget": 150000
    }
    response = client.post("/api/plans/generate", json=payload)
    assert response.status_code == 422


def test_create_plan_validates_guest_limits():
    """Verify validation boundaries: 1-10,000 guests."""
    tomorrow = (get_current_ist_date() + timedelta(days=60)).isoformat()
    res_zero = client.post("/api/plans/generate", json={
        "name": "Invalid Guests Event",
        "event_type": "birthday",
        "event_date": tomorrow,
        "location": "Mumbai",
        "guest_count": 0,
        "total_budget": 100000
    })
    assert res_zero.status_code == 422

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
    """Verify plan generation returns valid plan with transparent source label."""
    future_date = (get_current_ist_date() + timedelta(days=90)).isoformat()
    payload = {
        "name": "Tarun & Priya Celebration",
        "event_type": "wedding",
        "event_date": future_date,
        "location": "Jaipur, Rajasthan",
        "guest_count": 250,
        "total_budget": 2500000,
        "style": "Traditional Elegance",
        "theme": "Marigold & Amber",
        "special_requirements": "Vegetarian catering"
    }
    response = client.post("/api/plans/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Tarun & Priya Celebration"
    assert data["source"] in ["gemini", "rule-based-fallback"]
    assert data["budget"]["total_budget"] == 2500000
    assert len(data["budget"]["items"]) > 0
    assert len(data["vendors"]) > 0


def test_recalculate_endpoint_with_guest_scaling_and_review_actuals():
    """Verify POST /api/plans/recalculate updates budget, scales per-guest items, and flags actuals for review."""
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
                "actual_amount": 95000,
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

    assert "Catering per head" in data["changed_items"]
    assert "Hall fixed charge" not in data["changed_items"]
    # Actuals should NOT be changed, and Catering should be listed for review
    assert "Catering per head" in data["review_items"]

    budget = data["budget"]
    # 100,000 doubled to 200,000
    assert budget["items"][0]["estimated_amount"] == 200000
    assert budget["items"][0]["actual_amount"] == 95000  # Untouched!
    assert budget["total_planned"] == 250000
    # Effective = 95000 (actual) + 50000 (estimate) = 145000
    assert budget["total_effective"] == 145000
    assert budget["remaining_budget"] == 355000


def test_timeline_recalculate_endpoint():
    """Verify POST /api/plans/timeline recomputes milestones and flags."""
    future_date = (get_current_ist_date() + timedelta(days=45)).isoformat()
    payload = {
        "event_date": future_date,
        "event_type": "wedding",
        "completed_ids": ["ms-1"]
    }
    response = client.post("/api/plans/timeline", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["event_date"] == future_date
    ms1 = [m for m in data["milestones"] if m["id"] == "ms-1"][0]
    assert ms1["is_completed"] is True
    assert ms1["is_overdue"] is False


def test_cors_preflight_disallowed_origin():
    """Verify CORS preflight from disallowed origin gets no Access-Control-Allow-Origin."""
    response = client.options(
        "/api/plans/generate",
        headers={
            "Origin": "http://evil-attacker.com",
            "Access-Control-Request-Method": "POST"
        }
    )
    assert "access-control-allow-origin" not in response.headers
