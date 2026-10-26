"""Pydantic schemas and request/response models for EventPilot AI.

Enforces string length limits, enum bounds, and strict types.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from .budget_engine import BudgetItem, BudgetCalculationResult, MIN_GUESTS, MAX_GUESTS, MIN_BUDGET_INR, MAX_BUDGET_INR
from .timeline_engine import TimelineResult


class EventCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Name of the event")
    event_type: Literal["wedding", "birthday", "community"] = Field(..., description="Type of event")
    event_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Event date in YYYY-MM-DD (IST)")
    location: str = Field(..., min_length=2, max_length=120, description="City / Venue in India")
    guest_count: int = Field(..., ge=MIN_GUESTS, le=MAX_GUESTS, description="Guest count between 1 and 10,000")
    total_budget: int = Field(..., ge=MIN_BUDGET_INR, le=MAX_BUDGET_INR, description="Total budget in integer INR")
    style: str = Field(default="Traditional & Elegant", max_length=100, description="Style preference")
    theme: str = Field(default="", max_length=100, description="Color or cultural theme")
    special_requirements: str = Field(default="", max_length=500, description="Special dietary or logistical requirements")

    @field_validator("name", "location", "style", "theme", "special_requirements")
    @classmethod
    def strip_and_clean(cls, v: str) -> str:
        return v.strip()


class VendorItem(BaseModel):
    id: str
    category: str = Field(..., max_length=50)
    service_name: str = Field(..., max_length=100)
    estimated_cost: int = Field(..., ge=0, le=MAX_BUDGET_INR)
    status: Literal["not_contacted", "contacted", "quoted", "booked"] = "not_contacted"
    contact_notes: Optional[str] = Field(default="", max_length=300)


class IdeaCategory(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    practical_tip: Optional[str] = Field(default="", max_length=300)


class GroupedIdeas(BaseModel):
    decor: List[IdeaCategory] = Field(default_factory=list)
    food: List[IdeaCategory] = Field(default_factory=list)
    activities: List[IdeaCategory] = Field(default_factory=list)
    themes: List[IdeaCategory] = Field(default_factory=list)
    logistics: List[IdeaCategory] = Field(default_factory=list)


class FullPlanResponse(BaseModel):
    id: str
    name: str = Field(..., max_length=100)
    event_type: Literal["wedding", "birthday", "community"]
    event_date: str
    location: str = Field(..., max_length=120)
    guest_count: int
    total_budget: int
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
    total_budget: int = Field(..., ge=MIN_BUDGET_INR, le=MAX_BUDGET_INR)
    guest_count: int = Field(..., ge=MIN_GUESTS, le=MAX_GUESTS)
    previous_guest_count: Optional[int] = Field(None, ge=MIN_GUESTS, le=MAX_GUESTS)
    items: List[BudgetItem]


class RecalculateResponse(BaseModel):
    budget: BudgetCalculationResult
    changed_items: List[str] = Field(default_factory=list)
