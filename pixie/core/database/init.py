"""Database initialization and schema management."""

import logging
from typing import List

from sqlalchemy.exc import SQLAlchemyError

from .connection import get_engine
from .models import Base

logger = logging.getLogger(__name__)


def create_tables() -> None:
    """Create all database tables defined in the models."""
    try:
        engine = get_engine()
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_tables() -> None:
    """Drop all database tables."""
    try:
        engine = get_engine()
        logger.info("Dropping database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def reset_database() -> None:
    """Reset the database by dropping and recreating all tables."""
    logger.info("Resetting database...")
    drop_tables()
    create_tables()
    logger.info("Database reset complete")


def get_table_names() -> List[str]:
    """Get list of all table names in the database."""
    engine = get_engine()
    return engine.table_names()


def health_check() -> dict:
    """Perform database health check."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute("SELECT 1 as health_check")
            row = result.fetchone()
            if row and row[0] == 1:
                return {
                    "status": "healthy",
                    "message": "Database connection successful",
                    "tables": get_table_names(),
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Database health check failed",
                }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }


def init_database() -> None:
    """Initialize the database with tables and initial data."""
    logger.info("Initializing database...")

    # Create tables
    create_tables()

    # Here we could add initial data seeding if needed
    # For now, we'll rely on the SQL migration files for initial data

    logger.info("Database initialization complete")
