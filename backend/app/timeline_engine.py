"""Deterministic IST timeline and milestone engine for EventPilot AI.

Computes milestones via event date minus type-based offsets.
Flags overdue / at-risk milestones without altering dates.
Timezone: Asia/Kolkata (IST).
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
import zoneinfo
from pydantic import BaseModel, Field

IST = zoneinfo.ZoneInfo("Asia/Kolkata")


class Milestone(BaseModel):
    id: str
    title: str = Field(..., max_length=120)
    category: str = Field(..., max_length=50)
    target_date: str  # YYYY-MM-DD
    days_before_event: int
    is_completed: bool = False
    is_overdue: bool = False
    is_at_risk: bool = False
    notes: Optional[str] = Field(default="", max_length=300)


class TimelineResult(BaseModel):
    event_date: str  # YYYY-MM-DD
    current_ist_date: str  # YYYY-MM-DD
    days_remaining: int
    is_past_event: bool
    has_overdue_milestones: bool
    has_at_risk_milestones: bool
    alert_banner: Optional[str] = None
    milestones: List[Milestone]


# Offset definitions in days before event for Indian event types
MILESTONE_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "wedding": [
        {"title": "Book Wedding Venue & Muhurat Confirmation", "category": "Venue", "days_before": 180},
        {"title": "Finalize Catering Menu (Indian & Global Cuisines)", "category": "Catering", "days_before": 120},
        {"title": "Book Photographer, Videographer & Drone Crew", "category": "Media", "days_before": 90},
        {"title": "Lock Mehndi & Sangeet Décor & DJ/Sound Artist", "category": "Décor & Entertainment", "days_before": 60},
        {"title": "Send Wedding Cards / Digital Invites & RSVP tracking", "category": "Invitations", "days_before": 45},
        {"title": "Outfits, Jewelry & Bridal/Groom Makeup Trials", "category": "Attire", "days_before": 30},
        {"title": "Arrange Guest Accommodations & Transport Buses/Cabs", "category": "Logistics", "days_before": 14},
        {"title": "Final Vendor Walkthrough & Puja Samagri Checklist", "category": "Coordination", "days_before": 3},
    ],
    "birthday": [
        {"title": "Select Theme, Book Party Hall / Lawn", "category": "Venue", "days_before": 30},
        {"title": "Send Digital Invites & Track Guest Count", "category": "Invitations", "days_before": 21},
        {"title": "Order Custom Cake & Finalize Kids/Adults Menu", "category": "Catering", "days_before": 14},
        {"title": "Book Anchor/Magician, Balloon Artist & Music Setup", "category": "Entertainment", "days_before": 10},
        {"title": "Assemble Return Gifts & Party Favors", "category": "Favors", "days_before": 5},
        {"title": "Confirm Venue Setup Timing & Cake Delivery Slot", "category": "Coordination", "days_before": 1},
    ],
    "community": [
        {"title": "Form Organizing Committee & Secure Municipal/Society Approvals", "category": "Permits", "days_before": 60},
        {"title": "Book Community Ground / Stage & Sound Systems", "category": "Infrastructure", "days_before": 45},
        {"title": "Publish Event Circular / Flyers & Volunteer Signups", "category": "Community Outreach", "days_before": 30},
        {"title": "Finalize Food Stalls, Prasad / Community Langar Vendors", "category": "Catering", "days_before": 20},
        {"title": "Arrange Crowd Safety, First-Aid, Parking & Waste Management", "category": "Safety & Logistics", "days_before": 10},
        {"title": "Dry Run on Stage, Generator Backup & Vendor Briefing", "category": "Coordination", "days_before": 2},
    ],
}


def get_current_ist_date() -> date:
    """Return the current calendar date in Asia/Kolkata timezone."""
    return datetime.now(IST).date()


def parse_iso_date(date_str: str) -> date:
    """Safely parse YYYY-MM-DD string to date."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception as exc:
        raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.") from exc


def generate_timeline(
    event_date_str: str,
    event_type: str,
    reference_date: Optional[date] = None
) -> TimelineResult:
    """Generate milestones with strict IST evaluation.

    Rules:
    - Never silently move dates. Real target_date is strictly event_date - offset.
    - If target_date < today and not completed -> marked is_overdue=True.
    - If target_date is within 7 days of today and not completed -> is_at_risk=True.
    - Days remaining = (event_date - current_ist_date).days.
    """
    normalized_type = event_type.lower()
    if normalized_type not in MILESTONE_TEMPLATES:
        normalized_type = "community"

    event_dt = parse_iso_date(event_date_str)
    today = reference_date if reference_date is not None else get_current_ist_date()

    days_remaining = (event_dt - today).days
    is_past_event = days_remaining < 0

    templates = MILESTONE_TEMPLATES[normalized_type]
    milestones: List[Milestone] = []

    has_overdue = False
    has_at_risk = False

    for idx, tmpl in enumerate(templates):
        offset = tmpl["days_before"]
        target = event_dt - timedelta(days=offset)
        target_str = target.isoformat()

        is_overdue = (target < today) and not is_past_event
        # At risk if within 7 days from today or if target has already passed
        is_at_risk = (0 <= (target - today).days <= 7) or is_overdue

        if is_overdue:
            has_overdue = True
        if is_at_risk:
            has_at_risk = True

        milestones.append(
            Milestone(
                id=f"ms-{idx + 1}",
                title=tmpl["title"],
                category=tmpl["category"],
                target_date=target_str,
                days_before_event=offset,
                is_completed=False,
                is_overdue=is_overdue,
                is_at_risk=is_at_risk,
                notes=""
            )
        )

    alert_banner = None
    if is_past_event:
        alert_banner = f"This event date ({event_date_str}) is in the past. Update to a future date to track active milestones."
    elif has_overdue:
        alert_banner = "Some milestones are past their scheduled dates. Review overdue items and expedite vendor bookings."
    elif days_remaining <= 14:
        alert_banner = "Event is coming up in under 2 weeks! Check off critical finalization tasks."

    return TimelineResult(
        event_date=event_date_str,
        current_ist_date=today.isoformat(),
        days_remaining=days_remaining,
        is_past_event=is_past_event,
        has_overdue_milestones=has_overdue,
        has_at_risk_milestones=has_at_risk,
        alert_banner=alert_banner,
        milestones=milestones
    )
