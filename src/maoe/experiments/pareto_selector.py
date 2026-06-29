from __future__ import annotations

from pydantic import BaseModel, Field

from maoe.experiments.evaluator import CandidateEvaluation
from maoe.models.workflow import GoalConstraints, GoalQuality, WorkflowVariant


class ParetoSelection(BaseModel):
    recommended_workflow_id: str
    frontier_workflow_ids: list[str]
    rejected: dict[str, list[str]] = Field(default_factory=dict)
    reason: str


class ParetoSelector:
    def select(
        self,
        evaluations: list[CandidateEvaluation],
        constraints: GoalConstraints,
        quality: GoalQuality,
        preferred_variant: WorkflowVariant = WorkflowVariant.BALANCED,
    ) -> ParetoSelection:
        if not evaluations:
            raise ValueError("at least one candidate evaluation is required")

        feasible: list[CandidateEvaluation] = []
        rejected: dict[str, list[str]] = {}
        for evaluation in evaluations:
            reasons = self._constraint_failures(evaluation, constraints, quality)
            if reasons:
                rejected[evaluation.workflow_id] = reasons
            else:
                feasible.append(evaluation)
        if not feasible:
            raise ValueError("no candidate satisfies hard constraints")

        frontier = [
            candidate
            for candidate in feasible
            if not any(
                self._dominates(other, candidate)
                for other in feasible
                if other.workflow_id != candidate.workflow_id
            )
        ]
        preferred = next(
            (candidate for candidate in frontier if candidate.variant == preferred_variant),
            None,
        )
        recommended = preferred or max(
            frontier,
            key=lambda item: (
                item.quality,
                item.reliability,
                -item.cost,
                -item.latency_seconds,
                -item.risk.value,
            ),
        )
        return ParetoSelection(
            recommended_workflow_id=recommended.workflow_id,
            frontier_workflow_ids=sorted(item.workflow_id for item in frontier),
            rejected=rejected,
            reason=(
                f"selected {recommended.variant.value} from {len(frontier)} Pareto-optimal "
                "candidate(s) after hard-constraint filtering"
            ),
        )

    @staticmethod
    def _constraint_failures(
        evaluation: CandidateEvaluation,
        constraints: GoalConstraints,
        quality: GoalQuality,
    ) -> list[str]:
        failures: list[str] = []
        if not evaluation.passed:
            failures.append("quality gate failed")
        if evaluation.cost > constraints.budget:
            failures.append("cost budget exceeded")
        if evaluation.latency_seconds > constraints.deadline_seconds:
            failures.append("deadline exceeded")
        if evaluation.quality < quality.minimum_score:
            failures.append("minimum quality not met")
        if evaluation.risk > constraints.allowed_risk:
            failures.append("allowed risk exceeded")
        return failures

    @staticmethod
    def _dominates(left: CandidateEvaluation, right: CandidateEvaluation) -> bool:
        no_worse = (
            left.quality >= right.quality
            and left.reliability >= right.reliability
            and left.cost <= right.cost
            and left.latency_seconds <= right.latency_seconds
            and left.risk <= right.risk
        )
        strictly_better = (
            left.quality > right.quality
            or left.reliability > right.reliability
            or left.cost < right.cost
            or left.latency_seconds < right.latency_seconds
            or left.risk < right.risk
        )
        return no_worse and strictly_better
