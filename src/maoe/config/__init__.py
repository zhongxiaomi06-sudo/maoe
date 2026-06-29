from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MAOE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_base_url: str = "https://api.openai-next.com/v1"
    api_key: str = ""

    default_model: str = "gpt-4o-mini"
    max_concurrent_tasks: int = 5
    default_token_budget: int = 32000
    max_attempts_per_task: int = 3
    quality_check_model: str = "gpt-4o-mini"

    log_level: str = "INFO"
    log_format: str = "{time:HH:mm:ss} | {level:<7} | {message}"

    def model_config_dict(self) -> dict:
        return {
            "fast": {"model": "gpt-4o-mini", "max_tokens": 16384},
            "balanced": {"model": "gpt-4o", "max_tokens": 32768},
            "powerful": {"model": "gpt-5", "max_tokens": 65536},
            "critical": {"model": "gpt-5.5", "max_tokens": 131072},
        }


settings = Settings()
