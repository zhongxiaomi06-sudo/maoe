from __future__ import annotations

import re
from enum import IntEnum, StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class CertificationLevel(IntEnum):
    UNVERIFIED = 0
    COMPATIBLE = 1
    VERIFIED = 2
    TRUSTED = 3

    @classmethod
    def parse(cls, value: str | int | CertificationLevel) -> CertificationLevel:
        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return cls(value)
        return cls[value.upper()]


class SkillKind(StrEnum):
    KNOWLEDGE = "knowledge"
    TOOL = "tool"
    WORKFLOW = "workflow"


class RiskLevel(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def parse(cls, value: str | int | RiskLevel) -> RiskLevel:
        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return cls(value)
        return cls[value.upper()]


class CapabilityContract(BaseModel):
    provides: list[str] = Field(min_length=1)
    requires: list[str] = Field(default_factory=list)
    schemas: dict[str, str] = Field(default_factory=dict)

    @field_validator("provides", "requires")
    @classmethod
    def unique_capabilities(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("capability names cannot be empty")
        if len(values) != len(set(values)):
            raise ValueError("capability names must be unique")
        return values


class InputSpec(BaseModel):
    type: str
    required: bool = True


class EffectSpec(BaseModel):
    filesystem: str = "none"
    network: str = "none"
    external_side_effects: bool = False
    writes: list[str] = Field(default_factory=list)


class ResourceSpec(BaseModel):
    expected_tokens: int = Field(default=0, ge=0)
    expected_seconds: float = Field(default=0.0, ge=0.0)
    expected_cost: float = Field(default=0.0, ge=0.0)


class RiskSpec(BaseModel):
    level: RiskLevel = RiskLevel.LOW
    rollback: str | None = None

    @field_validator("level", mode="before")
    @classmethod
    def parse_level(cls, value: object) -> RiskLevel:
        return RiskLevel.parse(value)  # type: ignore[arg-type]


class QualitySpec(BaseModel):
    validators: list[str] = Field(min_length=1)
    minimum_score: float = Field(default=0.7, ge=0.0, le=1.0)


class SkillCapsule(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    version: str
    kind: SkillKind = SkillKind.WORKFLOW
    description: str = Field(min_length=1)
    capabilities: CapabilityContract
    inputs: dict[str, InputSpec] = Field(default_factory=dict)
    outputs: dict[str, InputSpec] = Field(default_factory=dict)
    preconditions: list[str] = Field(default_factory=list)
    effects: EffectSpec = Field(default_factory=EffectSpec)
    resources: ResourceSpec = Field(default_factory=ResourceSpec)
    risk: RiskSpec = Field(default_factory=RiskSpec)
    quality: QualitySpec
    certification: CertificationLevel = CertificationLevel.UNVERIFIED
    compatible_agents: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    task_types: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    context_cost: int = Field(default=0, ge=0)
    historical_success: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("version")
    @classmethod
    def valid_semver(cls, value: str) -> str:
        if not SEMVER_PATTERN.fullmatch(value):
            raise ValueError("version must be semantic version MAJOR.MINOR.PATCH")
        return value

    @field_validator("certification", mode="before")
    @classmethod
    def parse_certification(cls, value: object) -> CertificationLevel:
        return CertificationLevel.parse(value)  # type: ignore[arg-type]

    @model_validator(mode="after")
    def validate_contract(self) -> SkillCapsule:
        declared = set(self.capabilities.provides) | set(self.capabilities.requires)
        unknown_schemas = set(self.capabilities.schemas) - declared
        if unknown_schemas:
            raise ValueError(
                f"schemas reference undeclared capabilities: {sorted(unknown_schemas)}"
            )
        if self.risk.level >= RiskLevel.MEDIUM and not self.risk.rollback:
            raise ValueError("medium-or-higher risk skills require a rollback action")
        return self
