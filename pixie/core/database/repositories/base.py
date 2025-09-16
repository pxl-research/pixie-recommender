"""Base repository class with common CRUD operations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(ABC, Generic[ModelType]):
    """Base repository with common database operations."""

    def __init__(self, session: Session):
        self.session = session

    @property
    @abstractmethod
    def model_class(self) -> Type[ModelType]:
        """Return the model class for this repository."""
        pass

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get a record by ID."""
        try:
            return self.session.get(self.model_class, id)
        except SQLAlchemyError:
            return None

    def get_all(self, skip: int = 0, limit: Optional[int] = None) -> List[ModelType]:
        """Get all records with optional pagination."""
        query = select(self.model_class).offset(skip)
        if limit:
            query = query.limit(limit)
        return list(self.session.execute(query).scalars())

    def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        obj = self.model_class(**obj_data)
        self.session.add(obj)
        self.session.flush()  # Get the ID without committing
        return obj

    def update(self, id: int, obj_data: Dict[str, Any]) -> Optional[ModelType]:
        """Update an existing record."""
        obj = self.get_by_id(id)
        if obj:
            for key, value in obj_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self.session.flush()
        return obj

    def delete(self, id: int) -> bool:
        """Delete a record by ID."""
        obj = self.get_by_id(id)
        if obj:
            self.session.delete(obj)
            return True
        return False

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        query = select(self.model_class)
        if filters:
            conditions = []
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    conditions.append(getattr(self.model_class, key) == value)
            if conditions:
                query = query.where(and_(*conditions))

        result = self.session.execute(query)
        return len(list(result.scalars()))

    def exists(self, id: int) -> bool:
        """Check if a record exists."""
        return self.get_by_id(id) is not None

    def filter_by(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> List[ModelType]:
        """Filter records by multiple criteria."""
        query = select(self.model_class)

        # Apply filters
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                if isinstance(value, list):
                    # Handle list values (IN clause)
                    conditions.append(getattr(self.model_class, key).in_(value))
                else:
                    conditions.append(getattr(self.model_class, key) == value)

        if conditions:
            query = query.where(and_(*conditions))

        # Apply ordering
        if order_by:
            if hasattr(self.model_class, order_by):
                query = query.order_by(getattr(self.model_class, order_by))

        # Apply pagination
        query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        return list(self.session.execute(query).scalars())

    def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[ModelType]:
        """Search records using full-text search on specified fields."""
        query = select(self.model_class)

        # Build search conditions
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model_class, field):
                # Use ILIKE for case-insensitive search
                search_conditions.append(
                    getattr(self.model_class, field).ilike(f"%{search_term}%")
                )

        if search_conditions:
            query = query.where(or_(*search_conditions))

        query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        return list(self.session.execute(query).scalars())
