from __future__ import annotations

import asyncio
import json
import sys

import click
from loguru import logger

from maoe.config import settings
from maoe.orchestrator import MAOEEngine

_BENCHMARKS_AVAILABLE = False
_CONFIG_PROFILES: dict | None = None
_BENCHMARK_TASKS: list = []
_GET_TASK_BY_ID: object = None
_BENCHMARK_RUNNER: type | None = None
_REPORT_GENERATOR: type | None = None

try:
    import sys as _sys
    from pathlib import Path as _Path

    _project_root = _Path(__file__).resolve().parent.parent.parent
    if str(_project_root) not in _sys.path:
        _sys.path.insert(0, str(_project_root))

    from benchmarks.metrics import CONFIG_PROFILES as _CP
    from benchmarks.metrics import ConfigProfile
    from benchmarks.report import ReportGenerator
    from benchmarks.runner import BenchmarkRunner
    from benchmarks.suite import BENCHMARK_TASKS as _BT
    from benchmarks.suite import get_task_by_id

    _BENCHMARKS_AVAILABLE = True
    _CONFIG_PROFILES = _CP
    _BENCHMARK_TASKS = _BT
    _GET_TASK_BY_ID = get_task_by_id
    _BENCHMARK_RUNNER = BenchmarkRunner
    _REPORT_GENERATOR = ReportGenerator
except ImportError:
    pass


def _setup_logging(verbose: bool) -> None:
    level = "DEBUG" if verbose else settings.log_level
    logger.remove()
    logger.add(sys.stderr, format=settings.log_format, level=level, colorize=True)


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("description")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def run(description: str, verbose: bool, json_output: bool) -> None:
    """Execute a task through the MAOE engine."""
    _setup_logging(verbose)
    logger.info("MAOE v{} starting", "0.1.0")

    async def _run() -> None:
        engine = MAOEEngine()
        try:
            result = await engine.run(description)
            if json_output:
                click.echo(result.model_dump_json(indent=2))
            else:
                click.echo(f"\n{'='*60}")
                click.echo(f"Task: {result.description}")
                click.echo(f"Status: {result.status}")
                click.echo(f"Sub-tasks: {result.subtask_count} total, "
                           f"{result.completed_count} completed, "
                           f"{result.failed_count} failed")
                click.echo(f"Total cost: ${result.total_cost:.6f}")
                click.echo(f"Total tokens: {result.total_tokens}")
                click.echo(f"{'='*60}\n")
                for r in result.subtask_results:
                    status_icon = "✓" if r["status"] == "completed" else "✗"
                    click.echo(
                        f"  {status_icon} {r['id']}: {r['description'][:60]}"
                        f" [{r['model']}] ({r['complexity']})"
                    )
        finally:
            await engine.close()

    asyncio.run(_run())


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def config(verbose: bool) -> None:
    """Show current MAOE configuration."""
    _setup_logging(verbose)
    click.echo(json.dumps({
        "api_base_url": settings.api_base_url,
        "default_model": settings.default_model,
        "max_concurrent_tasks": settings.max_concurrent_tasks,
        "default_token_budget": settings.default_token_budget,
        "max_attempts_per_task": settings.max_attempts_per_task,
        "log_level": settings.log_level,
        "api_key_configured": bool(settings.api_key),
    }, indent=2))


if _BENCHMARKS_AVAILABLE:
    from benchmarks.metrics import ConfigProfile

    @cli.command()
    @click.option(
        "--profile", "-p",
        type=click.Choice([p.value for p in ConfigProfile]),
        default="default",
        help="Benchmark profile to run",
    )
    @click.option(
        "--task", "-t",
        default=None,
        help="Run a single task by ID (omit to run full suite)",
    )
    @click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
    @click.option("--output", "-o", default="benchmarks/results", help="Output directory")
    def benchmark(profile: str, task: str | None, verbose: bool, output: str) -> None:
        """Run the MAOE benchmark suite."""
        _setup_logging(verbose)

        config = _CONFIG_PROFILES[ConfigProfile(profile)]  # type: ignore[index]
        runner = _BENCHMARK_RUNNER(config)  # type: ignore[misc]

        if task:
            t = _GET_TASK_BY_ID(task)  # type: ignore[misc]
            if t is None:
                click.echo(f"Unknown task: {task}", err=True)
                raise click.Abort
            tasks = [t]
        else:
            tasks = _BENCHMARK_TASKS  # type: ignore[assignment]

        click.echo(f"Benchmark: {config.label}")
        click.echo(f"  Profile: {config.description}")
        click.echo(f"  Tasks:   {len(tasks)}")
        click.echo()

        async def _run() -> None:
            report = await runner.run_suite(tasks)
            gen = _REPORT_GENERATOR(report, output_dir=output)  # type: ignore[misc]
            json_path, md_path = gen.save()
            click.echo("\nReports written:")
            click.echo(f"  JSON: {json_path}")
            click.echo(f"  MD:   {md_path}")
            click.echo(f"\n{gen.to_markdown()}")

        asyncio.run(_run())


if __name__ == "__main__":
    cli()
