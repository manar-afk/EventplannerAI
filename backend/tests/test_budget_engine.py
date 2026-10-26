"""Unit tests for pure Python budget engine.

Verifies integer math, over-budget scenarios, separate estimates vs actuals,
guest-count scaling, and input validation without floats.
"""

import pytest
from backend.app.budget_engine import (
    BudgetItem,
    calculate_budget,
    scale_budget_items_for_guests,
    validate_budget_inputs,
    MIN_GUESTS,
    MAX_GUESTS,
    MIN_BUDGET_INR,
    MAX_BUDGET_INR
)


def test_budget_engine_basic_calculation():
    """Verify total planned, actual, effective, and remaining balance."""
    items = [
        BudgetItem(
            id="1",
            name="Catering",
            category="Food",
            cost_basis="per_guest",
            estimated_amount=50000,
            actual_amount=48000
        ),
        BudgetItem(
            id="2",
            name="Hall Rental",
            category="Venue",
            cost_basis="fixed",
            estimated_amount=30000,
            actual_amount=None  # Not entered yet -> uses estimate
        )
    ]
    # Total budget = 100,000 INR
    # Effective = 48,000 (actual) + 30,000 (estimate) = 78,000
    # Remaining = 100,000 - 78,000 = 22,000
    result = calculate_budget(total_budget=100000, items=items)

    assert result.total_budget == 100000
    assert result.total_planned == 80000
    assert result.total_actual == 48000
    assert result.total_effective == 78000
    assert result.remaining_budget == 22000
    assert result.is_over_budget is False
    assert result.over_budget_amount == 0


def test_budget_engine_over_budget_scenario():
    """Requirement: Explicitly cover over-budget scenario when estimates or actuals exceed total."""
    items = [
        BudgetItem(
            id="1",
            name="Grand Palace Venue",
            category="Venue",
            cost_basis="fixed",
            estimated_amount=600000,
            actual_amount=None
        ),
        BudgetItem(
            id="2",
            name="Luxury Catering",
            category="Food",
            cost_basis="per_guest",
            estimated_amount=500000,
            actual_amount=None
        )
    ]
    # Total budget is 1,000,000 INR, but items total 1,100,000 INR
    result = calculate_budget(total_budget=1000000, items=items)

    assert result.total_budget == 1000000  # Total budget is never altered
    assert result.total_planned == 1100000
    assert result.is_over_budget is True
    assert result.over_budget_amount == 100000
    assert result.remaining_budget == -100000


def test_budget_engine_guest_scaling_only_touches_per_guest_items():
    """Requirement: Guest count scaling recalculates ONLY per-guest items; fixed items untouched."""
    items = [
        BudgetItem(
            id="1",
            name="Per Head Dinner Buffet",
            category="Catering",
            cost_basis="per_guest",
            estimated_amount=100000,  # 100,000 for 100 guests = 1,000/head
            actual_amount=None
        ),
        BudgetItem(
            id="2",
            name="Banquet Hall Flat Fee",
            category="Venue",
            cost_basis="fixed",
            estimated_amount=50000,  # Flat fixed cost
            actual_amount=None
        ),
        BudgetItem(
            id="3",
            name="Return Gift Bags",
            category="Favors",
            cost_basis="per_guest",
            estimated_amount=20000,  # 20,000 for 100 guests = 200/head
            actual_amount=18000
        )
    ]

    # Double guests from 100 to 200
    updated_items, changed_names = scale_budget_items_for_guests(
        items=items,
        old_guest_count=100,
        new_guest_count=200
    )

    # Changed names should include both per_guest items, but NOT the fixed venue item
    assert "Per Head Dinner Buffet" in changed_names
    assert "Return Gift Bags" in changed_names
    assert "Banquet Hall Flat Fee" not in changed_names

    item_map = {item.name: item for item in updated_items}
    # 1. Scaled per-guest item
    assert item_map["Per Head Dinner Buffet"].estimated_amount == 200000
    # 2. Fixed item unchanged
    assert item_map["Banquet Hall Flat Fee"].estimated_amount == 50000
    # 3. Scaled with actual
    assert item_map["Return Gift Bags"].estimated_amount == 40000
    assert item_map["Return Gift Bags"].actual_amount == 36000


def test_budget_engine_rejects_invalid_inputs():
    """Requirement: Reject negatives, non-integers, and absurd values."""
    with pytest.raises(ValueError):
        validate_budget_inputs(total_budget=-500, guest_count=100)

    with pytest.raises(ValueError):
        validate_budget_inputs(total_budget=50000, guest_count=0)

    with pytest.raises(ValueError):
        validate_budget_inputs(total_budget=50000, guest_count=20000)

    with pytest.raises(ValueError):
        validate_budget_inputs(total_budget=MAX_BUDGET_INR + 10, guest_count=100)

    # Float rejection
    with pytest.raises(ValueError):
        calculate_budget(total_budget=50000.5, items=[])
