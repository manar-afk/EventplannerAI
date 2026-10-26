"""Pure Python budget engine for EventPilot AI.

Enforces integer rupee arithmetic, separate estimates vs actuals,
guest-count scaling using integer half-up math, and over-budget checks
with zero floating-point drift. No I/O or network operations.
"""

from typing import List, Optional, Tuple, Dict, Literal
from pydantic import BaseModel, Field, StrictInt, field_validator

MIN_GUESTS = 1
MAX_GUESTS = 10_000
MIN_BUDGET_INR = 1_000
MAX_BUDGET_INR = 100_000_000  # 10 Crore INR limit


def truncate_with_ellipsis(text: Optional[str], max_len: int) -> str:
    """Safely truncate text with an ellipsis if it exceeds max_len."""
    if not text:
        return ""
    stripped = text.strip()
    if len(stripped) <= max_len:
        return stripped
    return stripped[: max_len - 3] + "..."


class BudgetItem(BaseModel):
    id: str = Field(..., max_length=64)
    name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    cost_basis: Literal["per_guest", "fixed"]
    estimated_amount: StrictInt = Field(..., ge=0, le=MAX_BUDGET_INR)
    actual_amount: Optional[StrictInt] = Field(None, ge=0, le=MAX_BUDGET_INR)
    notes: Optional[str] = Field(default="", max_length=300)

    @field_validator("notes", mode="before")
    @classmethod
    def truncate_notes(cls, v: Optional[str]) -> str:
        return truncate_with_ellipsis(v, 300)


class CategoryBreakdown(BaseModel):
    category: str
    planned_amount: StrictInt
    actual_amount: StrictInt
    effective_amount: StrictInt
    item_count: StrictInt


class BudgetCalculationResult(BaseModel):
    total_budget: StrictInt
    total_planned: StrictInt
    total_actual: StrictInt
    total_effective: StrictInt
    remaining_budget: StrictInt
    is_over_budget: bool
    over_budget_amount: StrictInt
    categories: List[CategoryBreakdown]
    items: List[BudgetItem]


def validate_total_budget(total_budget: int) -> None:
    """Validate bounds on total budget."""
    if not isinstance(total_budget, int) or isinstance(total_budget, bool):
        raise ValueError("Total budget must be a strict integer.")
    if total_budget < MIN_BUDGET_INR:
        raise ValueError(f"Total budget must be at least ₹{MIN_BUDGET_INR:,}.")
    if total_budget > MAX_BUDGET_INR:
        raise ValueError(f"Total budget exceeds maximum allowed limit of ₹{MAX_BUDGET_INR:,}.")


def validate_guest_count(guest_count: int) -> None:
    """Validate bounds on guest count."""
    if not isinstance(guest_count, int) or isinstance(guest_count, bool):
        raise ValueError("Guest count must be a strict integer.")
    if guest_count < MIN_GUESTS or guest_count > MAX_GUESTS:
        raise ValueError(f"Guest count must be between {MIN_GUESTS} and {MAX_GUESTS}.")


def calculate_budget(
    total_budget: int,
    items: List[BudgetItem]
) -> BudgetCalculationResult:
    """Calculate budget breakdown from user's budget and items.

    Formula definition:
    - Estimated vs Actuals are kept strictly separate.
    - Total planned = sum(item.estimated_amount)
    - Total actual = sum(item.actual_amount for items where actual_amount is not None)
    - Total effective = sum(item.actual_amount if item.actual_amount is not None else item.estimated_amount)
    - Remaining budget = total_budget - total_effective
    - is_over_budget = remaining_budget < 0
    - over_budget_amount = max(0, -remaining_budget)
    - Never modifies total_budget.
    """
    validate_total_budget(total_budget)

    total_planned = 0
    total_actual = 0
    total_effective = 0

    category_map: Dict[str, Dict[str, int]] = {}

    for item in items:
        est = item.estimated_amount
        act = item.actual_amount

        total_planned += est
        if act is not None:
            total_actual += act
            effective = act
        else:
            effective = est
        total_effective += effective

        if item.category not in category_map:
            category_map[item.category] = {"planned": 0, "actual": 0, "effective": 0, "count": 0}
        category_map[item.category]["planned"] += est
        if act is not None:
            category_map[item.category]["actual"] += act
        category_map[item.category]["effective"] += effective
        category_map[item.category]["count"] += 1

    remaining_budget = total_budget - total_effective
    is_over_budget = remaining_budget < 0
    over_budget_amount = max(0, -remaining_budget)

    categories = [
        CategoryBreakdown(
            category=cat,
            planned_amount=data["planned"],
            actual_amount=data["actual"],
            effective_amount=data["effective"],
            item_count=data["count"]
        )
        for cat, data in sorted(category_map.items())
    ]

    return BudgetCalculationResult(
        total_budget=total_budget,
        total_planned=total_planned,
        total_actual=total_actual,
        total_effective=total_effective,
        remaining_budget=remaining_budget,
        is_over_budget=is_over_budget,
        over_budget_amount=over_budget_amount,
        categories=categories,
        items=items
    )


def scale_budget_items_for_guests(
    items: List[BudgetItem],
    old_guest_count: int,
    new_guest_count: int
) -> Tuple[List[BudgetItem], List[str], List[str]]:
    """Recalculate only per-guest item estimates using integer half-up scaling.

    Uses integer half-up formula: (2 * amount * new + old) // (2 * old).
    Never modifies user-entered actuals; returns a list of items with actuals to review.
    Raises ValueError if scaled estimate exceeds MAX_BUDGET_INR.
    Returns:
        (updated_items, changed_item_names, items_with_actuals_to_review)
    """
    validate_guest_count(old_guest_count)
    validate_guest_count(new_guest_count)

    if old_guest_count == new_guest_count:
        return [item.model_copy() for item in items], [], []

    updated_items: List[BudgetItem] = []
    changed_names: List[str] = []
    review_actuals: List[str] = []

    for item in items:
        if item.cost_basis == "per_guest":
            # Integer half-up scaling formula
            new_est = (2 * item.estimated_amount * new_guest_count + old_guest_count) // (2 * old_guest_count)
            if new_est > MAX_BUDGET_INR:
                raise ValueError(
                    f"Scaled estimate for '{item.name}' ({new_est}) exceeds maximum budget limit of ₹{MAX_BUDGET_INR:,}."
                )

            if new_est != item.estimated_amount:
                changed_names.append(item.name)

            if item.actual_amount is not None:
                review_actuals.append(item.name)

            # Never alter user-entered actuals!
            updated = item.model_copy(update={
                "estimated_amount": new_est,
                "actual_amount": item.actual_amount
            })
            updated_items.append(updated)
        else:
            # Fixed cost: untouched
            updated_items.append(item.model_copy())

    return updated_items, changed_names, review_actuals
