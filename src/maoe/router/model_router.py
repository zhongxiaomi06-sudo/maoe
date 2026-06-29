from __future__ import annotations

from loguru import logger

from maoe.models.complexity import ComplexityLevel
from maoe.models.routing import (
    DEFAULT_MODELS,
    TIER_ORDER,
    ModelCapability,
    ModelTier,
    RoutingDecision,
)

COMPLEXITY_TO_TIER: dict[ComplexityLevel, ModelTier] = {
    ComplexityLevel.TRIVIAL: ModelTier.FAST,
    ComplexityLevel.SIMPLE: ModelTier.FAST,
    ComplexityLevel.MODERATE: ModelTier.BALANCED,
    ComplexityLevel.COMPLEX: ModelTier.POWERFUL,
    ComplexityLevel.CRITICAL: ModelTier.CRITICAL,
}


def _tier_index(tier: ModelTier) -> int:
    return TIER_ORDER.index(tier)


def _next_tier(current: ModelTier) -> ModelTier | None:
    idx = _tier_index(current)
    if idx + 1 < len(TIER_ORDER):
        return TIER_ORDER[idx + 1]
    return None


class ModelRouter:
    def __init__(self, models: list[ModelCapability] | None = None) -> None:
        self._models = models or DEFAULT_MODELS
        self._model_by_tier: dict[ModelTier, ModelCapability] = {
            m.tier: m for m in self._models
        }

    def route(
        self,
        subtask_id: str,
        complexity_level: ComplexityLevel,
        estimated_input: int = 1000,
        estimated_output: int = 2000,
        force_tier: ModelTier | None = None,
    ) -> RoutingDecision:
        tier = force_tier or COMPLEXITY_TO_TIER.get(complexity_level, ModelTier.BALANCED)
        model_cap = self._model_by_tier.get(tier, self._model_by_tier[ModelTier.BALANCED])

        cost = (
            (estimated_input / 1000 * model_cap.cost_per_1k_input)
            + (estimated_output / 1000 * model_cap.cost_per_1k_output)
        )

        logger.debug(
            "Routed {} -> {} (tier={}, est_cost=${:.6f})",
            subtask_id,
            model_cap.name,
            tier,
            cost,
        )

        return RoutingDecision(
            subtask_id=subtask_id,
            assigned_model=model_cap.name,
            assigned_tier=tier,
            estimated_input_tokens=estimated_input,
            estimated_output_tokens=estimated_output,
            estimated_cost=cost,
            reason=f"Complexity {complexity_level.name} mapped to tier {tier}",
        )

    def escalate(
        self,
        current_decision: RoutingDecision,
    ) -> RoutingDecision | None:
        current_tier = current_decision.assigned_tier
        next_tier = _next_tier(current_tier)
        if next_tier is None:
            return None

        model_cap = self._model_by_tier.get(next_tier)
        if model_cap is None:
            return None

        cost = (
            (current_decision.estimated_input_tokens / 1000 * model_cap.cost_per_1k_input)
            + (current_decision.estimated_output_tokens / 1000 * model_cap.cost_per_1k_output)
        )

        return RoutingDecision(
            subtask_id=current_decision.subtask_id,
            assigned_model=model_cap.name,
            assigned_tier=next_tier,
            estimated_input_tokens=current_decision.estimated_input_tokens,
            estimated_output_tokens=current_decision.estimated_output_tokens,
            estimated_cost=cost,
            reason=f"Escalated from {current_tier} to {next_tier} after failure",
        )
