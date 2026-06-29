from __future__ import annotations

import pytest

from maoe.models.complexity import ComplexityLevel
from maoe.models.routing import ModelTier
from maoe.router.model_router import ModelRouter


@pytest.fixture
def router() -> ModelRouter:
    return ModelRouter()


def test_route_trivial_to_fast(router: ModelRouter) -> None:
    d = router.route("st-1", ComplexityLevel.TRIVIAL)
    assert d.assigned_tier == ModelTier.FAST
    assert d.assigned_model == "gpt-4o-mini"


def test_route_simple_to_fast(router: ModelRouter) -> None:
    d = router.route("st-1", ComplexityLevel.SIMPLE)
    assert d.assigned_tier == ModelTier.FAST


def test_route_moderate_to_balanced(router: ModelRouter) -> None:
    d = router.route("st-1", ComplexityLevel.MODERATE)
    assert d.assigned_tier == ModelTier.BALANCED
    assert d.assigned_model == "gpt-4o"


def test_route_complex_to_powerful(router: ModelRouter) -> None:
    d = router.route("st-1", ComplexityLevel.COMPLEX)
    assert d.assigned_tier == ModelTier.POWERFUL
    assert d.assigned_model == "gpt-5"


def test_route_critical_to_critical(router: ModelRouter) -> None:
    d = router.route("st-1", ComplexityLevel.CRITICAL)
    assert d.assigned_tier == ModelTier.CRITICAL
    assert d.assigned_model == "gpt-5.5"


def test_escalation_chain(router: ModelRouter) -> None:
    d = router.route("st-1", ComplexityLevel.SIMPLE)
    assert d.assigned_tier == ModelTier.FAST

    e1 = router.escalate(d)
    assert e1 is not None
    assert e1.assigned_tier == ModelTier.BALANCED
    assert e1.assigned_model == "gpt-4o"

    e2 = router.escalate(e1)
    assert e2 is not None
    assert e2.assigned_tier == ModelTier.POWERFUL
    assert e2.assigned_model == "gpt-5"

    e3 = router.escalate(e2)
    assert e3 is not None
    assert e3.assigned_tier == ModelTier.CRITICAL
    assert e3.assigned_model == "gpt-5.5"

    e4 = router.escalate(e3)
    assert e4 is None


def test_route_cost_increases_with_complexity(router: ModelRouter) -> None:
    cheap = router.route("st-1", ComplexityLevel.TRIVIAL)
    expensive = router.route("st-1", ComplexityLevel.CRITICAL)
    assert cheap.estimated_cost < expensive.estimated_cost


def test_force_tier(router: ModelRouter) -> None:
    d = router.route("st-1", ComplexityLevel.TRIVIAL, force_tier=ModelTier.POWERFUL)
    assert d.assigned_tier == ModelTier.POWERFUL
    assert d.assigned_model == "gpt-5"
