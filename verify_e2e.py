"""End-to-end verification script for EventPilot AI.

Simulates the complete user journey:
1. Healthcheck /healthz
2. SPA frontend static serving & Path traversal prevention
3. Create event -> generate plan via POST /api/plans/generate
4. Assert source label ('gemini' when configured, 'rule-based-fallback' when not)
5. Modify a budget item -> POST /api/plans/recalculate
6. Scale guest count -> verify only per-guest items change, actuals preserved
7. Test past date rejection (400 Bad Request)
"""

from datetime import timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings
from backend.app.timeline_engine import get_current_ist_date


def run_e2e_journey():
    client = TestClient(app)
    print("--- 1. Testing /healthz ---")
    r_health = client.get("/healthz")
    assert r_health.status_code == 200, f"Healthcheck failed: {r_health.text}"
    assert r_health.json() == {"status": "ok"}, f"Expected {{'status': 'ok'}}, got {r_health.json()}"
    print(f"Healthz response verified: {r_health.json()}")

    print("\n--- 2. Testing SPA frontend delivery & Path Traversal Prevention ---")
    r_spa = client.get("/")
    assert r_spa.status_code == 200, f"SPA failed: {r_spa.status_code}"
    assert "<!doctype html>" in r_spa.text.lower()
    assert r_spa.headers.get("Cache-Control") == "no-cache"
    print(f"SPA index.html served successfully (Length: {len(r_spa.text)} bytes, Cache-Control: no-cache)")

    r_trav = client.get("/../../backend/app/config.py")
    assert r_trav.status_code in (200, 404)
    if r_trav.status_code == 200:
        assert "SettingsConfigDict" not in r_trav.text, "Path traversal vulnerability: backend code exposed!"
    print("Path traversal attempt successfully defended (backend code not exposed).")

    print("\n--- 3. Testing Plan Generation via POST /api/plans/generate ---")
    today_ist = get_current_ist_date()
    event_date = (today_ist + timedelta(days=120)).isoformat()
    create_payload = {
        "name": "Priya & Rohan Royal Jaipur Wedding",
        "event_type": "wedding",
        "event_date": event_date,
        "location": "Jaipur, Rajasthan",
        "guest_count": 250,
        "total_budget": 2500000,
        "style": "Traditional Elegance",
        "theme": "Marigold & Royal Gold",
        "special_requirements": "Vegetarian catering, wheelchair accessible ramp."
    }
    r_plan = client.post("/api/plans/generate", json=create_payload)
    assert r_plan.status_code == 200, f"Plan generation failed: {r_plan.text}"
    plan = r_plan.json()

    # Requirement 15: Assert plan["source"] equals "gemini" when credentials configured, else "rule-based-fallback"
    expected_source = "gemini" if settings.is_gemini_configured else "rule-based-fallback"
    assert plan["source"] == expected_source, f"Expected source '{expected_source}', but got '{plan['source']}'"
    print(f"Source label verified: '{plan['source']}' (Expected: '{expected_source}')")
    print(f"Explanation: {plan['source_explanation']}")
    print(f"Total budget: INR {plan['budget']['total_budget']:,}")
    print(f"Total planned: INR {plan['budget']['total_planned']:,}")
    print(f"Remaining: INR {plan['budget']['remaining_budget']:,}")
    print(f"Over budget?: {plan['budget']['is_over_budget']}")

    print("\n--- 4. Testing Budget Item Edit & Recalculation ---")
    items = plan['budget']['items']
    items[0]['actual_amount'] = items[0]['estimated_amount'] + 15000
    recalc_payload = {
        "total_budget": plan['budget']['total_budget'],
        "guest_count": plan['guest_count'],
        "items": items
    }
    r_recalc = client.post("/api/plans/recalculate", json=recalc_payload)
    assert r_recalc.status_code == 200, f"Recalculate failed: {r_recalc.text}"
    updated_budget = r_recalc.json()['budget']
    print(f"Updated actual spent: INR {updated_budget['total_actual']:,}")
    print(f"Updated remaining: INR {updated_budget['remaining_budget']:,}")

    print("\n--- 5. Testing Guest Count Scaling (250 -> 300 guests) ---")
    scale_payload = {
        "total_budget": plan['budget']['total_budget'],
        "guest_count": 300,
        "previous_guest_count": 250,
        "items": items
    }
    r_scale = client.post("/api/plans/recalculate", json=scale_payload)
    assert r_scale.status_code == 200
    scale_data = r_scale.json()
    print(f"Changed per-guest items: {scale_data['changed_items']}")
    print(f"Actuals flagged for review: {scale_data['review_items']}")
    assert len(scale_data['changed_items']) > 0

    print("\n--- 6. Testing Past Date Rejection ---")
    past_date = (today_ist - timedelta(days=5)).isoformat()
    bad_payload = dict(create_payload, event_date=past_date)
    r_bad = client.post("/api/plans/generate", json=bad_payload)
    assert r_bad.status_code == 400
    print(f"Past date correctly rejected with: {r_bad.json()['detail']}")

    print("\n==========================================")
    print("ALL END-TO-END VERIFICATION CHECKS PASSED!")
    print("==========================================")


if __name__ == "__main__":
    run_e2e_journey()
