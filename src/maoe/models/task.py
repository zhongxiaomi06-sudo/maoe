from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class SubTask(BaseModel):
    id: str
    description: str
    dependencies: list[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    complexity_score: float | None = None
    complexity_level: str | None = None
    assigned_model: str | None = None
    assigned_tier: str | None = None
    token_budget: int | None = None
    output: str | None = None
    quality_pass: bool | None = None
    attempts: int = 0
    max_attempts: int = 3
    error: str | None = None
    escalation_count: int = 0


class Task(BaseModel):
    id: str
    description: str
    subtasks: list[SubTask] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: TaskStatus = TaskStatus.PENDING
    total_cost: float = 0.0
    total_tokens: int = 0


class TaskGraph(BaseModel):
    task: Task
    adjacency: dict[str, list[str]] = Field(default_factory=dict)

    def add_subtask(self, subtask: SubTask) -> None:
        self.task.subtasks.append(subtask)
        self.adjacency[subtask.id] = list(subtask.dependencies)

    def get_execution_order(self) -> list[list[SubTask]]:
        deps = {s.id: set(s.dependencies) for s in self.task.subtasks}
        remaining = {s.id for s in self.task.subtasks}
        lookup = {s.id: s for s in self.task.subtasks}
        layers: list[list[SubTask]] = []

        while remaining:
            ready = [lookup[n] for n in remaining if not deps[n]]
            if not ready:
                msg = "Circular dependency detected in task graph"
                raise ValueError(msg)
            layers.append(ready)
            ready_ids = {s.id for s in ready}
            remaining -= ready_ids
            for s in remaining:
                deps[s] -= ready_ids

        return layers

    def get_dependents(self, subtask_id: str) -> list[str]:
        return [s.id for s in self.task.subtasks if subtask_id in s.dependencies]
