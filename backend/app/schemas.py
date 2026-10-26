"""Pydantic schemas and request/response models for EventPilot AI.

Enforces string length limits, control character sanitization before validation,
StrictInt types, and output truncation BeforeValidators.
"""

from datetime import date
import re
from typing import List, Optional, Literal, Annotated, Any
from pydantic import BaseModel, Field, StrictInt, BeforeValidator, field_validator
from .budget_engine import (
    BudgetItem,
    BudgetCalculationResult,
    MIN_GUESTS,
    MAX_GUESTS,
    MIN_BUDGET_INR,
    MAX_BUDGET_INR,
    truncate_with_ellipsis
)
from .timeline_engine import TimelineResult

DEFAULT_STYLE = "Traditional Elegance"


def sanitize_input_text(v: Any) -> Any:
    """Strip control characters and whitespace before validation."""
    if isinstance(v, str):
        # Replace control chars (including newlines and tabs) with a single space
        cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", v)
        # Collapse multiple spaces and strip
        return re.sub(r"\s+", " ", cleaned).strip()
    return v


SanitizedStr = Annotated[str, BeforeValidator(sanitize_input_text)]


def truncate_100(v: Any) -> str:
    return truncate_with_ellipsis(str(v) if v is not None else "", 100)


def truncate_300(v: Any) -> str:
    return truncate_with_ellipsis(str(v) if v is not None else "", 300)


def truncate_500(v: Any) -> str:
    return truncate_with_ellipsis(str(v) if v is not None else "", 500)


class EventCreateRequest(BaseModel):
    name: SanitizedStr = Field(..., min_length=2, max_length=100, description="Name of the event")
    event_type: Literal["wedding", "birthday", "community"] = Field(..., description="Type of event")
    event_date: date = Field(..., description="Event date in YYYY-MM-DD (IST)")
    location: SanitizedStr = Field(..., min_length=2, max_length=120, description="City / Venue in India")
    guest_count: StrictInt = Field(..., ge=MIN_GUESTS, le=MAX_GUESTS, description="Guest count between 1 and 10,000")
    total_budget: StrictInt = Field(..., ge=MIN_BUDGET_INR, le=MAX_BUDGET_INR, description="Total budget in integer INR")
    style: SanitizedStr = Field(default=DEFAULT_STYLE, max_length=100, description="Style preference")
    theme: SanitizedStr = Field(default="", max_length=100, description="Color or cultural theme")
    special_requirements: SanitizedStr = Field(default="", max_length=500, description="Special dietary or logistical requirements")


class VendorItem(BaseModel):
    id: str = Field(..., max_length=64)
    budget_item_id: Optional[str] = Field(None, max_length=64)
    category: str = Field(..., max_length=50)
    service_name: str = Field(..., max_length=100)
    estimated_cost: StrictInt = Field(..., ge=0, le=MAX_BUDGET_INR)
    status: Literal["not_contacted", "contacted", "quoted", "booked"] = "not_contacted"
    contact_notes: Annotated[str, BeforeValidator(truncate_300)] = Field(default="", max_length=300)


class IdeaCategory(BaseModel):
    title: Annotated[str, BeforeValidator(truncate_100)] = Field(..., max_length=100)
    description: Annotated[str, BeforeValidator(truncate_500)] = Field(..., max_length=500)
    practical_tip: Annotated[str, BeforeValidator(truncate_300)] = Field(default="", max_length=300)


class GroupedIdeas(BaseModel):
    decor: List[IdeaCategory] = Field(default_factory=list)
    food: List[IdeaCategory] = Field(default_factory=list)
    activities: List[IdeaCategory] = Field(default_factory=list)
    themes: List[IdeaCategory] = Field(default_factory=list)
    logistics: List[IdeaCategory] = Field(default_factory=list)


class FullPlanResponse(BaseModel):
    id: str = Field(..., max_length=64)
    name: str = Field(..., max_length=100)
    event_type: Literal["wedding", "birthday", "community"]
    event_date: str
    location: str = Field(..., max_length=120)
    guest_count: StrictInt
    total_budget: StrictInt
    style: str = Field(..., max_length=100)
    theme: str = Field(..., max_length=100)
    special_requirements: str = Field(..., max_length=500)
    source: Literal["gemini", "rule-based-fallback"]
    source_explanation: Optional[str] = Field(default="", max_length=300)
    budget: BudgetCalculationResult
    timeline: TimelineResult
    vendors: List[VendorItem]
    ideas: GroupedIdeas
    created_at: str
    updated_at: str


class RecalculateRequest(BaseModel):
    total_budget: StrictInt = Field(..., ge=MIN_BUDGET_INR, le=MAX_BUDGET_INR)
    guest_count: StrictInt = Field(..., ge=MIN_GUESTS, le=MAX_GUESTS)
    previous_guest_count: Optional[StrictInt] = Field(None, ge=MIN_GUESTS, le=MAX_GUESTS)
    items: List[BudgetItem] = Field(..., max_length=100)


class RecalculateResponse(BaseModel):
    budget: BudgetCalculationResult
    changed_items: List[str] = Field(default_factory=list)
    review_items: List[str] = Field(default_factory=list)


class TimelineRecalculateRequest(BaseModel):
    event_date: date
    event_type: Literal["wedding", "birthday", "community"]
    completed_ids: List[str] = Field(default_factory=list, max_length=100)
