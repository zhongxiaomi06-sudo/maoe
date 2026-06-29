from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class ModelTier(StrEnum):
    FAST = "fast"
    BALANCED = "balanced"
    POWERFUL = "powerful"
    CRITICAL = "critical"


TIER_ORDER = [ModelTier.FAST, ModelTier.BALANCED, ModelTier.POWERFUL, ModelTier.CRITICAL]


class ModelCapability(BaseModel):
    name: str
    tier: ModelTier
    max_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    supports_vision: bool = False
    supports_reasoning: bool = False
    supports_code: bool = True
    provider: str = "openai-next"


DEFAULT_MODELS: list[ModelCapability] = [
    ModelCapability(
        name="gpt-4o-mini",
        tier=ModelTier.FAST,
        max_tokens=16384,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
    ),
    ModelCapability(
        name="gpt-4o",
        tier=ModelTier.BALANCED,
        max_tokens=32768,
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.01,
        supports_vision=True,
    ),
    ModelCapability(
        name="gpt-5",
        tier=ModelTier.POWERFUL,
        max_tokens=65536,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.04,
        supports_vision=True,
        supports_reasoning=True,
    ),
    ModelCapability(
        name="gpt-5.5",
        tier=ModelTier.CRITICAL,
        max_tokens=131072,
        cost_per_1k_input=0.05,
        cost_per_1k_output=0.15,
        supports_vision=True,
        supports_reasoning=True,
    ),
]


class RoutingDecision(BaseModel):
    subtask_id: str
    assigned_model: str
    assigned_tier: ModelTier
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost: float = 0.0
    reason: str = ""
