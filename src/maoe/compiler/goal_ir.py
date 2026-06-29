from __future__ import annotations

from maoe.models.capsule import RiskLevel
from maoe.models.workflow import GoalConstraints, GoalIR, GoalQuality

DEFAULT_ENVIRONMENT = [
    "requirement.raw",
    "source.python",
    "filesystem.read",
    "filesystem.write",
    "shell.pytest",
    "shell.ruff",
    "shell.bandit",
]


class GoalLowerer:
    """Deterministic goal lowering for the Python engineering MVP."""

    def lower(
        self,
        goal: str,
        *,
        budget: float = 0.5,
        token_budget: int = 100_000,
        deadline_seconds: float = 900.0,
        minimum_quality: float = 0.75,
        allowed_risk: RiskLevel = RiskLevel.MEDIUM,
    ) -> GoalIR:
        normalized = goal.lower()
        task_type = self._task_type(normalized)
        deliverables = ["source.modified", "test.report"]
        criteria = ["implementation matches the requested behavior", "all tests pass"]

        security_terms = ("security", "auth", "jwt", "permission", "安全", "鉴权", "权限", "登录")
        if any(term in normalized for term in security_terms):
            deliverables.append("security.report")
            criteria.append("no high-severity security findings")

        if any(term in normalized for term in ("document", "readme", "文档")):
            deliverables.append("docs.updated")
            criteria.append("documentation reflects the implemented behavior")

        return GoalIR(
            goal=goal,
            deliverables=deliverables,
            constraints=GoalConstraints(
                budget=budget,
                token_budget=token_budget,
                deadline_seconds=deadline_seconds,
                allowed_risk=allowed_risk,
            ),
            quality=GoalQuality(
                minimum_score=minimum_quality,
                security_high_findings=0 if "security.report" in deliverables else None,
            ),
            environment_capabilities=DEFAULT_ENVIRONMENT,
            language="python",
            task_type=task_type,
            acceptance_criteria=criteria,
        )

    @staticmethod
    def _task_type(goal: str) -> str:
        if any(term in goal for term in ("bug", "fix", "修复", "故障")):
            return "bugfix"
        if any(term in goal for term in ("refactor", "重构")):
            return "refactor"
        return "feature"
