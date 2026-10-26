"""Deterministic IST timeline and milestone engine for EventPilot AI.

Computes milestones via event date minus type-based offsets.
Flags overdue / at-risk milestones strictly on incomplete items without altering dates.
Timezone: Asia/Kolkata (IST).
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Set, FrozenSet
import zoneinfo
from pydantic import BaseModel, Field

try:
    IST = zoneinfo.ZoneInfo("Asia/Kolkata")
except Exception:
    import pytz
    IST = pytz.timezone("Asia/Kolkata")


class Milestone(BaseModel):
    id: str = Field(..., max_length=64)
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


# Standard milestones by event type
MILESTONE_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "wedding": [
        {"title": "Book Wedding Venue & Confirm Muhurat", "category": "Venue", "days_before": 180},
        {"title": "Finalize Catering Menu & Food Counters", "category": "Catering", "days_before": 120},
        {"title": "Book Photography, Videography & Media Team", "category": "Media", "days_before": 90},
        {"title": "Confirm Floral & Stage Décor and Sound/DJ", "category": "Décor", "days_before": 60},
        {"title": "Send Invitations & Track RSVPs", "category": "Invitations", "days_before": 45},
        {"title": "Ceremonial Attire & Styling Fittings", "category": "Attire", "days_before": 30},
        {"title": "Arrange Guest Accommodations & Local Shuttles", "category": "Logistics", "days_before": 14},
        {"title": "Final Vendor Walkthrough & Ceremony Essentials", "category": "Coordination", "days_before": 3},
    ],
    "birthday": [
        {"title": "Book Party Venue / Garden Space", "category": "Venue", "days_before": 30},
        {"title": "Send Digital Invites & Track Headcount", "category": "Invitations", "days_before": 21},
        {"title": "Order Custom Cake & Finalize Menu", "category": "Catering", "days_before": 14},
        {"title": "Book Emcee / Entertainer & Sound Setup", "category": "Entertainment", "days_before": 10},
        {"title": "Assemble Party Favors & Return Gifts", "category": "Favors", "days_before": 5},
        {"title": "Confirm Venue Setup Timing & Delivery Slots", "category": "Coordination", "days_before": 1},
    ],
    "community": [
        {"title": "Secure Venue Reservation & Approvals", "category": "Permits", "days_before": 60},
        {"title": "Arrange Stage, Tent & Sound Setup", "category": "Infrastructure", "days_before": 45},
        {"title": "Publish Event Circular & Volunteer Coordination", "category": "Outreach", "days_before": 30},
        {"title": "Finalize Catering & Refreshments Suppliers", "category": "Catering", "days_before": 20},
        {"title": "Coordinate Safety, Parking & Facilities", "category": "Logistics", "days_before": 10},
        {"title": "Stage Technical Dry Run & Briefings", "category": "Coordination", "days_before": 2},
    ],
}


def get_current_ist_date() -> date:
    """Return the current calendar date in Asia/Kolkata timezone."""
    return datetime.now(IST).date()


def parse_iso_date(date_val: Any) -> date:
    """Safely parse date object or YYYY-MM-DD string to date."""
    if isinstance(date_val, date):
        return date_val
    try:
        return datetime.strptime(str(date_val).strip(), "%Y-%m-%d").date()
    except OverflowError as exc:
        raise ValueError(f"Date '{date_val}' is out of range.") from exc
    except Exception as exc:
        raise ValueError(f"Invalid date format '{date_val}'. Expected YYYY-MM-DD.") from exc


def generate_timeline(
    event_date_input: Any,
    event_type: str,
    reference_date: Optional[date] = None,
    completed_ids: Optional[FrozenSet[str]] = None
) -> TimelineResult:
    """Generate standard timeline for the specified event type.

    Rules:
    - Never move computed dates silently.
    - Overdue and at-risk flags apply ONLY to incomplete milestones.
    - Raises ValueError on unknown event types.
    """
    normalized_type = event_type.lower().strip()
    if normalized_type not in MILESTONE_TEMPLATES:
        raise ValueError(f"Unknown event type: '{event_type}'. Must be one of: wedding, birthday, community.")

    try:
        event_dt = parse_iso_date(event_date_input)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"Invalid event date: {exc}") from exc

    today = reference_date if reference_date is not None else get_current_ist_date()
    completed_set: Set[str] = set(completed_ids) if completed_ids else set()

    try:
        days_remaining = (event_dt - today).days
    except OverflowError as exc:
        raise ValueError("Event date produces an arithmetic overflow.") from exc

    is_past_event = days_remaining < 0
    templates = MILESTONE_TEMPLATES[normalized_type]
    milestones: List[Milestone] = []

    has_overdue = False
    has_at_risk = False

    for idx, tmpl in enumerate(templates):
        ms_id = f"ms-{idx + 1}"
        offset = tmpl["days_before"]

        try:
            target = event_dt - timedelta(days=offset)
        except OverflowError as exc:
            raise ValueError(f"Milestone offset produces an overflow for date {event_dt}.") from exc

        target_str = target.isoformat()
        is_completed = ms_id in completed_set

        # Overdue and at-risk flags apply ONLY if NOT completed
        if not is_completed:
            is_overdue = (target < today) and not is_past_event
            is_at_risk = ((0 <= (target - today).days <= 7) or is_overdue) and not is_past_event
        else:
            is_overdue = False
            is_at_risk = False

        if is_overdue:
            has_overdue = True
        if is_at_risk:
            has_at_risk = True

        milestones.append(
            Milestone(
                id=ms_id,
                title=tmpl["title"],
                category=tmpl["category"],
                target_date=target_str,
                days_before_event=offset,
                is_completed=is_completed,
                is_overdue=is_overdue,
                is_at_risk=is_at_risk,
                notes=""
            )
        )

    alert_banner = None
    if is_past_event:
        alert_banner = f"This event date ({event_dt.isoformat()}) is in the past. Standard milestone dates have concluded."
    elif has_overdue:
        alert_banner = "Some scheduled milestones have passed. Review pending items."
    elif days_remaining <= 14:
        alert_banner = "Event is within 2 weeks. Finalize vendor confirmations and critical tasks."

    return TimelineResult(
        event_date=event_dt.isoformat(),
        current_ist_date=today.isoformat(),
        days_remaining=days_remaining,
        is_past_event=is_past_event,
        has_overdue_milestones=has_overdue,
        has_at_risk_milestones=has_at_risk,
        alert_banner=alert_banner,
        milestones=milestones
    )
