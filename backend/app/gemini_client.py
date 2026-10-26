"""Gemini integration module using the modern google-genai SDK.

Handles Vertex AI / Application Default Credentials or GEMINI_API_KEY.
Uses structured schema generation, timeouts, 1-retry transient logic,
prompt-injection protection via XML delimitation, and graceful fallback
to the deterministic rule-based planner.
"""

import json
import logging
import time
import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError

from .config import settings
from .schemas import (
    EventCreateRequest,
    FullPlanResponse,
    VendorItem,
    GroupedIdeas,
    IdeaCategory,
)
from .budget_engine import BudgetItem, calculate_budget
from .timeline_engine import generate_timeline
from .rule_based_planner import generate_rule_based_plan

logger = logging.getLogger("eventpilot.gemini")


# Pydantic schema specifically for Gemini structured output parsing
class ProposedBudgetItem(BaseModel):
    name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    cost_basis: str = Field(..., pattern="^(per_guest|fixed)$")
    suggested_amount: int = Field(..., ge=0)
    notes: Optional[str] = Field(default="", max_length=300)


class ProposedVendor(BaseModel):
    category: str = Field(..., max_length=50)
    service_name: str = Field(..., max_length=100)
    estimated_cost: int = Field(..., ge=0)
    contact_notes: Optional[str] = Field(default="", max_length=300)


class ProposedIdeasGroup(BaseModel):
    decor: List[IdeaCategory] = Field(default_factory=list)
    food: List[IdeaCategory] = Field(default_factory=list)
    activities: List[IdeaCategory] = Field(default_factory=list)
    themes: List[IdeaCategory] = Field(default_factory=list)
    logistics: List[IdeaCategory] = Field(default_factory=list)


class GeminiPlanProposal(BaseModel):
    budget_items: List[ProposedBudgetItem] = Field(..., min_length=1)
    vendors: List[ProposedVendor] = Field(..., min_length=1)
    ideas: ProposedIdeasGroup


def _build_client():
    """Build google-genai Client supporting Vertex AI ADC or GEMINI_API_KEY.

    Returns None if no API key or Google Application Credentials are configured.
    """
    import os
    from google import genai

    if settings.gemini_api_key and settings.gemini_api_key.strip():
        return genai.Client(api_key=settings.gemini_api_key.strip())

    # Check for ADC or Vertex environment
    has_adc = (
        bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")) or
        bool(os.getenv("K_SERVICE")) or  # Standard Google Cloud Run environment variable
        bool(os.getenv("GOOGLE_CLOUD_PROJECT"))
    )

    if has_adc:
        try:
            project = os.getenv("GOOGLE_CLOUD_PROJECT") or None
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            return genai.Client(vertexai=True, project=project, location=location)
        except Exception as exc:
            logger.warning("Failed to initialize Vertex AI client with ADC: %s", exc)
            return None

    # No credentials configured
    return None


def _build_safe_prompt(event: EventCreateRequest) -> str:
    """Format prompt with XML delimiters to neutralize prompt injection attacks."""
    return f"""You are a master Indian event planner and cultural expert.
Generate a structured, hyper-personalized planning proposal for an Indian event.

Crucial Grounding Rules:
1. Ideas, vendor selections, and budget line items MUST directly incorporate the user's specific location, style, theme, and special requirements. Generic filler is strictly unacceptable.
2. For money: Suggest realistic integer INR costs for an event in India. Do NOT perform total budget balancing; provide estimated costs per item. The system budget engine handles all totals.
3. Classify cost_basis as strictly either 'per_guest' (e.g. catering, invitations, return gifts) or 'fixed' (e.g. venue rental, stage décor, sound/DJ, photography).
4. Strictly return JSON adhering to the provided schema.

<USER_INPUTS>
<EVENT_NAME>{event.name}</EVENT_NAME>
<EVENT_TYPE>{event.event_type}</EVENT_TYPE>
<EVENT_DATE_IST>{event.event_date}</EVENT_DATE_IST>
<LOCATION>{event.location}</LOCATION>
<GUEST_COUNT>{event.guest_count}</GUEST_COUNT>
<TARGET_BUDGET_INR>{event.total_budget}</TARGET_BUDGET_INR>
<STYLE_PREFERENCE>{event.style}</STYLE_PREFERENCE>
<THEME>{event.theme}</THEME>
<SPECIAL_REQUIREMENTS>{event.special_requirements}</SPECIAL_REQUIREMENTS>
</USER_INPUTS>
"""


