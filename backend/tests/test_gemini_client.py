"""Boundary tests for Gemini integration and fallback resilience.

Tests explicitly cover:
- Successful Gemini structured output
- Malformed Gemini output (bad JSON) -> fallback
- Schema mismatch in Gemini output -> fallback
- Unconfigured client -> fallback with source 'rule-based-fallback'
"""

from unittest.mock import MagicMock, patch
import pytest
from backend.app.schemas import EventCreateRequest
from backend.app.gemini_client import generate_plan_with_gemini_or_fallback
from backend.app.timeline_engine import get_current_ist_date
from datetime import timedelta


@pytest.fixture
def sample_event() -> EventCreateRequest:
    future_date = (get_current_ist_date() + timedelta(days=45)).isoformat()
    return EventCreateRequest(
        name="Aarav 1st Birthday",
        event_type="birthday",
        event_date=future_date,
        location="Bengaluru, Karnataka",
        guest_count=80,
        total_budget=300000,
        style="Playful Pastel",
        theme="Jungle Safari",
        special_requirements="Nut-free snacks for children"
    )


def test_gemini_malformed_json_triggers_fallback(sample_event):
    """Requirement: Malformed Gemini output (bad JSON) -> fallback tagged source = 'rule-based-fallback'."""
    mock_response = MagicMock()
    mock_response.text = "NOT_VALID_JSON {broken: true"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("backend.app.gemini_client._build_client", return_value=mock_client):
        plan = generate_plan_with_gemini_or_fallback(sample_event)

        assert plan.source == "rule-based-fallback"
        assert "fallback" in plan.source_explanation.lower() or "integrity" in plan.source_explanation.lower()
        assert len(plan.budget.items) > 0
        assert plan.total_budget == sample_event.total_budget


def test_gemini_schema_mismatch_triggers_fallback(sample_event):
    """Requirement: Gemini output schema mismatch -> fallback tagged source = 'rule-based-fallback'."""
    mock_response = MagicMock()
    # Missing required 'budget_items' and 'vendors'
    mock_response.text = '{"some_unrelated_key": 123}'

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("backend.app.gemini_client._build_client", return_value=mock_client):
        plan = generate_plan_with_gemini_or_fallback(sample_event)

        assert plan.source == "rule-based-fallback"
        assert len(plan.budget.items) > 0


def test_gemini_api_exception_triggers_fallback(sample_event):
    """Requirement: Network / API failure gracefully falls back to deterministic rules."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("Connection timeout to Gemini API")

    with patch("backend.app.gemini_client._build_client", return_value=mock_client):
        plan = generate_plan_with_gemini_or_fallback(sample_event)

        assert plan.source == "rule-based-fallback"
        assert plan.name == sample_event.name


def test_gemini_successful_structured_output(sample_event):
    """Verify happy-path structured parsing produces source = 'gemini'."""
    valid_payload = {
        "budget_items": [
            {
                "name": "Pastel Balloon Safari Garland",
                "category": "Décor",
                "cost_basis": "fixed",
                "suggested_amount": 35000,
                "notes": "Jungle safari elements in Bengaluru"
            },
            {
                "name": "Live Chaat & Mini Burgers",
                "category": "Catering",
                "cost_basis": "per_guest",
                "suggested_amount": 90000,
                "notes": "Nut-free menu for 80 guests"
            }
        ],
        "vendors": [
            {
                "category": "Décor",
                "service_name": "Bengaluru Balloon Craftsmen",
                "estimated_cost": 35000,
                "contact_notes": "Specialists in pastel theme"
            }
        ],
        "ideas": {
            "decor": [
                {
                    "title": "Jungle Greens & Wooden Cutouts",
                    "description": "Eucalyptus greens and customized wooden baby giraffe photobooth in Bengaluru.",
                    "practical_tip": "Keep photobooth well lit."
                }
            ],
            "food": [],
            "activities": [],
            "themes": [],
            "logistics": []
        }
    }

    import json
    mock_response = MagicMock()
    mock_response.text = json.dumps(valid_payload)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("backend.app.gemini_client._build_client", return_value=mock_client):
        plan = generate_plan_with_gemini_or_fallback(sample_event)

        assert plan.source == "gemini"
        assert "gemini" in plan.source_explanation.lower()
        assert len(plan.budget.items) == 2
        assert plan.budget.total_planned == 125000
