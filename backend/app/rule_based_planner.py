"""Deterministic rule-based planning engine for EventPilot AI.

Used as a fallback when Gemini is unavailable, unconfigured, or returns an unparseable response.
Labels source as 'rule-based-fallback'.
Allocates budget via exact largest-remainder integer distribution.
"""

from typing import List, Dict, Any, Literal
import uuid
from .budget_engine import BudgetItem, calculate_budget
from .timeline_engine import generate_timeline
from .schemas import (
    EventCreateRequest,
    FullPlanResponse,
    VendorItem,
    GroupedIdeas,
    IdeaCategory,
)
from .event_data import BUDGET_TEMPLATES, VENDOR_TEMPLATES


def largest_remainder_allocation(total: int, weights: List[int]) -> List[int]:
    """Distribute integer total across weights with exact sum matching."""
    W = sum(weights)
    quotas = [(total * w) / W for w in weights]
    floors = [int(q) for q in quotas]
    diff = total - sum(floors)
    remainders = [(q - f, i) for i, (q, f) in enumerate(zip(quotas, floors))]
    remainders.sort(reverse=True, key=lambda x: x[0])
    for k in range(diff):
        floors[remainders[k][1]] += 1
    return floors


def assemble_plan(
    event: EventCreateRequest,
    items: List[BudgetItem],
    vendors: List[VendorItem],
    ideas: GroupedIdeas,
    source: Literal["gemini", "rule-based-fallback"],
    source_explanation: str
) -> FullPlanResponse:
    """Shared plan assembler for both Gemini and fallback paths."""
    budget_result = calculate_budget(event.total_budget, items)
    timeline_result = generate_timeline(event.event_date, event.event_type)
    now_iso = timeline_result.current_ist_date

    return FullPlanResponse(
        id=f"plan-{uuid.uuid4().hex[:8]}",
        name=event.name,
        event_type=event.event_type,
        event_date=str(event.event_date),
        location=event.location,
        guest_count=event.guest_count,
        total_budget=event.total_budget,
        style=event.style,
        theme=event.theme,
        special_requirements=event.special_requirements,
        source=source,
        source_explanation=source_explanation,
        budget=budget_result,
        timeline=timeline_result,
        vendors=vendors,
        ideas=ideas,
        created_at=now_iso,
        updated_at=now_iso
    )


def generate_rule_based_plan(
    event: EventCreateRequest,
    fallback_reason: str = "Gemini unavailable; showing a template plan built from built-in rules."
) -> FullPlanResponse:
    """Generate a template event plan from standard rules with exact budget distribution."""
    etype = event.event_type.lower().strip()
    if etype == "wedding":
        budget_defs = BUDGET_TEMPLATES["wedding"]
        vendor_defs = VENDOR_TEMPLATES["wedding"]
    elif etype == "birthday":
        budget_defs = BUDGET_TEMPLATES["birthday"]
        vendor_defs = VENDOR_TEMPLATES["birthday"]
    elif etype == "community":
        budget_defs = BUDGET_TEMPLATES["community"]
        vendor_defs = VENDOR_TEMPLATES["community"]
    else:
        raise ValueError(f"Unknown event type '{event.event_type}'. Must be wedding, birthday, or community.")

    # 1. Allocate exact budget amounts via largest-remainder integer split
    weights = [defn["weight"] for defn in budget_defs]
    allocated_amounts = largest_remainder_allocation(event.total_budget, weights)

    # 2. Build budget items and index them by key
    items: List[BudgetItem] = []
    item_by_key: Dict[str, BudgetItem] = {}

    for idx, (defn, amount) in enumerate(zip(budget_defs, allocated_amounts)):
        item_id = f"bi-{idx + 1}-{uuid.uuid4().hex[:6]}"
        item = BudgetItem(
            id=item_id,
            name=defn["name"],
            category=defn["category"],
            cost_basis=defn["cost_basis"],
            estimated_amount=amount,
            actual_amount=None,
            notes=defn["notes"]
        )
        items.append(item)
        item_by_key[defn["key"]] = item

    # 3. Build vendors linked directly to their budget items
    vendors: List[VendorItem] = []
    for idx, v_def in enumerate(vendor_defs):
        bkey = v_def["budget_key"]
        linked_item = item_by_key.get(bkey)
        linked_cost = linked_item.estimated_amount if linked_item else 0
        linked_id = linked_item.id if linked_item else None

        vendors.append(
            VendorItem(
                id=f"v-{idx + 1}-{uuid.uuid4().hex[:6]}",
                budget_item_id=linked_id,
                category=v_def["category"],
                service_name=v_def["service_name"],
                estimated_cost=linked_cost,
                status="not_contacted",
                contact_notes=f"Find a local {v_def['category']} vendor in {event.location}"
            )
        )

    # 4. Culturally neutral ideas
    decor_ideas = [
        IdeaCategory(
            title="Cohesive Ambient Lighting & Palette",
            description="Use warm ambient lighting and consistent floral or fabric accents aligned with the chosen palette.",
            practical_tip="Prioritize entrance and main stage lighting for clear photographs."
        )
    ]

    food_description = "Coordinate service timings between appetizers and main meal counters."
    food_tip = "Confirm guest counts with caterers 5 days prior to the event."
    if event.special_requirements:
        food_tip = f"Confirm with caterer: {event.special_requirements[:200]}"

    food_ideas = [
        IdeaCategory(
            title="Balanced Meal Selection",
            description=food_description,
            practical_tip=food_tip
        )
    ]

    activity_ideas = [
        IdeaCategory(
            title="Scheduled Announcements & Background Music",
            description="Prepare an event playlist and designate an announcer for key milestones.",
            practical_tip="Keep speeches and formal segments under 10 minutes to maintain momentum."
        )
    ]

    theme_ideas = [
        IdeaCategory(
            title="Visual Harmony & Signage",
            description="Coordinate welcome signage, table numbers, and digital invites with the theme.",
            practical_tip="Use readable fonts on all directional signage."
        )
    ]

    logistics_ideas = [
        IdeaCategory(
            title="Guest Transit & Parking Coordination",
            description="Ensure clear arrival signage and designated drop-off points.",
            practical_tip="Share venue location and parking instructions in advance."
        )
    ]

    ideas = GroupedIdeas(
        decor=decor_ideas,
        food=food_ideas,
        activities=activity_ideas,
        themes=theme_ideas,
        logistics=logistics_ideas
    )

    return assemble_plan(
        event=event,
        items=items,
        vendors=vendors,
        ideas=ideas,
        source="rule-based-fallback",
        source_explanation=fallback_reason
    )
