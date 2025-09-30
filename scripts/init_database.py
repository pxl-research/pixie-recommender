#!/usr/bin/env python3
"""Simple database initialization script for CI/CD environments."""

import logging
import os

from sqlalchemy import create_engine

from pixie.core.database.models import Base

logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment variables."""
    default_url = "postgresql://pixie_user:pixie_password@postgres:5432/pixie_dev"
    return os.getenv("DATABASE_URL", default_url)


def init_database_simple():
    """Ensure database tables exist without inserting sample data."""
    engine = create_engine(get_database_url())

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema ensured successfully")
        return True
    except Exception as exc:  # pragma: no cover - log and re-raise
        logger.error(f"Database initialization failed: {exc}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database_simple()
