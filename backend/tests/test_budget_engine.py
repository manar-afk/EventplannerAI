"""Unit tests for pure Python budget engine."""

import pytest
from pydantic import ValidationError
from backend.app.budget_engine import (
    BudgetItem,
    calculate_budget,
    scale_budget_items_for_guests,
    validate_total_budget,
    validate_guest_count,
    MIN_GUESTS,
    MAX_GUESTS,
    MIN_BUDGET_INR,
    MAX_BUDGET_INR
)
from backend.app.rule_based_planner import largest_remainder_allocation


def test_budget_engine_basic_calculation():
    """Verify total planned, actual, effective, remaining balance and over_budget agreement."""
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
            actual_amount=None
        )
    ]
    result = calculate_budget(total_budget=100000, items=items)

    assert result.total_budget == 100000
    assert result.total_planned == 80000
    assert result.total_actual == 48000
    assert result.total_effective == 78000
    assert result.remaining_budget == 22000
    assert result.is_over_budget is False
    assert result.is_over_budget == (result.remaining_budget < 0)
    assert result.over_budget_amount == 0


def test_budget_engine_over_budget_scenario():
    """Requirement: is_over_budget == (remaining < 0) and over_budget_amount == -remaining."""
    items = [
        BudgetItem(
            id="1",
            name="Grand Venue",
            category="Venue",
            cost_basis="fixed",
            estimated_amount=700000,
            actual_amount=None
        ),
        BudgetItem(
            id="2",
            name="Catering",
            category="Food",
            cost_basis="per_guest",
            estimated_amount=500000,
            actual_amount=None
        )
    ]
    result = calculate_budget(total_budget=1000000, items=items)

    assert result.total_budget == 1000000
    assert result.remaining_budget == -200000
    assert result.is_over_budget is True
    assert result.is_over_budget == (result.remaining_budget < 0)
    assert result.over_budget_amount == 200000


def test_half_up_scaling_five_rupees():
    """Requirement: half-up scaling (5 rupees, 2 to 1 guests gives 3)."""
    item = BudgetItem(
        id="1",
        name="Small Item",
        category="Favors",
        cost_basis="per_guest",
        estimated_amount=5,
        actual_amount=None
    )
    scaled_items, changed, review = scale_budget_items_for_guests([item], 2, 1)
    assert scaled_items[0].estimated_amount == 3
    assert changed == ["Small Item"]
    assert review == []


def test_scaling_round_trip_250_to_300_to_250():
    """Requirement: 250 to 300 to 250 round trip."""
    item = BudgetItem(
        id="1",
        name="Catering Feast",
        category="Catering",
        cost_basis="per_guest",
        estimated_amount=250000,
        actual_amount=None
    )
    # 250 to 300
    scaled_items, _, _ = scale_budget_items_for_guests([item], 250, 300)
    assert scaled_items[0].estimated_amount == 300000

    # 300 back to 250
    back_items, _, _ = scale_budget_items_for_guests(scaled_items, 300, 250)
    assert back_items[0].estimated_amount == 250000


def test_scaling_never_changes_actuals_and_flags_review():
    """Requirement: actuals unchanged by scaling; returned in review list."""
    item = BudgetItem(
        id="1",
        name="Catering Buffet",
        category="Catering",
        cost_basis="per_guest",
        estimated_amount=100000,
        actual_amount=95000
    )
    scaled_items, changed, review = scale_budget_items_for_guests([item], 100, 200)
    assert scaled_items[0].estimated_amount == 200000
    assert scaled_items[0].actual_amount == 95000  # UNTOUCHED!
    assert "Catering Buffet" in review
    assert "Catering Buffet" in changed


def test_scaling_cap_overflow_raises():
    """Requirement: cap overflow raises ValueError."""
    item = BudgetItem(
        id="1",
        name="Huge Venue Setup",
        category="Catering",
        cost_basis="per_guest",
        estimated_amount=80_000_000,
        actual_amount=None
    )
    with pytest.raises(ValueError, match="exceeds maximum budget limit"):
        scale_budget_items_for_guests([item], 100, 200)


def test_rejects_non_strict_int_types():
    """Requirement: '1000' and 1000.5 rejected."""
    with pytest.raises(ValidationError):
        BudgetItem(
            id="1",
            name="Test",
            category="Venue",
            cost_basis="fixed",
            estimated_amount="1000"  # string rejected by StrictInt
        )

    with pytest.raises(ValidationError):
        BudgetItem(
            id="1",
            name="Test",
            category="Venue",
            cost_basis="fixed",
            estimated_amount=1000.5  # float rejected by StrictInt
        )

    with pytest.raises(ValueError):
        validate_total_budget(-500)

    with pytest.raises(ValueError):
        validate_total_budget(500)  # below MIN_BUDGET_INR

    with pytest.raises(ValueError):
        validate_guest_count(0)


def test_largest_remainder_split_exact_sum():
    """Requirement: split sums exactly to the budget."""
    weights = [24, 34, 14, 10, 5, 4, 3, 6]
    for budget in [1000, 1503, 100000, 2500000, 9999999]:
        allocation = largest_remainder_allocation(budget, weights)
        assert sum(allocation) == budget
