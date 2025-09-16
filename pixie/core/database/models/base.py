"""Base database model configuration for SQLAlchemy."""

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

# Create the declarative base for all models
Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields and methods."""

    __abstract__ = True

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>"
