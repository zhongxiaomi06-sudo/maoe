from __future__ import annotations

from enum import IntEnum

from pydantic import BaseModel, Field


class ComplexityLevel(IntEnum):
    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    CRITICAL = 5


class ComplexityScore(BaseModel):
    level: ComplexityLevel
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    factors: dict[str, float] = Field(default_factory=dict)

    @property
    def label(self) -> str:
        return self.level.name.lower()
