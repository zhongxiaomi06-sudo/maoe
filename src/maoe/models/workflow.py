from __future__ import annotations

import json
from enum import StrEnum
from hashlib import sha256

from pydantic import BaseModel, Field

from maoe.models.capsule import RiskLevel


class WorkflowVariant(StrEnum):
    ECONOMY = "economy"
    BALANCED = "balanced"
    QUALITY = "quality"


class GoalConstraints(BaseModel):
    budget: float = Field(default=0.5, gt=0.0)
    token_budget: int = Field(default=100_000, gt=0)
    deadline_seconds: float = Field(default=900.0, gt=0.0)
    network_write: bool = False
    allowed_risk: RiskLevel = RiskLevel.MEDIUM


class GoalQuality(BaseModel):
    minimum_score: float = Field(default=0.75, ge=0.0, le=1.0)
    tests_pass: bool = True
    security_high_findings: int | None = Field(default=None, ge=0)


class GoalIR(BaseModel):
    goal: str = Field(min_length=1)
    deliverables: list[str] = Field(min_length=1)
    constraints: GoalConstraints = Field(default_factory=GoalConstraints)
    quality: GoalQuality = Field(default_factory=GoalQuality)
    environment_capabilities: list[str] = Field(default_factory=list)
    language: str = "python"
    task_type: str = "feature"
    acceptance_criteria: list[str] = Field(default_factory=list)

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode()).hexdigest()


class CapabilityNode(BaseModel):
    id: str
    capability: str
    required_by: list[str] = Field(default_factory=list)
    satisfied_by_environment: bool = False


class CapabilityEdge(BaseModel):
    source: str
    target: str
    skill_id: str | None = None


class CapabilityGraph(BaseModel):
    nodes: list[CapabilityNode] = Field(default_factory=list)
    edges: list[CapabilityEdge] = Field(default_factory=list)
    required_outputs: list[str] = Field(default_factory=list)


class WorkflowNode(BaseModel):
    id: str
    skill_id: str
    skill_version: str
    agent: str
    model_tier: str
    dependencies: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)
    provides: list[str] = Field(default_factory=list)
    validators: list[str] = Field(default_factory=list)
    rollback: str | None = None
    expected_tokens: int = 0
    expected_seconds: float = 0.0
    expected_cost: float = 0.0
    risk: RiskLevel = RiskLevel.LOW
    writes: list[str] = Field(default_factory=list)
    reusable: bool = True


class WorkflowDAG(BaseModel):
    nodes: list[WorkflowNode]

    def node_map(self) -> dict[str, WorkflowNode]:
        return {node.id: node for node in self.nodes}

    def layers(self) -> list[list[str]]:
        lookup = self.node_map()
        remaining = set(lookup)
        dependencies = {node.id: set(node.dependencies) for node in self.nodes}
        layers: list[list[str]] = []
        while remaining:
            ready = sorted(node_id for node_id in remaining if not dependencies[node_id])
            if not ready:
                raise ValueError("workflow contains a cycle")
            layers.append(ready)
            remaining -= set(ready)
            for node_id in remaining:
                dependencies[node_id] -= set(ready)
        return layers


class CandidateWorkflow(BaseModel):
    variant: WorkflowVariant
    workflow_id: str
    dag: WorkflowDAG
    estimated_cost: float
    estimated_tokens: int
    estimated_seconds: float
    predicted_quality: float
    predicted_reliability: float
    risk: RiskLevel
    risks: list[str] = Field(default_factory=list)
    shared_node_ids: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)


class CompileIssue(BaseModel):
    code: str
    message: str
    node_id: str | None = None
    capability: str | None = None


class CompileResult(BaseModel):
    goal_ir: GoalIR
    capability_graph: CapabilityGraph
    candidates: list[CandidateWorkflow]
    recommendation: WorkflowVariant
    issues: list[CompileIssue] = Field(default_factory=list)
    lock_digest: str

    def lock_payload(self) -> dict:
        return {
            "schema_version": "1.0.0",
            "goal_ir": self.goal_ir.model_dump(mode="json"),
            "capability_graph": self.capability_graph.model_dump(mode="json"),
            "candidates": [candidate.model_dump(mode="json") for candidate in self.candidates],
            "recommendation": self.recommendation.value,
            "issues": [issue.model_dump(mode="json") for issue in self.issues],
            "lock_digest": self.lock_digest,
        }
