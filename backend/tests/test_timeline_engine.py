"""Unit tests for timeline and milestone engine."""

from datetime import date, timedelta
import pytest
from backend.app.timeline_engine import generate_timeline, parse_iso_date, IST


def test_zoneinfo_loads():
    """Requirement: ZoneInfo loads Asia/Kolkata timezone."""
    assert IST is not None
    assert "Kolkata" in str(IST)


def test_completed_milestones_have_no_flags():
    """Requirement: completed milestones have no flags."""
    ref_date = date(2026, 11, 1)
    event_date = date(2026, 11, 15)

    # Incomplete ms-1 (offset 180 days -> May 2026, long overdue)
    incomplete_res = generate_timeline(event_date, "wedding", reference_date=ref_date)
    ms1_incomp = incomplete_res.milestones[0]
    assert ms1_incomp.is_overdue is True

    # Mark ms-1 completed
    completed_res = generate_timeline(
        event_date,
        "wedding",
        reference_date=ref_date,
        completed_ids=frozenset(["ms-1"])
    )
    ms1_comp = completed_res.milestones[0]
    assert ms1_comp.is_completed is True
    assert ms1_comp.is_overdue is False
    assert ms1_comp.is_at_risk is False


def test_boundary_dates():
    """Requirement: boundary dates (today, tomorrow, +7 days, offset landing exactly on today)."""
    today = date(2026, 11, 1)

    # 1. Event is today
    res_today = generate_timeline(today, "birthday", reference_date=today)
    assert res_today.days_remaining == 0
    assert res_today.is_past_event is False

    # 2. Event is tomorrow
    res_tomorrow = generate_timeline(today + timedelta(days=1), "birthday", reference_date=today)
    assert res_tomorrow.days_remaining == 1

    # 3. Event is exactly +7 days away
    res_7 = generate_timeline(today + timedelta(days=7), "birthday", reference_date=today)
    assert res_7.days_remaining == 7
    assert res_7.alert_banner is not None

    # 4. Milestone offset landing exactly on today
    # Birthday has 1-day offset milestone: event tomorrow -> milestone target is today!
    ms1 = [m for m in res_tomorrow.milestones if m.days_before_event == 1][0]
    assert ms1.target_date == today.isoformat()
    assert ms1.is_at_risk is True
    assert ms1.is_overdue is False  # Target is today, not past


def test_unknown_event_type_raises():
    """Requirement: unknown event type raises ValueError instead of silently defaulting."""
    with pytest.raises(ValueError, match="Unknown event type"):
        generate_timeline(date(2026, 12, 1), "gala_dinner")
