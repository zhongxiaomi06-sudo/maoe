from __future__ import annotations

from pydantic import BaseModel

from maoe.experiments.evaluator import CandidateEvaluation
from maoe.models.workflow import CandidateWorkflow, GoalIR


class EarlyStopDecision(BaseModel):
    stop: bool
    reason: str


class EarlyStopper:
    def __init__(self, maximum_candidates: int = 3, minimum_gain_per_cost: float = 1.0) -> None:
        if not 1 <= maximum_candidates <= 3:
            raise ValueError("maximum_candidates must be between 1 and 3")
        self.maximum_candidates = maximum_candidates
        self.minimum_gain_per_cost = minimum_gain_per_cost

    def decide(
        self,
        goal: GoalIR,
        completed: list[CandidateEvaluation],
        remaining: list[CandidateWorkflow],
    ) -> EarlyStopDecision:
        if len(completed) >= self.maximum_candidates:
            return EarlyStopDecision(stop=True, reason="candidate limit reached")
        spent = sum(item.cost for item in completed)
        if spent >= goal.constraints.budget:
            return EarlyStopDecision(stop=True, reason="cost budget exhausted")
        if not remaining:
            return EarlyStopDecision(stop=True, reason="no candidates remain")

        passing = [
            item
            for item in completed
            if item.passed and item.quality >= goal.quality.minimum_score
        ]
        if not passing:
            return EarlyStopDecision(stop=False, reason="quality threshold has not been reached")

        best = max(passing, key=lambda item: item.quality)
        affordable = [
            item for item in remaining if spent + item.estimated_cost <= goal.constraints.budget
        ]
        if not affordable:
            return EarlyStopDecision(
                stop=True, reason="remaining candidates exceed residual budget"
            )
        gains = [
            max(candidate.predicted_quality - best.quality, 0.0)
            / max(candidate.estimated_cost, 1e-9)
            for candidate in affordable
        ]
        if max(gains, default=0.0) < self.minimum_gain_per_cost:
            return EarlyStopDecision(
                stop=True,
                reason="expected quality gain is lower than incremental cost threshold",
            )
        return EarlyStopDecision(
            stop=False, reason="a remaining candidate has useful expected gain"
        )
