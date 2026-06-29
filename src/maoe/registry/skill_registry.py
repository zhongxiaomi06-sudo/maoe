from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from maoe.models.capsule import CertificationLevel, SkillCapsule


class SkillMatch(BaseModel):
    skill_id: str
    version: str
    accepted: bool
    score: float = 0.0
    matched_capabilities: list[str] = Field(default_factory=list)
    missing_environment: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class SkillRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self._capsules: dict[tuple[str, str], SkillCapsule] = {}
        self._revoked: set[tuple[str, str]] = set()

    @classmethod
    def discover(cls, root: Path) -> SkillRegistry:
        registry = cls(root)
        manifest_path = registry.root / ".maoe" / "manifest.yaml"
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        for entry in data.get("skills", []):
            skill_path = registry._safe_path(entry["path"])
            capsule_path = entry.get("capsule")
            if capsule_path:
                resolved_capsule = registry._safe_path(capsule_path)
            else:
                resolved_capsule = skill_path.with_name("capsule.yaml")
            registry.register_file(resolved_capsule)
        return registry

    def register_file(self, path: Path) -> SkillCapsule:
        resolved = path.resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError(f"skill capsule escapes project root: {path}")
        raw = yaml.safe_load(resolved.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"skill capsule must be a mapping: {resolved}")
        capsule = SkillCapsule.model_validate(raw)
        self.register(capsule)
        return capsule

    def register(self, capsule: SkillCapsule) -> None:
        key = (capsule.id, capsule.version)
        if key in self._capsules:
            raise ValueError(f"duplicate skill capsule: {capsule.id}@{capsule.version}")
        self._capsules[key] = capsule

    def revoke(self, skill_id: str, version: str) -> None:
        key = (skill_id, version)
        if key not in self._capsules:
            raise KeyError(f"unknown skill capsule: {skill_id}@{version}")
        self._revoked.add(key)

    def get(self, skill_id: str, version: str | None = None) -> SkillCapsule:
        candidates = [
            capsule
            for key, capsule in self._capsules.items()
            if key not in self._revoked and capsule.id == skill_id
        ]
        if version is not None:
            candidates = [capsule for capsule in candidates if capsule.version == version]
        if not candidates:
            suffix = f"@{version}" if version else ""
            raise KeyError(f"unknown or revoked skill capsule: {skill_id}{suffix}")
        return max(candidates, key=lambda item: self._version_tuple(item.version))

    def all(self, minimum_certification: CertificationLevel | None = None) -> list[SkillCapsule]:
        capsules = [
            capsule
            for key, capsule in self._capsules.items()
            if key not in self._revoked
            and (minimum_certification is None or capsule.certification >= minimum_certification)
        ]
        return sorted(capsules, key=lambda item: (item.id, self._version_tuple(item.version)))

    def search(
        self,
        capability: str,
        *,
        language: str | None = None,
        task_type: str | None = None,
        agent: str | None = None,
        available_capabilities: set[str] | None = None,
        minimum_certification: CertificationLevel = CertificationLevel.VERIFIED,
        include_rejected: bool = False,
    ) -> list[SkillMatch]:
        results: list[SkillMatch] = []
        available = available_capabilities or set()
        for capsule in self.all():
            reasons: list[str] = []
            matched = [item for item in capsule.capabilities.provides if item == capability]
            if not matched:
                reasons.append(f"does not provide {capability}")
            if capsule.certification < minimum_certification:
                reasons.append(
                    f"certification {capsule.certification.name.lower()} is below "
                    f"{minimum_certification.name.lower()}"
                )
            if language and capsule.languages and language not in capsule.languages:
                reasons.append(f"language {language} is not supported")
            if task_type and capsule.task_types and task_type not in capsule.task_types:
                reasons.append(f"task type {task_type} is not supported")
            if agent and capsule.compatible_agents and agent not in capsule.compatible_agents:
                reasons.append(f"agent {agent} is not compatible")

            missing = sorted(set(capsule.capabilities.requires) - available)
            accepted = not reasons
            if accepted or include_rejected:
                results.append(
                    SkillMatch(
                        skill_id=capsule.id,
                        version=capsule.version,
                        accepted=accepted,
                        score=self._score(capsule, capability, available) if accepted else 0.0,
                        matched_capabilities=matched,
                        missing_environment=missing,
                        reasons=(
                            [
                                f"provides {capability}",
                                f"certification={capsule.certification.name.lower()}",
                                f"{len(missing)} prerequisite capabilities need binding",
                            ]
                            if accepted
                            else reasons
                        ),
                    )
                )
        return sorted(results, key=lambda item: (not item.accepted, -item.score, item.skill_id))

    def write_snapshot(self, path: Path | None = None) -> Path:
        destination = path or self.root / ".maoe" / "skill-registry.json"
        payload = {
            "schema_version": "1.0.0",
            "skills": [capsule.model_dump(mode="json") for capsule in self.all()],
            "revoked": [f"{skill_id}@{version}" for skill_id, version in sorted(self._revoked)],
        }
        destination.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return destination

    def _safe_path(self, relative: str) -> Path:
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"manifest path escapes project root: {relative}")
        if not path.is_file():
            raise FileNotFoundError(path)
        return path

    @staticmethod
    def _version_tuple(version: str) -> tuple[int, int, int]:
        major, minor, patch = version.split(".")
        return int(major), int(minor), int(patch)

    @staticmethod
    def _score(capsule: SkillCapsule, capability: str, available: set[str]) -> float:
        contract_match = 1.0 if capability in capsule.capabilities.provides else 0.0
        coverage = 1.0 / max(len(capsule.capabilities.provides), 1)
        required = set(capsule.capabilities.requires)
        environment_fit = len(required & available) / len(required) if required else 1.0
        normalized_cost = min(capsule.resources.expected_cost / 0.1, 1.0)
        normalized_risk = capsule.risk.level.value / 4.0
        score = (
            contract_match * 0.30
            + coverage * 0.20
            + capsule.historical_success * 0.15
            + capsule.quality.minimum_score * 0.15
            + environment_fit * 0.10
            - normalized_cost * 0.05
            - normalized_risk * 0.05
        )
        return round(max(score, 0.0), 6)
