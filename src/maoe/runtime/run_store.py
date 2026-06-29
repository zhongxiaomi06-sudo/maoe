from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from maoe.models.workflow import CandidateWorkflow, CompileResult
from maoe.runtime.redaction import redact
from maoe.runtime.state import DecisionRecord, EventRecord, NodeRunState, RunPhase, RunState


class RunStore:
    FILENAMES = (
        "state.json",
        "decisions.jsonl",
        "events.jsonl",
        "context.json",
        "artifacts.json",
        "costs.json",
        "checkpoint.json",
        "report.json",
    )

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.runs_root = self.root / ".maoe" / "runs"

    def create(
        self,
        compiled: CompileResult,
        candidate: CandidateWorkflow,
        context: dict[str, Any] | None = None,
    ) -> RunState:
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        run_id = f"run-{stamp}-{uuid4().hex[:8]}"
        run_dir = self.runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        state = RunState(
            run_id=run_id,
            goal=compiled.goal_ir.goal,
            workflow_id=candidate.workflow_id,
            variant=candidate.variant.value,
            nodes={node.id: NodeRunState(node_id=node.id) for node in candidate.dag.nodes},
        )
        self.save_state(state)
        (run_dir / "events.jsonl").touch()
        (run_dir / "decisions.jsonl").touch()
        self._write_json(run_dir / "context.json", context or {})
        self._write_json(run_dir / "artifacts.json", {"artifacts": []})
        self._write_json(
            run_dir / "costs.json",
            {"total_tokens": 0, "total_cost": 0.0, "nodes": {}},
        )
        self._write_json(run_dir / "checkpoint.json", state.model_dump(mode="json"))
        self._write_json(run_dir / "report.json", {})
        return state

    def save_state(self, state: RunState) -> None:
        state.updated_at = datetime.now(UTC)
        self._write_json(self._run_dir(state.run_id) / "state.json", state.model_dump(mode="json"))

    def load_state(self, run_id: str) -> RunState:
        return RunState.model_validate(self._read_json(self._run_dir(run_id) / "state.json"))

    def checkpoint(self, state: RunState) -> None:
        self.save_state(state)
        self._write_json(
            self._run_dir(state.run_id) / "checkpoint.json",
            state.model_dump(mode="json"),
        )

    def resume(self, run_id: str) -> RunState:
        path = self._run_dir(run_id) / "checkpoint.json"
        state = RunState.model_validate(self._read_json(path))
        if state.phase in {RunPhase.COMPLETED, RunPhase.STOPPED}:
            return state
        state.phase = RunPhase.READY
        self.save_state(state)
        return state

    def append_event(self, event: EventRecord) -> None:
        self._append_jsonl(
            self._run_dir(event.run_id) / "events.jsonl",
            event.model_dump(mode="json"),
        )

    def append_decision(self, decision: DecisionRecord) -> None:
        self._append_jsonl(
            self._run_dir(decision.run_id) / "decisions.jsonl",
            decision.model_dump(mode="json"),
        )

    def read_events(self, run_id: str) -> list[dict[str, Any]]:
        return self._read_jsonl(self._run_dir(run_id) / "events.jsonl")

    def record_artifacts(self, run_id: str, artifacts: list[dict[str, Any]]) -> None:
        self._write_json(
            self._run_dir(run_id) / "artifacts.json",
            {"artifacts": artifacts},
        )

    def record_costs(self, state: RunState) -> None:
        self._write_json(
            self._run_dir(state.run_id) / "costs.json",
            {
                "total_tokens": state.total_tokens,
                "total_cost": state.total_cost,
                "nodes": {
                    node_id: {"tokens": node.tokens, "cost": node.cost}
                    for node_id, node in state.nodes.items()
                },
            },
        )

    def write_report(self, run_id: str, report: dict[str, Any]) -> None:
        self._write_json(self._run_dir(run_id) / "report.json", report)

    def read_report(self, run_id: str) -> dict[str, Any]:
        return self._read_json(self._run_dir(run_id) / "report.json")

    def _run_dir(self, run_id: str) -> Path:
        if not run_id.startswith("run-") or "/" in run_id or ".." in run_id:
            raise ValueError("invalid run id")
        path = (self.runs_root / run_id).resolve()
        if not path.is_relative_to(self.runs_root.resolve()):
            raise ValueError("run id escapes run directory")
        if not path.is_dir():
            raise FileNotFoundError(path)
        return path

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"expected JSON object in {path}")
        return data

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        clean = redact(payload)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(clean, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    @staticmethod
    def _append_jsonl(path: Path, payload: Any) -> None:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(redact(payload), sort_keys=True, ensure_ascii=True) + "\n")

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        return records
