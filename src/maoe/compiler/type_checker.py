from __future__ import annotations

from maoe.models.capsule import SkillCapsule
from maoe.models.workflow import CompileIssue, GoalIR, WorkflowDAG
from maoe.registry import SkillRegistry


class StaticValidationError(ValueError):
    def __init__(self, issues: list[CompileIssue]) -> None:
        self.issues = issues
        super().__init__("; ".join(issue.message for issue in issues))


class WorkflowTypeChecker:
    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def validate(self, goal: GoalIR, dag: WorkflowDAG) -> list[CompileIssue]:
        issues: list[CompileIssue] = []
        lookup = dag.node_map()

        for node in dag.nodes:
            unknown = sorted(set(node.dependencies) - set(lookup))
            for dependency in unknown:
                issues.append(
                    CompileIssue(
                        code="unknown_dependency",
                        message=f"{node.id} depends on unknown node {dependency}",
                        node_id=node.id,
                    )
                )

        if issues:
            return issues

        try:
            layers = dag.layers()
        except ValueError:
            return [
                CompileIssue(
                    code="cycle",
                    message="workflow dependency graph contains a cycle",
                )
            ]

        available = set(goal.environment_capabilities)
        schemas: dict[str, str] = {}
        capsules: dict[str, SkillCapsule] = {}
        for node in dag.nodes:
            capsules[node.id] = self._registry.get(node.skill_id, node.skill_version)

        for layer in layers:
            layer_provides: list[tuple[str, str, str | None]] = []
            for node_id in layer:
                node = lookup[node_id]
                capsule = capsules[node_id]
                missing = sorted(set(node.requires) - available)
                for capability in missing:
                    issues.append(
                        CompileIssue(
                            code="capability_gap",
                            message=f"{node.id} requires unavailable capability {capability}",
                            node_id=node.id,
                            capability=capability,
                        )
                    )
                for capability in node.requires:
                    expected = capsule.capabilities.schemas.get(capability)
                    actual = schemas.get(capability)
                    if expected and actual and expected != actual:
                        issues.append(
                            CompileIssue(
                                code="schema_mismatch",
                                message=(
                                    f"{node.id} expects {capability} schema {expected}, "
                                    f"but upstream provides {actual}"
                                ),
                                node_id=node.id,
                                capability=capability,
                            )
                        )
                for capability in node.provides:
                    layer_provides.append(
                        (node.id, capability, capsule.capabilities.schemas.get(capability))
                    )

            issues.extend(self._resource_conflicts(layer, lookup))
            for _, capability, schema in layer_provides:
                available.add(capability)
                if schema:
                    schemas[capability] = schema

        for deliverable in goal.deliverables:
            if deliverable not in available:
                issues.append(
                    CompileIssue(
                        code="missing_deliverable",
                        message=f"workflow does not produce required deliverable {deliverable}",
                        capability=deliverable,
                    )
                )
                continue
            producers = [node for node in dag.nodes if deliverable in node.provides]
            if producers and not any(node.validators for node in producers):
                issues.append(
                    CompileIssue(
                        code="missing_validator",
                        message=f"deliverable {deliverable} has no validator",
                        capability=deliverable,
                    )
                )

        total_cost = sum(node.expected_cost for node in dag.nodes)
        total_tokens = sum(node.expected_tokens for node in dag.nodes)
        if total_cost > goal.constraints.budget:
            issues.append(
                CompileIssue(
                    code="cost_budget_exceeded",
                    message=(
                        f"estimated cost {total_cost:.6f} exceeds budget "
                        f"{goal.constraints.budget:.6f}"
                    ),
                )
            )
        if total_tokens > goal.constraints.token_budget:
            issues.append(
                CompileIssue(
                    code="token_budget_exceeded",
                    message=(
                        f"estimated tokens {total_tokens} exceed budget "
                        f"{goal.constraints.token_budget}"
                    ),
                )
            )
        for node in dag.nodes:
            capsule = capsules[node.id]
            if capsule.risk.level > goal.constraints.allowed_risk:
                issues.append(
                    CompileIssue(
                        code="risk_not_allowed",
                        message=f"{node.id} risk exceeds allowed level",
                        node_id=node.id,
                    )
                )
            if capsule.effects.network == "write" and not goal.constraints.network_write:
                issues.append(
                    CompileIssue(
                        code="permission_conflict",
                        message=f"{node.id} requires network write permission",
                        node_id=node.id,
                    )
                )
            if capsule.effects.filesystem == "write" and "filesystem.write" not in available:
                issues.append(
                    CompileIssue(
                        code="permission_conflict",
                        message=f"{node.id} requires filesystem.write",
                        node_id=node.id,
                    )
                )
        return issues

    @staticmethod
    def _resource_conflicts(layer: list[str], lookup: dict) -> list[CompileIssue]:
        issues: list[CompileIssue] = []
        for index, left_id in enumerate(layer):
            left = lookup[left_id]
            for right_id in layer[index + 1 :]:
                right = lookup[right_id]
                left_writes = set(left.writes)
                right_writes = set(right.writes)
                overlap = left_writes & right_writes
                wildcard = (
                    "*" in left_writes and bool(right_writes)
                ) or ("*" in right_writes and bool(left_writes))
                if overlap or wildcard:
                    resources = sorted(overlap) or ["*"]
                    issues.append(
                        CompileIssue(
                            code="resource_conflict",
                            message=(
                                f"parallel nodes {left_id} and {right_id} write shared resources "
                                f"{resources}"
                            ),
                        )
                    )
        return issues
