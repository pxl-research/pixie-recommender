"""Simple configuration for Pixie Core development."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AzureConfig:
    """Azure OpenAI configuration."""
    api_version: str
    api_endpoint: str
    api_key: str
    model_version: str


@dataclass
class SearchConfig:
    """Search configuration."""
    data_file_path: str
    default_page_size: int


@dataclass
class Config:
    """Main configuration."""
    azure: AzureConfig
    search: SearchConfig

    @classmethod
    def from_env(cls) -> Config:
        """Load config from environment variables."""
        azure_config = AzureConfig(
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            api_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/"),
            api_key=os.getenv("AZURE_OPENAI_KEY", "dummy-key-for-development"),
            model_version=os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
        )

        search_config = SearchConfig(
            data_file_path=os.getenv("PIXIE_PRINTER_DATA", "pixie/core/data/printers.json"),
            default_page_size=int(os.getenv("PIXIE_DEFAULT_PAGE_SIZE", "10")),
        )

        return cls(azure=azure_config, search=search_config)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
