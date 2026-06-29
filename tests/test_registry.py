from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from maoe.models.capsule import (
    CapabilityContract,
    CertificationLevel,
    QualitySpec,
    RiskSpec,
    SkillCapsule,
)
from maoe.registry import SkillRegistry

ROOT = Path(__file__).resolve().parent.parent


def test_registry_discovers_verified_capsules() -> None:
    registry = SkillRegistry.discover(ROOT)
    assert len(registry.all()) == 12
    assert all(
        capsule.certification >= CertificationLevel.VERIFIED
        for capsule in registry.all()
    )


def test_registry_search_explains_matches_and_rejections() -> None:
    registry = SkillRegistry.discover(ROOT)
    matches = registry.search("test.report", language="python", include_rejected=True)
    accepted = [match for match in matches if match.accepted]
    rejected = [match for match in matches if not match.accepted]
    assert {match.skill_id for match in accepted} == {
        "python.pytest-runner",
        "python.tdd-composite",
    }
    assert all(match.reasons for match in accepted)
    assert any(
        "does not provide test.report" in reason
        for match in rejected
        for reason in match.reasons
    )


def test_registry_rejects_duplicate_capsule() -> None:
    registry = SkillRegistry.discover(ROOT)
    capsule = registry.get("python.pytest-runner")
    with pytest.raises(ValueError, match="duplicate"):
        registry.register(capsule)


def test_capsule_requires_rollback_for_medium_risk() -> None:
    with pytest.raises(ValidationError, match="rollback"):
        SkillCapsule(
            id="test.medium-risk",
            version="1.0.0",
            description="A test capsule",
            capabilities=CapabilityContract(provides=["test.output"]),
            risk=RiskSpec(level="medium"),
            quality=QualitySpec(validators=["output_valid"]),
        )
