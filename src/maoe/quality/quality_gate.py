from __future__ import annotations

import json
from dataclasses import dataclass, field

from maoe.llm import LLMClient

QUALITY_PROMPT = """Evaluate whether the sub-task output meets requirements.

Sub-task description: {description}

Output to evaluate:
{output}

Respond in JSON format:
{{
  "pass": true/false,
  "score": 0.0-1.0,
  "reasoning": "Brief explanation",
  "issues": ["Issue 1", "Issue 2"]
}}

Criteria:
1. Is the output non-empty and substantial?
2. Does it directly address the sub-task description?
3. Is it technically sound and well-structured?
4. Does it provide actionable or complete results?"""

EXECUTE_PROMPT = """Execute the following sub-task and produce the output.

Sub-task: {description}
Context from dependencies:
{dep_context}

Produce the output directly. Be thorough and complete."""


@dataclass
class QualityVerdict:
    passed: bool
    score: float
    reasoning: str
    issues: list[str] = field(default_factory=list)


@dataclass
class SubtaskResult:
    subtask_id: str
    output: str
    quality: QualityVerdict
    attempts: int = 1
    model_used: str = ""


class QualityGate:
    def __init__(self, llm: LLMClient, model: str = "gpt-4o-mini") -> None:
        self._llm = llm
        self._model = model

    async def check(self, description: str, output: str) -> QualityVerdict:
        # Basic checks first
        if not output or len(output.strip()) < 10:
            return QualityVerdict(
                passed=False,
                score=0.0,
                reasoning="Output is empty or too short",
                issues=["Empty or minimal output"],
            )

        return await self._check_with_llm(description, output)

    async def _check_with_llm(self, description: str, output: str) -> QualityVerdict:
        prompt = QUALITY_PROMPT.format(description=description, output=output[:4000])
        resp = await self._llm.chat_json(
            model=self._model,
            messages=[
                {"role": "system", "content": "You are a strict quality gate."},
                {"role": "user", "content": prompt},
            ],
        )

        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            return QualityVerdict(
                passed=False,
                score=0.0,
                reasoning="Warning: could not parse LLM quality response",
                issues=["Quality response was not valid JSON"],
            )

        return QualityVerdict(
            passed=bool(data.get("pass", False)),
            score=min(1.0, max(0.0, float(data.get("score", 0.5)))),
            reasoning=data.get("reasoning", ""),
            issues=data.get("issues", []),
        )


class SubtaskExecutor:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def execute(
        self,
        description: str,
        model: str,
        dep_context: str = "",
        max_tokens: int = 16000,
    ) -> str:
        prompt = EXECUTE_PROMPT.format(
            description=description,
            dep_context=dep_context or "No prior context.",
        )
        resp = await self._llm.chat(
            model=model,
            messages=[
                {"role": "system", "content": "Execute the sub-task precisely."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
        )
        return resp.content
