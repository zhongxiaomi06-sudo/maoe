from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, Field

from maoe.experiments.early_stopper import EarlyStopper
from maoe.experiments.evaluator import CandidateEvaluation
from maoe.experiments.pareto_selector import ParetoSelection, ParetoSelector
from maoe.models.workflow import CandidateWorkflow, CompileResult

EvaluationFunction = Callable[[CandidateWorkflow, set[str]], CandidateEvaluation]


class ExperimentResult(BaseModel):
    evaluations: list[CandidateEvaluation]
    selection: ParetoSelection
    stopped_early: bool = False
    stop_reason: str = ""
    reused_node_ids: list[str] = Field(default_factory=list)


class CandidateLab:
    def __init__(
        self,
        evaluator: EvaluationFunction | None = None,
        early_stopper: EarlyStopper | None = None,
        selector: ParetoSelector | None = None,
    ) -> None:
        self._evaluator = evaluator or self._prediction_evaluator
        self._early_stopper = early_stopper or EarlyStopper()
        self._selector = selector or ParetoSelector()

    def run(self, compiled: CompileResult) -> ExperimentResult:
        ordered = sorted(
            compiled.candidates,
            key=lambda item: (item.estimated_cost, item.variant.value),
        )
        completed: list[CandidateEvaluation] = []
        artifact_cache: set[str] = set()
        stopped_early = False
        stop_reason = ""

        for index, candidate in enumerate(ordered):
            evaluation = self._evaluator(candidate, artifact_cache)
            reused = sorted(set(candidate.shared_node_ids) & artifact_cache)
            evaluation = evaluation.model_copy(update={"reused_node_ids": reused})
            completed.append(evaluation)
            artifact_cache.update(candidate.shared_node_ids)

            decision = self._early_stopper.decide(
                compiled.goal_ir,
                completed,
                ordered[index + 1 :],
            )
            if decision.stop:
                stopped_early = index < len(ordered) - 1
                stop_reason = decision.reason
                break

        selection = self._selector.select(
            completed,
            compiled.goal_ir.constraints,
            compiled.goal_ir.quality,
            preferred_variant=compiled.recommendation,
        )
        return ExperimentResult(
            evaluations=completed,
            selection=selection,
            stopped_early=stopped_early,
            stop_reason=stop_reason,
            reused_node_ids=sorted(artifact_cache),
        )

    @staticmethod
    def _prediction_evaluator(
        candidate: CandidateWorkflow,
        _: set[str],
    ) -> CandidateEvaluation:
        return CandidateEvaluation.from_prediction(candidate)
