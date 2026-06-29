"""Benchmark metric models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class TaskCategory(StrEnum):
    """Categories of benchmark tasks."""

    CODE_GENERATION = "code_generation"
    LOGIC_REASONING = "logic_reasoning"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TEST_WRITING = "test_writing"
    ANALYSIS = "analysis"
    PLANNING = "planning"


class ConfigProfile(StrEnum):
    """Predefined benchmark profiles for model tier configuration."""

    FAST_ONLY = "fast_only"
    BALANCED_ONLY = "balanced_only"
    DEFAULT = "default"
    AGGRESSIVE_ESCALATION = "aggressive_escalation"
    CONSERVATIVE = "conservative"


@dataclass
class BenchmarkConfig:
    """Configuration for a single benchmark profile."""

    profile: ConfigProfile
    label: str
    description: str
    # Model tier overrides (None = use default routing)
    force_tier: str | None = None  # "fast", "balanced", "powerful", "critical"
    max_attempts: int = 3
    max_concurrent: int = 5
    token_budget: int = 100_000
    # Quality gate settings
    quality_model: str = "gpt-4o-mini"
    # Enable/disable features for ablation
    enable_escalation: bool = True
    enable_quality_gate: bool = True


# Predefined configuration profiles
CONFIG_PROFILES: dict[ConfigProfile, BenchmarkConfig] = {
    ConfigProfile.DEFAULT: BenchmarkConfig(
        profile=ConfigProfile.DEFAULT,
        label="Default",
        description="Standard MAOE configuration with all features enabled",
    ),
    ConfigProfile.FAST_ONLY: BenchmarkConfig(
        profile=ConfigProfile.FAST_ONLY,
        label="Fast Only",
        description="All subtasks forced to gpt-4o-mini (fast tier)",
        force_tier="fast",
        max_attempts=1,
    ),
    ConfigProfile.BALANCED_ONLY: BenchmarkConfig(
        profile=ConfigProfile.BALANCED_ONLY,
        label="Balanced Only",
        description="All subtasks forced to gpt-4o (balanced tier)",
        force_tier="balanced",
    ),
    ConfigProfile.AGGRESSIVE_ESCALATION: BenchmarkConfig(
        profile=ConfigProfile.AGGRESSIVE_ESCALATION,
        label="Aggressive Escalation",
        description="Start with fast tier, escalate aggressively on failure",
        force_tier="fast",
        max_attempts=5,
    ),
    ConfigProfile.CONSERVATIVE: BenchmarkConfig(
        profile=ConfigProfile.CONSERVATIVE,
        label="Conservative",
        description="No quality gate, single attempt per subtask",
        enable_quality_gate=False,
        enable_escalation=False,
        max_attempts=1,
    ),
}


@dataclass
class SubtaskMetric:
    """Metrics for a single subtask execution."""

    subtask_id: str
    description: str
    complexity_level: str
    assigned_model: str
    assigned_tier: str
    attempts: int
    escalation_count: int
    quality_score: float | None
    quality_passed: bool
    status: str
    estimated_cost: float = 0.0


@dataclass
class BenchmarkRun:
    """Metrics collected from a single MAOE engine run."""

    # Task info
    description: str
    category: TaskCategory | None = None

    # Timing
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    duration_seconds: float = 0.0

    # Results
    subtask_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    escalation_count: int = 0
    total_attempts: int = 0
    quality_failures: int = 0

    # Cost
    total_cost: float = 0.0
    total_tokens: int = 0
    estimated_cost: float = 0.0

    # Per-subtask detail
    subtask_metrics: list[SubtaskMetric] = field(default_factory=list)

    # Config used
    config_profile: ConfigProfile = ConfigProfile.DEFAULT

    # Raw engine result
    status: str = ""
    error: str | None = None


@dataclass
class BenchmarkResult:
    """Aggregated result across multiple runs of the same task."""

    task_description: str
    task_category: TaskCategory | None
    runs: list[BenchmarkRun] = field(default_factory=list)

    def add_run(self, run: BenchmarkRun) -> None:
        self.runs.append(run)

    @property
    def success_rate(self) -> float:
        if not self.runs:
            return 0.0
        successes = sum(1 for r in self.runs if r.status == "completed" and r.failed_count == 0)
        return successes / len(self.runs)

    @property
    def avg_cost(self) -> float:
        if not self.runs:
            return 0.0
        return sum(r.total_cost for r in self.runs) / len(self.runs)

    @property
    def avg_tokens(self) -> float:
        if not self.runs:
            return 0.0
        return sum(r.total_tokens for r in self.runs) / len(self.runs)

    @property
    def avg_duration(self) -> float:
        if not self.runs:
            return 0.0
        return sum(r.duration_seconds for r in self.runs) / len(self.runs)

    @property
    def avg_escalations(self) -> float:
        if not self.runs:
            return 0.0
        return sum(r.escalation_count for r in self.runs) / len(self.runs)

    @property
    def total_cost_all(self) -> float:
        return sum(r.total_cost for r in self.runs)


@dataclass
class BenchmarkReport:
    """Complete benchmark report across all tasks and profiles."""

    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    maoe_version: str = "0.1.0"

    # Results: {profile_name: {task_description: BenchmarkResult}}
    results: dict[str, dict[str, BenchmarkResult]] = field(default_factory=dict)

    # Profiles used
    profiles: list[BenchmarkConfig] = field(default_factory=list)

    def add_result(
        self,
        profile: ConfigProfile,
        task_desc: str,
        task_category: TaskCategory | None,
        run: BenchmarkRun,
    ) -> None:
        profile_key = profile.value
        if profile_key not in self.results:
            self.results[profile_key] = {}
        if task_desc not in self.results[profile_key]:
            self.results[profile_key][task_desc] = BenchmarkResult(
                task_description=task_desc,
                task_category=task_category,
            )
        self.results[profile_key][task_desc].add_run(run)

    @property
    def total_cost(self) -> float:
        return sum(
            result.total_cost_all
            for profile_results in self.results.values()
            for result in profile_results.values()
        )
