from __future__ import annotations

from dataclasses import dataclass, field

from loguru import logger

from maoe.models.routing import ModelTier

COMPLEXITY_TOKEN_MULTIPLIER: dict[int, float] = {
    1: 0.3,
    2: 0.5,
    3: 1.0,
    4: 2.0,
    5: 4.0,
}

TIER_BUDGET_SHARE: dict[ModelTier, float] = {
    ModelTier.FAST: 0.1,
    ModelTier.BALANCED: 0.2,
    ModelTier.POWERFUL: 0.3,
    ModelTier.CRITICAL: 0.4,
}


@dataclass
class BudgetAllocation:
    subtask_id: str
    token_budget: int
    estimated_cost: float
    tier: ModelTier


@dataclass
class EconomistReport:
    allocations: list[BudgetAllocation] = field(default_factory=list)
    total_budget: int = 0
    total_estimated_cost: float = 0.0
    warnings: list[str] = field(default_factory=list)


class TokenEconomist:
    def __init__(self, global_budget: int = 100_000) -> None:
        self._global_budget = global_budget
        self._spent: dict[str, int] = {}

    def allocate(
        self,
        subtasks: list[tuple[str, int, ModelTier]],
    ) -> EconomistReport:
        report = EconomistReport(total_budget=self._global_budget)

        total_weight = 0.0
        weights: dict[str, float] = {}
        for sid, complexity_val, tier in subtasks:
            w = COMPLEXITY_TOKEN_MULTIPLIER.get(complexity_val, 1.0)
            w *= TIER_BUDGET_SHARE.get(tier, 0.25)
            weights[sid] = w
            total_weight += w

        for sid, complexity_val, tier in subtasks:
            share = weights[sid] / total_weight if total_weight > 0 else 1.0 / max(len(subtasks), 1)
            budget = int(self._global_budget * share)
            budget = max(1000, min(budget, 64000))

            cost = budget * TIER_BUDGET_SHARE.get(tier, 0.25) * 0.0001

            report.allocations.append(
                BudgetAllocation(
                    subtask_id=sid,
                    token_budget=budget,
                    estimated_cost=cost,
                    tier=tier,
                )
            )
            report.total_estimated_cost += cost

        logger.info(
            "Allocated budget across {} sub-tasks: total={}, est_cost=${:.4f}",
            len(subtasks),
            self._global_budget,
            report.total_estimated_cost,
        )

        if report.total_estimated_cost > 0.10:
            report.warnings.append(
                f"Estimated cost ${report.total_estimated_cost:.4f} exceeds $0.10 threshold"
            )

        return report

    def record_spend(self, subtask_id: str, tokens: int) -> None:
        self._spent[subtask_id] = self._spent.get(subtask_id, 0) + tokens

    def total_spent(self) -> int:
        return sum(self._spent.values())

    def remaining_budget(self) -> int:
        return max(0, self._global_budget - self.total_spent())
