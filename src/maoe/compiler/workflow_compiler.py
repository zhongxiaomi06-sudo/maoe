from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from maoe.compiler.capability_graph import CapabilityPlanner
from maoe.compiler.goal_ir import GoalLowerer
from maoe.compiler.type_checker import StaticValidationError, WorkflowTypeChecker
from maoe.models.capsule import CertificationLevel, RiskLevel, SkillCapsule
from maoe.models.workflow import (
    CandidateWorkflow,
    CompileIssue,
    CompileResult,
    GoalIR,
    WorkflowDAG,
    WorkflowNode,
    WorkflowVariant,
)
from maoe.registry import SkillRegistry

VARIANT_MODEL_TIERS = {
    WorkflowVariant.ECONOMY: "fast",
    WorkflowVariant.BALANCED: "balanced",
    WorkflowVariant.QUALITY: "powerful",
}

VARIANT_EXTRA_OUTPUTS = {
    WorkflowVariant.ECONOMY: [],
    WorkflowVariant.BALANCED: ["quality.report"],
    WorkflowVariant.QUALITY: ["quality.report", "review.report"],
}


class WorkflowCompiler:
    def __init__(self, root: Path, registry: SkillRegistry | None = None) -> None:
        self.root = root.resolve()
        self.registry = registry or SkillRegistry.discover(self.root)
        self.lowerer = GoalLowerer()
        self.planner = CapabilityPlanner(self.registry)
        self.checker = WorkflowTypeChecker(self.registry)

    def compile(self, goal: str | GoalIR, **goal_options: object) -> CompileResult:
        goal_ir = goal if isinstance(goal, GoalIR) else self.lowerer.lower(goal, **goal_options)
        capability_graph = self.planner.plan(goal_ir)
        candidates: list[CandidateWorkflow] = []

        for variant in WorkflowVariant:
            candidates.append(self._build_candidate(goal_ir, variant))

        shared = self._shared_nodes(candidates)
        candidates = [
            candidate.model_copy(update={"shared_node_ids": sorted(shared)})
            for candidate in candidates
        ]
        recommendation = self._recommend(goal_ir, candidates)

        unsigned = {
            "goal_ir": goal_ir.model_dump(mode="json"),
            "capability_graph": capability_graph.model_dump(mode="json"),
            "candidates": [candidate.model_dump(mode="json") for candidate in candidates],
            "recommendation": recommendation.value,
        }
        lock_digest = sha256(self._canonical(unsigned).encode()).hexdigest()
        return CompileResult(
            goal_ir=goal_ir,
            capability_graph=capability_graph,
            candidates=candidates,
            recommendation=recommendation,
            lock_digest=lock_digest,
        )

    def write_lockfile(self, result: CompileResult, path: Path | None = None) -> Path:
        destination = path or self.root / "workflow.lock.json"
        destination.write_text(
            json.dumps(result.lock_payload(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return destination

    def _build_candidate(self, goal: GoalIR, variant: WorkflowVariant) -> CandidateWorkflow:
        environment = set(goal.environment_capabilities)
        required_outputs = list(
            dict.fromkeys([*goal.deliverables, *VARIANT_EXTRA_OUTPUTS[variant]])
        )
        selected: dict[str, SkillCapsule] = {}
        capability_provider: dict[str, str] = {}

        def bind(capability: str, stack: tuple[str, ...]) -> None:
            if capability in environment or capability in capability_provider:
                return
            if capability in stack:
                raise StaticValidationError(
                    [
                        CompileIssue(
                            code="capability_cycle",
                            message=f"capability planning cycle detected at {capability}",
                            capability=capability,
                        )
                    ]
                )

            matches = self.registry.search(
                capability,
                language=goal.language,
                task_type=goal.task_type,
                available_capabilities=environment | set(capability_provider),
                minimum_certification=CertificationLevel.VERIFIED,
            )
            if not matches:
                raise StaticValidationError(
                    [
                        CompileIssue(
                            code="capability_gap",
                            message=f"no verified skill provides {capability}",
                            capability=capability,
                        )
                    ]
                )
            match = min(matches, key=lambda item: self._rank(item.skill_id, item.version, variant))
            capsule = self.registry.get(match.skill_id, match.version)
            selected[capsule.id] = capsule
            for provided in capsule.capabilities.provides:
                capability_provider.setdefault(provided, capsule.id)
            for requirement in capsule.capabilities.requires:
                bind(requirement, (*stack, capability))

        for output in required_outputs:
            bind(output, ())

        nodes: list[WorkflowNode] = []
        for skill_id, capsule in sorted(selected.items()):
            dependencies = sorted(
                {
                    capability_provider[requirement]
                    for requirement in capsule.capabilities.requires
                    if requirement not in environment
                    and capability_provider.get(requirement) != capsule.id
                }
            )
            nodes.append(
                WorkflowNode(
                    id=skill_id,
                    skill_id=skill_id,
                    skill_version=capsule.version,
                    agent=self._agent_for(capsule),
                    model_tier=VARIANT_MODEL_TIERS[variant],
                    dependencies=dependencies,
                    requires=capsule.capabilities.requires,
                    provides=capsule.capabilities.provides,
                    validators=capsule.quality.validators,
                    rollback=capsule.risk.rollback,
                    expected_tokens=capsule.resources.expected_tokens,
                    expected_seconds=capsule.resources.expected_seconds,
                    expected_cost=capsule.resources.expected_cost,
                    risk=capsule.risk.level,
                    writes=capsule.effects.writes,
                )
            )

        dag = WorkflowDAG(nodes=nodes)
        validation_goal = goal.model_copy(update={"deliverables": required_outputs})
        issues = self.checker.validate(validation_goal, dag)
        if issues:
            raise StaticValidationError(issues)

        total_cost = sum(node.expected_cost for node in nodes)
        total_tokens = sum(node.expected_tokens for node in nodes)
        layer_seconds = [
            max((dag.node_map()[node_id].expected_seconds for node_id in layer), default=0.0)
            for layer in dag.layers()
        ]
        expected_seconds = sum(layer_seconds)
        qualities = [selected[node.skill_id].quality.minimum_score for node in nodes]
        reliability = [selected[node.skill_id].historical_success for node in nodes]
        predicted_quality = min(qualities, default=0.0)
        predicted_reliability = min(reliability, default=0.0)
        risk = max((node.risk for node in nodes), default=RiskLevel.LOW)
        workflow_payload = {
            "goal": goal.fingerprint,
            "variant": variant.value,
            "dag": dag.model_dump(mode="json"),
        }
        workflow_digest = sha256(self._canonical(workflow_payload).encode()).hexdigest()
        workflow_id = f"wf-{variant.value}-{workflow_digest[:12]}"
        return CandidateWorkflow(
            variant=variant,
            workflow_id=workflow_id,
            dag=dag,
            estimated_cost=round(total_cost, 8),
            estimated_tokens=total_tokens,
            estimated_seconds=round(expected_seconds, 3),
            predicted_quality=round(predicted_quality, 4),
            predicted_reliability=round(predicted_reliability, 4),
            risk=risk,
            risks=[
                f"{node.skill_id} has {node.risk.name.lower()} risk"
                for node in nodes
                if node.risk >= RiskLevel.MEDIUM
            ],
            rationale=[
                f"variant={variant.value} uses {VARIANT_MODEL_TIERS[variant]} model tier",
                f"bound {len(nodes)} verified skills for {len(required_outputs)} outputs",
                f"static validation passed within ${goal.constraints.budget:.4f} budget",
            ],
        )

    def _rank(
        self,
        skill_id: str,
        version: str,
        variant: WorkflowVariant,
    ) -> tuple:
        capsule = self.registry.get(skill_id, version)
        if variant == WorkflowVariant.ECONOMY:
            return (
                capsule.resources.expected_cost,
                capsule.resources.expected_tokens,
                capsule.risk.level,
                -capsule.quality.minimum_score,
                capsule.id,
            )
        if variant == WorkflowVariant.QUALITY:
            return (
                -capsule.quality.minimum_score,
                -capsule.historical_success,
                capsule.risk.level,
                capsule.resources.expected_cost,
                capsule.id,
            )
        return (
            -(
                capsule.quality.minimum_score * 0.45
                + capsule.historical_success * 0.35
                - min(capsule.resources.expected_cost / 0.1, 1.0) * 0.20
            ),
            capsule.risk.level,
            capsule.id,
        )

    @staticmethod
    def _agent_for(capsule: SkillCapsule) -> str:
        return capsule.compatible_agents[0] if capsule.compatible_agents else "code-agent"

    @staticmethod
    def _shared_nodes(candidates: list[CandidateWorkflow]) -> set[str]:
        if not candidates:
            return set()
        signatures: list[dict[str, str]] = []
        for candidate in candidates:
            signatures.append(
                {
                    node.id: sha256(
                        json.dumps(
                            node.model_dump(mode="json", exclude={"model_tier"}),
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode()
                    ).hexdigest()
                    for node in candidate.dag.nodes
                }
            )
        common = set(signatures[0])
        for signature in signatures[1:]:
            common &= set(signature)
        return {
            node_id
            for node_id in common
            if len({signature[node_id] for signature in signatures}) == 1
        }

    @staticmethod
    def _recommend(goal: GoalIR, candidates: list[CandidateWorkflow]) -> WorkflowVariant:
        feasible = [
            candidate
            for candidate in candidates
            if candidate.estimated_cost <= goal.constraints.budget
            and candidate.estimated_tokens <= goal.constraints.token_budget
            and candidate.estimated_seconds <= goal.constraints.deadline_seconds
            and candidate.predicted_quality >= goal.quality.minimum_score
            and candidate.risk <= goal.constraints.allowed_risk
        ]
        for preferred in (
            WorkflowVariant.BALANCED,
            WorkflowVariant.ECONOMY,
            WorkflowVariant.QUALITY,
        ):
            if any(candidate.variant == preferred for candidate in feasible):
                return preferred
        return min(candidates, key=lambda item: item.estimated_cost).variant

    @staticmethod
    def _canonical(value: object) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
