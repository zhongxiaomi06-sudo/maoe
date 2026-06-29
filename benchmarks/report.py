"""Benchmark report generation — JSON and Markdown output."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from benchmarks.metrics import BenchmarkReport


class ReportGenerator:
    """Generates benchmark reports in JSON and Markdown formats."""

    def __init__(self, report: BenchmarkReport, output_dir: str | Path = "benchmarks/results") -> None:
        self.report = report
        self.output_dir = Path(output_dir)

    def to_json(self, path: str | Path | None = None) -> str:
        """Export report as a JSON string. Optionally write to file."""
        data = self._serialize()
        text = json.dumps(data, indent=2, ensure_ascii=False)
        if path:
            dest = Path(path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
        return text

    def to_markdown(self) -> str:
        """Generate a human-readable Markdown report."""
        lines: list[str] = []
        lines.append("# MAOE Benchmark Report")
        lines.append("")
        lines.append(f"**Generated**: {self.report.generated_at}")
        lines.append(f"**MAOE Version**: {self.report.maoe_version}")
        lines.append(f"**Profiles Tested**: {len(self.report.profiles)}")
        lines.append("")

        # Summary table
        lines.append("## Summary")
        lines.append("")
        lines.append("| Profile | Tasks | Success Rate | Avg Cost | Avg Tokens | Avg Duration | Total Cost |")
        lines.append("|---------|-------|-------------|----------|------------|-------------|------------|")

        for profile_config in self.report.profiles:
            pkey = profile_config.profile.value
            profile_results = self.report.results.get(pkey, {})
            if not profile_results:
                continue

            total_tasks = len(profile_results)
            successes = sum(
                1 for br in profile_results.values() if br.success_rate > 0
            )
            success_rate = f"{successes}/{total_tasks}"
            avg_cost = sum(br.avg_cost for br in profile_results.values()) / max(total_tasks, 1)
            avg_tokens = sum(br.avg_tokens for br in profile_results.values()) / max(total_tasks, 1)
            avg_dur = sum(br.avg_duration for br in profile_results.values()) / max(total_tasks, 1)
            total_cost = sum(br.total_cost_all for br in profile_results.values())

            lines.append(
                f"| {profile_config.label} | {total_tasks} | {success_rate} | "
                f"${avg_cost:.6f} | {avg_tokens:.0f} | {avg_dur:.1f}s | ${total_cost:.4f} |"
            )

        lines.append("")

        # Per-profile detail
        for profile_config in self.report.profiles:
            pkey = profile_config.profile.value
            profile_results = self.report.results.get(pkey, {})
            if not profile_results:
                continue

            lines.append(f"## Profile: {profile_config.label}")
            lines.append("")
            lines.append(f"_{profile_config.description}_")
            lines.append("")
            lines.append("| Task | Category | Status | Cost | Tokens | Duration | Escalations | Quality Fails |")
            lines.append("|------|----------|--------|------|--------|----------|-------------|---------------|")

            for task_desc, result in sorted(profile_results.items()):
                for run in result.runs:
                    cat = run.category.value if run.category else "-"
                    status = "✅" if run.status == "completed" and run.failed_count == 0 else "❌"
                    lines.append(
                        f"| {task_desc[:50]} | {cat} | {status} | "
                        f"${run.total_cost:.6f} | {run.total_tokens} | {run.duration_seconds:.1f}s | "
                        f"{run.escalation_count} | {run.quality_failures} |"
                    )

            lines.append("")

            # Per-task subtask detail
            lines.append("### Subtask Details")
            lines.append("")
            for task_desc, result in sorted(profile_results.items()):
                lines.append(f"**{task_desc[:60]}**  ")
                for run in result.runs:
                    if not run.subtask_metrics:
                        continue
                    lines.append("")
                    lines.append("| Subtask | Model | Tier | Complexity | Attempts | Quality | Status |")
                    lines.append("|---------|-------|------|------------|----------|---------|--------|")
                    for sm in run.subtask_metrics:
                        qual = f"{sm.quality_score}" if sm.quality_score is not None else "-"
                        lines.append(
                            f"| {sm.subtask_id} | {sm.assigned_model} | {sm.assigned_tier} | "
                            f"{sm.complexity_level} | {sm.attempts} | {qual} | {sm.status} |"
                        )
                lines.append("")

        return "\n".join(lines)

    def save(self, basename: str = "benchmark-report") -> tuple[Path, Path]:
        """Save both JSON and Markdown reports. Returns (json_path, md_path)."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        json_path = self.output_dir / f"{basename}-{ts}.json"
        md_path = self.output_dir / f"{basename}-{ts}.md"

        self.to_json(json_path)
        md_text = self.to_markdown()
        md_path.write_text(md_text, encoding="utf-8")

        return json_path, md_path

    def _serialize(self) -> dict:
        """Serialize report to a JSON-compatible dict."""
        profiles_data = []
        for pc in self.report.profiles:
            profiles_data.append({
                "profile": pc.profile.value,
                "label": pc.label,
                "description": pc.description,
                "force_tier": pc.force_tier,
                "max_attempts": pc.max_attempts,
                "enable_escalation": pc.enable_escalation,
                "enable_quality_gate": pc.enable_quality_gate,
            })

        results_data = {}
        for pkey, task_results in self.report.results.items():
            results_data[pkey] = {}
            for task_desc, result in task_results.items():
                runs_data = []
                for run in result.runs:
                    runs_data.append({
                        "description": run.description,
                        "category": run.category.value if run.category else None,
                        "status": run.status,
                        "duration_seconds": run.duration_seconds,
                        "subtask_count": run.subtask_count,
                        "completed_count": run.completed_count,
                        "failed_count": run.failed_count,
                        "total_cost": run.total_cost,
                        "total_tokens": run.total_tokens,
                        "escalation_count": run.escalation_count,
                        "total_attempts": run.total_attempts,
                        "quality_failures": run.quality_failures,
                        "error": run.error,
                        "subtask_metrics": [
                            {
                                "subtask_id": sm.subtask_id,
                                "complexity_level": sm.complexity_level,
                                "assigned_model": sm.assigned_model,
                                "assigned_tier": sm.assigned_tier,
                                "attempts": sm.attempts,
                                "quality_score": sm.quality_score,
                                "quality_passed": sm.quality_passed,
                                "status": sm.status,
                            }
                            for sm in run.subtask_metrics
                        ],
                    })
                results_data[pkey][task_desc] = {
                    "task_category": result.task_category.value if result.task_category else None,
                    "runs": runs_data,
                    "success_rate": result.success_rate,
                    "avg_cost": result.avg_cost,
                    "avg_tokens": result.avg_tokens,
                    "avg_duration": result.avg_duration,
                }

        return {
            "generated_at": self.report.generated_at,
            "maoe_version": self.report.maoe_version,
            "total_cost": self.report.total_cost,
            "profiles": profiles_data,
            "results": results_data,
        }
