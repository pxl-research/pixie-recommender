"""Computer repository for desktop computer data access."""

from typing import List, Optional

from sqlalchemy import between

from ..models.computer import Computer
from .base import BaseRepository


class ComputerRepository(BaseRepository[Computer]):
    """Repository for computer operations."""

    @property
    def model_class(self):
        return Computer

    def get_by_brand(
        self,
        brand: str,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Computer]:
        """Get computers by brand."""
        return self.filter_by({"brand": brand}, skip=skip, limit=limit)

    def get_by_price_range(
        self,
        min_price: float,
        max_price: float,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Computer]:
        """Get computers within price range."""
        query = self.session.query(Computer).filter(
            between(Computer.price, min_price, max_price)
        ).offset(skip)

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_by_processor(
        self,
        processor: str,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Computer]:
        """Get computers by processor type."""
        return self.filter_by({"processor": processor}, skip=skip, limit=limit)

    def search_computers(
        self,
        search_term: str,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Computer]:
        """Search computers by name, brand, or processor."""
        return self.search(
            search_term,
            ["name", "brand", "processor"],
            skip=skip,
            limit=limit
        )

    def get_available_computers(self, skip: int = 0, limit: Optional[int] = None) -> List[Computer]:
        """Get computers that are in stock."""
        return self.filter_by({"availability_status": "in_stock"}, skip=skip, limit=limit)

    def create_computer(self, **kwargs) -> Computer:
        """Create a new computer."""
        return self.create(kwargs)

    def update_computer(self, id: int, **kwargs) -> Optional[Computer]:
        """Update computer information."""
        return self.update(id, kwargs)
