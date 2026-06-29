"""Benchmark runner — executes tasks through MAOE engine and collects metrics."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from loguru import logger

from benchmarks.metrics import (
    BenchmarkConfig,
    BenchmarkReport,
    BenchmarkRun,
    SubtaskMetric,
)
from benchmarks.suite import BenchmarkTask
from maoe.orchestrator import MAOEEngine


class BenchmarkRunner:
    """Runs benchmark tasks through the MAOE engine and collects metrics."""

    def __init__(self, config: BenchmarkConfig) -> None:
        self.config = config
        self._engine: MAOEEngine | None = None

    async def run_task(self, task: BenchmarkTask) -> BenchmarkRun:
        """Execute a single benchmark task through the MAOE engine."""
        run = BenchmarkRun(
            description=task.description,
            category=task.category,
            started_at=datetime.now(UTC),
            config_profile=self.config.profile,
        )

        # Build engine with profile overrides
        overrides: dict = {}
        if self.config.force_tier:
            overrides["force_model_tier"] = self.config.force_tier
        if self.config.max_attempts:
            overrides["max_attempts_per_task"] = self.config.max_attempts

        engine = MAOEEngine(**self._engine_kwargs())
        self._engine = engine

        start = time.monotonic()
        try:
            result = await engine.run(task.description)
            run.finished_at = datetime.now(UTC)
            run.duration_seconds = time.monotonic() - start

            run.subtask_count = result.subtask_count
            run.completed_count = result.completed_count
            run.failed_count = result.failed_count
            run.total_cost = result.total_cost
            run.total_tokens = result.total_tokens
            run.status = result.status

            # Extract per-subtask metrics
            for sr in result.subtask_results:
                sm = SubtaskMetric(
                    subtask_id=sr["id"],
                    description=sr["description"][:80],
                    complexity_level=sr.get("complexity", ""),
                    assigned_model=sr.get("model", ""),
                    assigned_tier=sr.get("tier", ""),
                    attempts=sr.get("attempts", 0),
                    escalation_count=sr.get("escalation_count", 0),
                    quality_score=sr.get("quality_score"),
                    quality_passed=sr.get("quality_passed", True),
                    status=sr.get("status", ""),
                )
                run.subtask_metrics.append(sm)
                run.total_attempts += sm.attempts
                if sm.attempts > 1:
                    run.escalation_count += 1
                if sm.quality_score is not None and sm.quality_score < 1.0:
                    run.quality_failures += 1

            run.estimated_cost = self._compute_estimated_cost(task)

        except Exception as exc:
            run.finished_at = datetime.now(UTC)
            run.duration_seconds = time.monotonic() - start
            run.status = "error"
            run.error = str(exc)
            logger.error("Benchmark task failed: {}", exc)

        finally:
            await engine.close()

        return run

    async def run_suite(
        self,
        tasks: list[BenchmarkTask],
    ) -> BenchmarkReport:
        """Run a full benchmark suite across all tasks."""
        report = BenchmarkReport(
            generated_at=datetime.now(UTC).isoformat(),
            profiles=[self.config],
        )

        logger.info(
            "Benchmark suite starting | profile={} | tasks={}",
            self.config.label,
            len(tasks),
        )

        for task in tasks:
            logger.info("  Running task: {} ({})", task.id, task.description[:50])
            run = await self.run_task(task)
            report.add_result(self.config.profile, task.description, task.category, run)

            if run.status == "completed":
                logger.info(
                    "    -> status={} cost=${:.6f} tokens={} duration={:.1f}s",
                    run.status,
                    run.total_cost,
                    run.total_tokens,
                    run.duration_seconds,
                )
                if run.subtask_count > task.max_subtasks:
                    logger.warning(
                        "    -> over-decomposed: {} subtasks (max {})",
                        run.subtask_count,
                        task.max_subtasks,
                    )
            else:
                logger.warning("    -> status={} error={}", run.status, run.error)

        return report

    def _engine_kwargs(self) -> dict:
        """Build engine constructor kwargs from config profile."""
        kwargs: dict = {}
        if self.config.max_concurrent:
            # Override settings before engine init
            pass  # Configured via settings env
        return kwargs

    @staticmethod
    def _compute_estimated_cost(task: BenchmarkTask) -> float:
        """Rough cost estimate based on task complexity."""
        base = len(task.description) / 1000 * 0.002
        return round(base, 6)
