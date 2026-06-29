from __future__ import annotations

from pydantic import BaseModel, Field

from maoe.models.capsule import RiskLevel
from maoe.models.workflow import CandidateWorkflow, WorkflowVariant


class CandidateEvaluation(BaseModel):
    workflow_id: str
    variant: WorkflowVariant
    quality: float = Field(ge=0.0, le=1.0)
    reliability: float = Field(ge=0.0, le=1.0)
    cost: float = Field(ge=0.0)
    latency_seconds: float = Field(ge=0.0)
    risk: RiskLevel
    passed: bool
    executed_node_ids: list[str] = Field(default_factory=list)
    reused_node_ids: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)

    @classmethod
    def from_prediction(cls, candidate: CandidateWorkflow) -> CandidateEvaluation:
        return cls(
            workflow_id=candidate.workflow_id,
            variant=candidate.variant,
            quality=candidate.predicted_quality,
            reliability=candidate.predicted_reliability,
            cost=candidate.estimated_cost,
            latency_seconds=candidate.estimated_seconds,
            risk=candidate.risk,
            passed=True,
            executed_node_ids=[node.id for node in candidate.dag.nodes],
            evidence=["static_validation_passed", "prediction_only"],
        )
