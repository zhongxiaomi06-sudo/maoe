"""Predefined benchmark task definitions."""

from __future__ import annotations

from dataclasses import dataclass, field

from benchmarks.metrics import TaskCategory


@dataclass
class BenchmarkTask:
    """A single benchmark task definition."""

    description: str
    category: TaskCategory
    id: str
    tags: list[str] = field(default_factory=list)
    # Expected quality markers - strings the output should contain as a basic pass check
    expected_markers: list[str] = field(default_factory=list)
    # Minimum acceptable subtask count
    min_subtasks: int = 1
    # Maximum acceptable subtask count
    max_subtasks: int = 10


# ── Code Generation ───────────────────────────────────────────────────

TASK_VALIDATE_EMAIL = BenchmarkTask(
    id="code-email-validator",
    description="Create a Python function that validates email addresses",
    category=TaskCategory.CODE_GENERATION,
    tags=["python", "validation", "regex"],
    expected_markers=["validate_email", "def ", "return"],
    min_subtasks=3,
    max_subtasks=7,
)

TASK_FIBONACCI = BenchmarkTask(
    id="code-fibonacci",
    description="Create a Python function that generates the Fibonacci sequence up to n terms",
    category=TaskCategory.CODE_GENERATION,
    tags=["python", "algorithm"],
    expected_markers=["def fibonacci", "return"],
    min_subtasks=2,
    max_subtasks=5,
)

TASK_JSON_PARSER = BenchmarkTask(
    id="code-json-parser",
    description="Write a Python class that can parse a JSON string into a Python dictionary with error handling",
    category=TaskCategory.CODE_GENERATION,
    tags=["python", "parsing", "json"],
    expected_markers=["class ", "def parse", "json"],
    min_subtasks=3,
    max_subtasks=6,
)

# ── Logic / Reasoning ─────────────────────────────────────────────────

TASK_FIZZBUZZ = BenchmarkTask(
    id="logic-fizzbuzz",
    description="Write a Python program that prints numbers from 1 to 100, but for multiples of 3 print 'Fizz', for multiples of 5 print 'Buzz', and for multiples of both print 'FizzBuzz'",
    category=TaskCategory.LOGIC_REASONING,
    tags=["python", "logic"],
    expected_markers=["Fizz", "Buzz", "FizzBuzz"],
    min_subtasks=1,
    max_subtasks=4,
)

TASK_PRIME_CHECK = BenchmarkTask(
    id="logic-prime-check",
    description="Write a Python function to check if a given number is prime, optimized with early termination",
    category=TaskCategory.LOGIC_REASONING,
    tags=["python", "math", "optimization"],
    expected_markers=["def is_prime", "return"],
    min_subtasks=2,
    max_subtasks=5,
)

# ── Documentation ─────────────────────────────────────────────────────

TASK_DOCSTRING = BenchmarkTask(
    id="docs-function-docstring",
    description="Write comprehensive docstring documentation for a function that calculates the Levenshtein distance between two strings",
    category=TaskCategory.DOCUMENTATION,
    tags=["documentation", "docstring"],
    expected_markers=["Args:", "Returns:", "Example"],
    min_subtasks=2,
    max_subtasks=5,
)

# ── Test Writing ──────────────────────────────────────────────────────

TASK_TEST_CALCULATOR = BenchmarkTask(
    id="test-calculator",
    description="Write pytest unit tests for a Calculator class with add, subtract, multiply, and divide methods",
    category=TaskCategory.TEST_WRITING,
    tags=["python", "testing", "pytest"],
    expected_markers=["def test_", "assert"],
    min_subtasks=2,
    max_subtasks=5,
)

# ── Analysis ──────────────────────────────────────────────────────────

TASK_CODE_REVIEW = BenchmarkTask(
    id="analysis-code-review",
    description="Review the following Python code for bugs, style issues, and performance problems: def foo(l): return [x for x in l if x not in l]",
    category=TaskCategory.ANALYSIS,
    tags=["code-review", "analysis"],
    expected_markers=["bug", "issue"],
    min_subtasks=1,
    max_subtasks=4,
)

# ── Planning ──────────────────────────────────────────────────────────

TASK_DEPLOY_PLAN = BenchmarkTask(
    id="plan-deploy",
    description="Create a step-by-step deployment plan for a Python web application using Docker and AWS ECS, including CI/CD pipeline, health checks, and rollback strategy",
    category=TaskCategory.PLANNING,
    tags=["devops", "aws", "docker", "deployment"],
    expected_markers=["Docker", "ECS", "CI/CD", "rollback"],
    min_subtasks=3,
    max_subtasks=8,
)


# ── All tasks ─────────────────────────────────────────────────────────

BENCHMARK_TASKS: list[BenchmarkTask] = [
    TASK_VALIDATE_EMAIL,
    TASK_FIBONACCI,
    TASK_JSON_PARSER,
    TASK_FIZZBUZZ,
    TASK_PRIME_CHECK,
    TASK_DOCSTRING,
    TASK_TEST_CALCULATOR,
    TASK_CODE_REVIEW,
    TASK_DEPLOY_PLAN,
]


def get_task_by_id(task_id: str) -> BenchmarkTask | None:
    """Look up a benchmark task by its ID."""
    for task in BENCHMARK_TASKS:
        if task.id == task_id:
            return task
    return None


def get_tasks_by_category(category: TaskCategory) -> list[BenchmarkTask]:
    """Get all tasks in a given category."""
    return [t for t in BENCHMARK_TASKS if t.category == category]
