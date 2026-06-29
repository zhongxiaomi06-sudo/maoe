from __future__ import annotations

from maoe.models.capsule import CertificationLevel
from maoe.models.workflow import CapabilityEdge, CapabilityGraph, CapabilityNode, GoalIR
from maoe.registry import SkillRegistry


class CapabilityPlanner:
    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def plan(self, goal: GoalIR) -> CapabilityGraph:
        nodes: dict[str, CapabilityNode] = {}
        edges: set[tuple[str, str, str | None]] = set()
        environment = set(goal.environment_capabilities)

        def visit(capability: str, required_by: str, stack: tuple[str, ...]) -> None:
            if capability in stack:
                return
            node = nodes.setdefault(
                capability,
                CapabilityNode(
                    id=f"cap-{capability}",
                    capability=capability,
                    satisfied_by_environment=capability in environment,
                ),
            )
            if required_by not in node.required_by:
                node.required_by.append(required_by)
            if capability in environment:
                return

            matches = self._registry.search(
                capability,
                language=goal.language,
                task_type=goal.task_type,
                available_capabilities=environment,
                minimum_certification=CertificationLevel.VERIFIED,
            )
            if not matches:
                return
            capsule = self._registry.get(matches[0].skill_id, matches[0].version)
            for requirement in capsule.capabilities.requires:
                visit(requirement, capability, (*stack, capability))
                edges.add((requirement, capability, capsule.id))

        for output in goal.deliverables:
            visit(output, "goal", ())

        return CapabilityGraph(
            nodes=sorted(nodes.values(), key=lambda item: item.capability),
            edges=[
                CapabilityEdge(source=source, target=target, skill_id=skill_id)
                for source, target, skill_id in sorted(edges)
            ],
            required_outputs=list(goal.deliverables),
        )
