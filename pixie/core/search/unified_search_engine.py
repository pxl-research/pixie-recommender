"""Unified search engine that can switch between JSON and database backends."""

import logging
import os
from typing import Any, Dict, List, Optional

from ..utils.config import get_config

logger = logging.getLogger(__name__)


class UnifiedSearchEngine:
    """Unified search engine that switches between JSON and database backends.

    Methods:
      search(sql: str, attributes: Optional[Dict[str, Any]],
             category: Optional[str] = None) -> List[Dict]
    """

    def __init__(self):
        self._config = get_config()
        self._backend = None
        self._load_backend()

    def _load_backend(self):
        """Load the appropriate search backend based on configuration."""
        # Check if database mode is explicitly enabled
        use_database = os.getenv("PIXIE_USE_DATABASE", "false").lower() == "true"

        # Also check if database URL is configured (not the default dummy)
        db_url = self._config.database.url
        if not use_database and db_url and "localhost" in db_url and "pixie_db" in db_url:
            # If using default dummy database URL, don't try database
            use_database = False
        elif db_url and db_url != "postgresql://pixie_user:pixie_password@localhost:5432/pixie_db":
            # If database URL is customized, try to use database
            use_database = True

        if use_database:
            try:
                from .database_search_engine import DatabaseSearchEngine
                self._backend = DatabaseSearchEngine()
                logger.info("Using database search backend")
            except ImportError as e:
                logger.warning(f"Database backend not available: {e}")
                self._fallback_to_json()
            except Exception as e:
                logger.warning(f"Database backend failed to initialize: {e}")
                self._fallback_to_json()
        else:
            self._fallback_to_json()

    def _fallback_to_json(self):
        """Fallback to JSON-based search engine."""
        try:
            from .search_engine import RealSearchEngine
            self._backend = RealSearchEngine()
            logger.info("Using JSON search backend")
        except ImportError as e:
            logger.error(f"No search backend available: {e}")
            raise RuntimeError("No search backend available")

    def search(
        self,
        sql: str,
        attributes: Optional[Dict[str, Any]],
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search products using the configured backend."""
        if self._backend is None:
            raise RuntimeError("Search backend not initialized")

        return self._backend.search(sql, attributes, category)

    def get_categories(self) -> List[str]:
        """Get list of available categories."""
        if self._backend is None:
            raise RuntimeError("Search backend not initialized")

        return self._backend.get_categories()

    def get_category_metadata(self, category: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific category."""
        if self._backend is None:
            raise RuntimeError("Search backend not initialized")

        return self._backend.get_category_metadata(category)


def create_unified_search_engine() -> UnifiedSearchEngine:
    """Factory function for unified search engine."""
    return UnifiedSearchEngine()
