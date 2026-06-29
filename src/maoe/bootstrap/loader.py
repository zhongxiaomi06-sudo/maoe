from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class LoadedContextItem:
    path: str
    sha256: str
    reason: str
    loaded_at: str


@dataclass
class BootstrapContext:
    run_id: str
    root: Path
    manifest: dict[str, Any]
    loaded_context: list[LoadedContextItem] = field(default_factory=list)


class BootstrapLoader:
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or self._discover_root()

    def load(self) -> BootstrapContext:
        manifest = self._load_manifest()
        self._validate_manifest(manifest)
        loaded_context: list[LoadedContextItem] = [
            self._record(".maoe/manifest.yaml", "registry")
        ]

        for item in manifest.get("core_files", []):
            rel_path = item["path"]
            reason = item.get("reason", "mandatory")
            loaded_context.append(self._record(rel_path, reason))

        run_id = f"run-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
        return BootstrapContext(
            run_id=run_id,
            root=self._root,
            manifest=manifest,
            loaded_context=loaded_context,
        )

    def _discover_root(self) -> Path:
        current = Path.cwd().resolve()
        for candidate in [current, *current.parents]:
            if (candidate / ".maoe" / "manifest.yaml").exists():
                return candidate
        return current

    def _load_manifest(self) -> dict[str, Any]:
        manifest_path = self._root / ".maoe" / "manifest.yaml"
        with manifest_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError("manifest.yaml must contain a mapping")
        return data

    def _record(self, rel_path: str, reason: str) -> LoadedContextItem:
        abs_path = self._root / rel_path
        if not abs_path.is_file():
            raise FileNotFoundError(abs_path)
        digest = sha256(abs_path.read_bytes()).hexdigest()
        return LoadedContextItem(
            path=rel_path,
            sha256=digest,
            reason=reason,
            loaded_at=datetime.now(UTC).isoformat(),
        )

    def _validate_manifest(self, manifest: dict[str, Any]) -> None:
        required_groups = ("core_files", "agents", "skills", "commands", "hooks")
        for group in required_groups:
            entries = manifest.get(group)
            if not isinstance(entries, list) or not entries:
                raise ValueError(f"manifest group {group} must be a non-empty list")
            names: set[str] = set()
            for entry in entries:
                if not isinstance(entry, dict) or "path" not in entry:
                    raise ValueError(f"manifest group {group} contains an invalid entry")
                identity = str(entry.get("name", entry["path"]))
                if identity in names:
                    raise ValueError(f"duplicate {group} entry: {identity}")
                names.add(identity)
                path = (self._root / entry["path"]).resolve()
                if not path.is_relative_to(self._root) or not path.is_file():
                    raise ValueError(f"invalid {group} path: {entry['path']}")
