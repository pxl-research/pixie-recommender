"""Simple configuration for Pixie Core development."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Load environment variables from .env.dev if it exists
project_root = Path(__file__).parent.parent.parent
env_dev_path = project_root / ".env.dev"
if env_dev_path.exists():
    from dotenv import load_dotenv

    load_dotenv(env_dev_path)


@dataclass
class AzureConfig:
    """Azure OpenAI configuration."""

    api_version: str
    api_endpoint: str
    api_key: str
    model_version: str


@dataclass
class Config:
    """Main configuration."""

    azure: AzureConfig
    default_page_size: int

    @classmethod
    def from_env(cls) -> Config:
        """Load config from environment variables."""
        azure_config = AzureConfig(
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            api_endpoint=os.getenv(
                "AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/"
            ),
            api_key=os.getenv("AZURE_OPENAI_KEY", "dummy-key-for-development"),
            model_version=os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
        )

        page_size = int(os.getenv("PIXIE_DEFAULT_PAGE_SIZE", "10"))

        return cls(azure=azure_config, default_page_size=page_size)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reset_config() -> None:
    """Reset cached configuration - useful for testing or when environment changes."""
    global _config
    _config = None
