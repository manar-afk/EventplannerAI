"""Pure Python budget engine for EventPilot AI.

Enforces integer rupee arithmetic, separate estimates vs actuals,
guest-count scaling, and over-budget checks with zero floating-point drift.
No I/O or network operations.
"""

from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field

MIN_GUESTS = 1
MAX_GUESTS = 10_000
MIN_BUDGET_INR = 1_000
MAX_BUDGET_INR = 100_000_000  # 10 Crore INR limit to prevent absurd values


class BudgetItem(BaseModel):
    id: str
    name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    cost_basis: str = Field(..., pattern="^(per_guest|fixed)$")
    estimated_amount: int = Field(..., ge=0, le=MAX_BUDGET_INR)
    actual_amount: Optional[int] = Field(None, ge=0, le=MAX_BUDGET_INR)
    notes: Optional[str] = Field(default="", max_length=300)


class CategoryBreakdown(BaseModel):
    category: str
    planned_amount: int
    actual_amount: int
    item_count: int


class BudgetCalculationResult(BaseModel):
    total_budget: int
    total_planned: int
    total_actual: int
    total_effective: int
    remaining_budget: int
    is_over_budget: bool
    over_budget_amount: int
    categories: List[CategoryBreakdown]
    items: List[BudgetItem]


def validate_budget_inputs(total_budget: int, guest_count: int) -> None:
    """Validate constraints on total budget and guest count."""
    if not isinstance(total_budget, int) or isinstance(total_budget, bool):
        raise ValueError("Total budget must be an integer.")
    if not isinstance(guest_count, int) or isinstance(guest_count, bool):
        raise ValueError("Guest count must be an integer.")
    if total_budget < MIN_BUDGET_INR:
        raise ValueError(f"Total budget must be at least ₹{MIN_BUDGET_INR:,}.")
    if total_budget > MAX_BUDGET_INR:
        raise ValueError(f"Total budget exceeds maximum allowed limit of ₹{MAX_BUDGET_INR:,}.")
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
    - If total_effective > total_budget OR total_planned > total_budget, flagged as over-budget.
    - Never modifies total_budget.
    """
    if not isinstance(total_budget, int) or isinstance(total_budget, bool):
        raise ValueError("Total budget must be an integer.")
    if total_budget < 0 or total_budget > MAX_BUDGET_INR:
        raise ValueError(f"Invalid budget: {total_budget}. Must be between 0 and {MAX_BUDGET_INR}.")

    total_planned = 0
    total_actual = 0
    total_effective = 0

    category_map: Dict[str, Dict[str, int]] = {}

    for item in items:
        est = item.estimated_amount
        act = item.actual_amount

        if not isinstance(est, int) or est < 0:
            raise ValueError(f"Item '{item.name}' has invalid estimated amount: {est}")
        if act is not None and (not isinstance(act, int) or act < 0):
            raise ValueError(f"Item '{item.name}' has invalid actual amount: {act}")

        total_planned += est
        if act is not None:
            total_actual += act
            effective = act
        else:
            effective = est
        total_effective += effective

        if item.category not in category_map:
            category_map[item.category] = {"planned": 0, "actual": 0, "count": 0}
        category_map[item.category]["planned"] += est
        if act is not None:
            category_map[item.category]["actual"] += act
        category_map[item.category]["count"] += 1

    remaining_budget = total_budget - total_effective
    is_over_budget = total_planned > total_budget or total_effective > total_budget
    over_budget_amount = max(0, max(total_planned, total_effective) - total_budget)

    categories = [
        CategoryBreakdown(
            category=cat,
            planned_amount=data["planned"],
            actual_amount=data["actual"],
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
) -> Tuple[List[BudgetItem], List[str]]:
    """Recalculate only per-guest items when guest count changes.

    Fixed items are completely untouched.
    Returns:
        (updated_items, changed_item_names)
    """
    validate_budget_inputs(MIN_BUDGET_INR, old_guest_count)
    validate_budget_inputs(MIN_BUDGET_INR, new_guest_count)

    if old_guest_count == new_guest_count:
        return [item.model_copy() for item in items], []

    updated_items: List[BudgetItem] = []
    changed_names: List[str] = []

    for item in items:
        if item.cost_basis == "per_guest":
            # Compute per-guest unit cost using integer math
            # Round to nearest integer rupee
            unit_cost = item.estimated_amount / old_guest_count
            new_est = int(round(unit_cost * new_guest_count))
            new_est = min(new_est, MAX_BUDGET_INR)

            new_actual = None
            if item.actual_amount is not None:
                actual_unit = item.actual_amount / old_guest_count
                new_actual = min(int(round(actual_unit * new_guest_count)), MAX_BUDGET_INR)

            updated = item.model_copy(update={
                "estimated_amount": new_est,
                "actual_amount": new_actual
            })
            updated_items.append(updated)
            changed_names.append(item.name)
        else:
            # Fixed cost: untouched
            updated_items.append(item.model_copy())

    return updated_items, changed_names