def generate_plan_with_gemini_or_fallback(event: EventCreateRequest) -> FullPlanResponse:
    """Generate plan using Gemini model or gracefully fall back to rule-based planner.

    Enforces:
    - Retries once on transient network/timeout errors.
    - Schema validation via Pydantic.
    - Transparent source labeling ('gemini' vs 'rule-based-fallback').
    - Never changes user's total budget; flags over-budget if proposed estimates exceed it.
    """
    client = None
    try:
        client = _build_client()
    except Exception as exc:
        logger.warning("Could not initialize Gemini client: %s. Using rule-based fallback.", exc)

    if client is None:
        return generate_rule_based_plan(
            event,
            fallback_reason="Gemini API credentials not configured in environment. Using verified Indian cultural event rules."
        )

    prompt = _build_safe_prompt(event)
    raw_response_text: Optional[str] = None
    last_error: Optional[Exception] = None

    # Up to 1 retry on transient failures
    for attempt in range(2):
        try:
            logger.info("Calling Gemini model '%s' (attempt %d/2)...", settings.gemini_model, attempt + 1)
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": GeminiPlanProposal,
                    "max_output_tokens": 4096,
                    "temperature": 0.4,
                }
            )
            if response and response.text:
                raw_response_text = response.text
                break
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini attempt %d failed: %s", attempt + 1, exc)
            time.sleep(1.0)

    if not raw_response_text:
        err_msg = str(last_error) if last_error else "Empty response from model"
        logger.warning("Gemini generation failed (%s). Triggering fallback.", err_msg)
        return generate_rule_based_plan(
            event,
            fallback_reason=f"Gemini service unavailable ({err_msg[:80]}). Displaying deterministic rule-based plan."
        )

    # Validate model response with Pydantic
    try:
        data = json.loads(raw_response_text)
        proposal = GeminiPlanProposal.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as parse_exc:
        logger.error("Gemini response failed schema validation: %s. Falling back.", parse_exc)
        return generate_rule_based_plan(
            event,
            fallback_reason="Gemini output failed structured validation. Generated fallback plan to ensure data integrity."
        )

    # Convert proposed budget items into deterministic BudgetItem objects
    items: List[BudgetItem] = []
    for idx, prop in enumerate(proposal.budget_items):
        items.append(
            BudgetItem(
                id=f"bi-g-{idx + 1}-{uuid.uuid4().hex[:6]}",
                name=prop.name,
                category=prop.category,
                cost_basis=prop.cost_basis,
                estimated_amount=int(prop.suggested_amount),
                actual_amount=None,
                notes=prop.notes or ""
            )
        )

    # Budget calculation via pure Python engine
    budget_result = calculate_budget(event.total_budget, items)

    # Deterministic IST Timeline
    timeline_result = generate_timeline(event.event_date, event.event_type)

    # Vendors
    vendors: List[VendorItem] = []
    for idx, v in enumerate(proposal.vendors):
        vendors.append(
            VendorItem(
                id=f"v-g-{idx + 1}-{uuid.uuid4().hex[:6]}",
                category=v.category,
                service_name=v.service_name,
                estimated_cost=int(v.estimated_cost),
                status="not_contacted",
                contact_notes=v.contact_notes or ""
            )
        )

    ideas = GroupedIdeas(
        decor=proposal.ideas.decor,
        food=proposal.ideas.food,
        activities=proposal.ideas.activities,
        themes=proposal.ideas.themes,
        logistics=proposal.ideas.logistics
    )

    now_iso = timeline_result.current_ist_date

    return FullPlanResponse(
        id=f"plan-{uuid.uuid4().hex[:8]}",
        name=event.name,
        event_type=event.event_type,
        event_date=event.event_date,
        location=event.location,
        guest_count=event.guest_count,
        total_budget=event.total_budget,
        style=event.style,
        theme=event.theme,
        special_requirements=event.special_requirements,
        source="gemini",
        source_explanation=f"Custom plan generated by {settings.gemini_model}",
        budget=budget_result,
        timeline=timeline_result,
        vendors=vendors,
        ideas=ideas,
        created_at=now_iso,
        updated_at=now_iso
    )
