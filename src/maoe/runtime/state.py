from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RunPhase(StrEnum):
    CREATED = "created"
    CONTEXT_LOADED = "context_loaded"
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    VERIFYING = "verifying"
    RETRYING = "retrying"
    ESCALATING = "escalating"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class NodePhase(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodeRunState(BaseModel):
    node_id: str
    phase: NodePhase = NodePhase.PENDING
    attempts: int = 0
    error: str | None = None
    error_fingerprint: str | None = None
    artifact_hashes: dict[str, str] = Field(default_factory=dict)
    tokens: int = 0
    cost: float = 0.0
    latency_seconds: float = 0.0
    quality_score: float = 0.0
    reused: bool = False


class RunState(BaseModel):
    run_id: str
    goal: str
    workflow_id: str
    variant: str
    phase: RunPhase = RunPhase.CREATED
    nodes: dict[str, NodeRunState] = Field(default_factory=dict)
    total_tokens: int = 0
    total_cost: float = 0.0
    elapsed_seconds: float = 0.0
    active_agents: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EventRecord(BaseModel):
    event_id: str
    sequence: int
    run_id: str
    event_type: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)


class DecisionRecord(BaseModel):
    decision_id: str
    sequence: int
    run_id: str
    action: str
    reason: str
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
