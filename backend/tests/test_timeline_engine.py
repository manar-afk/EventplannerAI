"""Unit tests for timeline and milestone engine."""

from datetime import date, timedelta
import pytest
from backend.app.timeline_engine import generate_timeline, parse_iso_date


def test_timeline_future_event_with_milestones():
    """Verify standard future event milestone offsets."""
    ref_date = date(2026, 11, 1)
    # Event 200 days in the future
    event_date = "2027-05-20"

    result = generate_timeline(event_date, "wedding", reference_date=ref_date)

    assert result.is_past_event is False
    assert result.days_remaining == (parse_iso_date(event_date) - ref_date).days
    assert len(result.milestones) == 8
    # 180 days before event milestone: 2027-05-20 minus 180 days
    ms180 = [m for m in result.milestones if m.days_before_event == 180][0]
    expected_ms180_date = (parse_iso_date(event_date) - timedelta(days=180)).isoformat()
    assert ms180.target_date == expected_ms180_date


def test_timeline_overdue_and_at_risk_milestones():
    """Requirement: If milestone date passed or event too close, keep real date, mark overdue/at-risk."""
    ref_date = date(2026, 11, 1)
    # Event is only 30 days away, but wedding has 180, 120, 90, 60, 45, 30 day milestones!
    event_date = (ref_date + timedelta(days=30)).isoformat()

    result = generate_timeline(event_date, "wedding", reference_date=ref_date)

    assert result.has_overdue_milestones is True
    assert result.alert_banner is not None
    # 180-day milestone was 150 days ago: must be flagged overdue
    ms_180 = [m for m in result.milestones if m.days_before_event == 180][0]
    assert ms_180.is_overdue is True
    # The real date must NOT have been moved
    expected_date = (parse_iso_date(event_date) - timedelta(days=180)).isoformat()
    assert ms_180.target_date == expected_date


def test_timeline_past_event_flag():
    """Verify past event date sets is_past_event=True and explicit banner."""
    ref_date = date(2026, 11, 1)
    past_date = "2026-10-15"

    result = generate_timeline(past_date, "birthday", reference_date=ref_date)

    assert result.is_past_event is True
    assert result.days_remaining < 0
    assert "in the past" in result.alert_banner
