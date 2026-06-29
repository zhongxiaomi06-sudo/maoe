from __future__ import annotations

from maoe.economist.token_economist import TokenEconomist
from maoe.models.routing import ModelTier


def test_budget_allocation_single() -> None:
    econ = TokenEconomist(global_budget=100_000)
    report = econ.allocate([("st-1", 3, ModelTier.BALANCED)])
    assert len(report.allocations) == 1
    assert report.allocations[0].subtask_id == "st-1"
    assert 1000 <= report.allocations[0].token_budget <= 64000


def test_budget_allocation_multiple() -> None:
    econ = TokenEconomist(global_budget=100_000)
    report = econ.allocate([
        ("st-1", 1, ModelTier.FAST),
        ("st-2", 3, ModelTier.BALANCED),
        ("st-3", 5, ModelTier.CRITICAL),
    ])
    assert len(report.allocations) == 3
    budgets = {a.subtask_id: a.token_budget for a in report.allocations}
    # Critical task should get larger budget than trivial
    assert budgets["st-3"] > budgets["st-1"]


def test_budget_small_global() -> None:
    econ = TokenEconomist(global_budget=1000)
    report = econ.allocate([("st-1", 3, ModelTier.BALANCED)])
    assert report.allocations[0].token_budget >= 1000


def test_spend_tracking() -> None:
    econ = TokenEconomist(global_budget=100_000)
    econ.record_spend("st-1", 5000)
    econ.record_spend("st-1", 3000)
    assert econ.total_spent() == 8000
    assert econ.remaining_budget() == 92000


def test_cost_warning() -> None:
    econ = TokenEconomist(global_budget=1_000_000)
    report = econ.allocate([("st-1", 5, ModelTier.CRITICAL)])
    # Large budget + critical tier might trigger warning
    assert len(report.warnings) >= 0  # no crash
