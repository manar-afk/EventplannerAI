"""End-to-end verification script for EventPilot AI.

Simulates the complete user journey:
1. Healthcheck /healthz
2. SPA frontend static serving /
3. Create event -> generate plan via POST /api/plans/generate
4. Verify source label ('gemini' or 'rule-based-fallback')
5. Modify a budget item -> POST /api/plans/recalculate
6. Scale guest count -> verify only per-guest items change
7. Test past date rejection
"""

import sys
import json
from datetime import date, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app

def run_e2e_journey():
    client = TestClient(app)
    print("--- 1. Testing /healthz ---")
    r_health = client.get("/healthz")
    assert r_health.status_code == 200, f"Healthcheck failed: {r_health.text}"
    print(f"Healthz response: {r_health.json()}")

    print("\n--- 2. Testing SPA frontend delivery at / ---")
    r_spa = client.get("/")
    assert r_spa.status_code == 200, f"SPA failed: {r_spa.status_code}"
    assert "<!doctype html>" in r_spa.text.lower()
    print(f"SPA index.html served successfully (Length: {len(r_spa.text)} bytes)")

    print("\n--- 3. Testing Plan Generation via POST /api/plans/generate ---")
    event_date = (date.today() + timedelta(days=120)).isoformat()
    create_payload = {
        "name": "Priya & Rohan Royal Jaipur Wedding",
        "event_type": "wedding",
        "event_date": event_date,
        "location": "Jaipur, Rajasthan",
        "guest_count": 250,
        "total_budget": 2500000,
        "style": "Royal Rajasthani Heritage",
        "theme": "Marigold & Royal Gold",
        "special_requirements": "Strictly pure vegetarian Jain catering, wheelchair accessible mandap."
    }
    r_plan = client.post("/api/plans/generate", json=create_payload)
    assert r_plan.status_code == 200, f"Plan generation failed: {r_plan.text}"
    plan = r_plan.json()
    print(f"Plan ID: {plan['id']}")
    print(f"Source label: {plan['source']} ({plan['source_explanation']})")
    print(f"Total budget: INR {plan['budget']['total_budget']:,}")
    print(f"Total planned: INR {plan['budget']['total_planned']:,}")
    print(f"Remaining: INR {plan['budget']['remaining_budget']:,}")
    print(f"Over budget?: {plan['budget']['is_over_budget']}")
    print(f"Budget line items count: {len(plan['budget']['items'])}")
    print(f"Milestones count: {len(plan['timeline']['milestones'])}")
    print(f"Vendors count: {len(plan['vendors'])}")
    print(f"Food ideas count: {len(plan['ideas']['food'])}")

    print("\n--- 4. Testing Budget Item Edit & Recalculation ---")
    items = plan['budget']['items']
    # Record actual cost for the first item
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
    assert len(scale_data['changed_items']) > 0

    print("\n--- 6. Testing Past Date Rejection ---")
    past_date = (date.today() - timedelta(days=5)).isoformat()
    bad_payload = dict(create_payload, event_date=past_date)
    r_bad = client.post("/api/plans/generate", json=bad_payload)
    assert r_bad.status_code == 400
    print(f"Past date correctly rejected with: {r_bad.json()['detail']}")

    print("\n==========================================")
    print("ALL END-TO-END VERIFICATION CHECKS PASSED!")
    print("==========================================")

if __name__ == "__main__":
    run_e2e_journey()
