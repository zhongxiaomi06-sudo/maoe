from __future__ import annotations

from maoe.llm import LLMResponse
from maoe.quality.quality_gate import QualityGate, QualityVerdict


def test_empty_output_fails() -> None:
    verdict = QualityVerdict(
        passed=False,
        score=0.0,
        reasoning="Output is empty or too short",
        issues=["Empty or minimal output"],
    )
    assert not verdict.passed
    assert verdict.score == 0.0


def test_short_output_fails() -> None:
    v = QualityVerdict(
        passed=False,
        score=0.1,
        reasoning="Too short",
        issues=["Output too brief"],
    )
    assert not v.passed
    assert len(v.issues) == 1


def test_perfect_output_passes() -> None:
    v = QualityVerdict(
        passed=True,
        score=1.0,
        reasoning="All criteria met",
    )
    assert v.passed
    assert v.score == 1.0


def test_partial_output() -> None:
    v = QualityVerdict(
        passed=True,
        score=0.7,
        reasoning="Mostly meets requirements",
        issues=["Could be more detailed"],
    )
    assert v.passed
    assert v.score == 0.7


async def test_invalid_quality_json_does_not_pass() -> None:
    class InvalidJSONClient:
        async def chat_json(self, **_: object) -> LLMResponse:
            return LLMResponse(content="not-json", model="fake")

    gate = QualityGate(InvalidJSONClient())  # type: ignore[arg-type]
    verdict = await gate.check("produce a substantial answer", "a substantial output value")
    assert not verdict.passed
    assert verdict.score == 0.0
    assert "Warning" in verdict.reasoning
