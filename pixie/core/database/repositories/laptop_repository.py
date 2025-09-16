"""Laptop repository for laptop data access."""

from typing import List, Optional

from sqlalchemy import between

from ..models.laptop import Laptop
from .base import BaseRepository


class LaptopRepository(BaseRepository[Laptop]):
    """Repository for laptop operations."""

    @property
    def model_class(self):
        return Laptop

    def get_by_brand(self, brand: str, skip: int = 0, limit: Optional[int] = None) -> List[Laptop]:
        """Get laptops by brand."""
        return self.filter_by({"brand": brand}, skip=skip, limit=limit)

    def get_by_price_range(
        self,
        min_price: float,
        max_price: float,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Laptop]:
        """Get laptops within price range."""
        query = self.session.query(Laptop).filter(
            between(Laptop.price, min_price, max_price)
        ).offset(skip)

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_by_screen_size(
        self,
        min_size: float,
        max_size: float,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Laptop]:
        """Get laptops by screen size range."""
        query = self.session.query(Laptop).filter(
            between(Laptop.screen_size_inches, min_size, max_size)
        ).offset(skip)

        if limit:
            query = query.limit(limit)

        return query.all()

    def search_laptops(
        self,
        search_term: str,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Laptop]:
        """Search laptops by name, brand, or processor."""
        return self.search(
            search_term,
            ["name", "brand", "processor"],
            skip=skip,
            limit=limit
        )

    def get_available_laptops(self, skip: int = 0, limit: Optional[int] = None) -> List[Laptop]:
        """Get laptops that are in stock."""
        return self.filter_by({"availability_status": "in_stock"}, skip=skip, limit=limit)

    def create_laptop(self, **kwargs) -> Laptop:
        """Create a new laptop."""
        return self.create(kwargs)

    def update_laptop(self, id: int, **kwargs) -> Optional[Laptop]:
        """Update laptop information."""
        return self.update(id, kwargs)
