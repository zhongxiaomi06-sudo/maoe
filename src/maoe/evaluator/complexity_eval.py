from __future__ import annotations

import json

from loguru import logger

from maoe.llm import LLMClient
from maoe.models.complexity import ComplexityLevel, ComplexityScore

COMPLEXITY_PROMPT = """Analyze the complexity of this sub-task.

Respond in JSON format:
{{"level": 1-5, "score": 0.0-1.0, "reasoning": "...",
  "factors": {{"scope": 0.0-1.0, "difficulty": 0.0-1.0,
               "dependencies": 0.0-1.0, "domain_knowledge": 0.0-1.0}}}}

Rules: level 1=trivial, 2=simple, 3=moderate, 4=complex, 5=critical.
Consider: scope, difficulty, dependencies, domain knowledge.

Sub-task: {description}"""


class ComplexityEval:
    def __init__(self, llm: LLMClient, model: str = "gpt-4o-mini") -> None:
        self._llm = llm
        self._model = model

    async def evaluate(self, description: str) -> ComplexityScore:
        return await self._evaluate_with_llm(description)

    async def _evaluate_with_llm(self, description: str) -> ComplexityScore:
        prompt = COMPLEXITY_PROMPT.format(description=description)
        resp = await self._llm.chat_json(
            model=self._model,
            messages=[
                {"role": "system", "content": "You are a complexity analysis engine."},
                {"role": "user", "content": prompt},
            ],
        )

        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse complexity JSON, using defaults")
            return ComplexityScore(
                level=ComplexityLevel.MODERATE,
                score=0.5,
                reasoning="Fallback: could not parse LLM response",
            )

        level_val = data.get("level", 3)
        if isinstance(level_val, int) and 1 <= level_val <= 5:
            level = ComplexityLevel(level_val)
        else:
            level = ComplexityLevel.MODERATE

        return ComplexityScore(
            level=level,
            score=min(1.0, max(0.0, data.get("score", 0.5))),
            reasoning=data.get("reasoning", ""),
            factors=data.get("factors", {}),
        )
