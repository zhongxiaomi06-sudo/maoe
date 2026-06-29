from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger

from maoe.config import settings


@dataclass
class LLMResponse:
    content: str
    model: str
    usage_input_tokens: int = 0
    usage_output_tokens: int = 0
    cost: float = 0.0
    finish_reason: str = ""


MODEL_LIMITS: dict[str, int] = {
    "gpt-4o-mini": 16384,
    "gpt-4o": 16384,
    "gpt-5": 65536,
    "gpt-5.5": 131072,
}

COST_PER_1K: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o": (0.0025, 0.01),
    "gpt-5": (0.01, 0.04),
    "gpt-5.5": (0.05, 0.15),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = COST_PER_1K.get(model, (0.001, 0.002))
    return (input_tokens / 1000 * rates[0]) + (output_tokens / 1000 * rates[1])


class LLMClient:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._input_tokens = 0
        self._output_tokens = 0
        self._cost = 0.0

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.api_base_url,
                timeout=httpx.Timeout(120.0),
            )
        return self._client

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        client = await self._get_client()
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            model_limit = MODEL_LIMITS.get(model, 16384)
            body["max_tokens"] = min(max_tokens, model_limit)
        if response_format is not None:
            body["response_format"] = response_format

        logger.debug("LLM request: model={} messages={}", model, len(messages))

        resp = await client.post(
            "/chat/completions",
            json=body,
            headers={"Authorization": f"Bearer {settings.api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        content = choice["message"]["content"] or ""
        usage = data.get("usage", {})
        inp = usage.get("prompt_tokens", 0)
        out = usage.get("completion_tokens", 0)
        cost = estimate_cost(model, inp, out)
        self._input_tokens += inp
        self._output_tokens += out
        self._cost += cost

        return LLMResponse(
            content=content,
            model=data.get("model", model),
            usage_input_tokens=inp,
            usage_output_tokens=out,
            cost=cost,
            finish_reason=choice.get("finish_reason", ""),
        )

    async def chat_json(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> LLMResponse:
        return await self.chat(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def usage_snapshot(self) -> dict[str, float | int]:
        return {
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
            "total_tokens": self._input_tokens + self._output_tokens,
            "cost": self._cost,
        }
