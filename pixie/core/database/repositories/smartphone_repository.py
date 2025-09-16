"""Smartphone repository for smartphone data access."""

from typing import List, Optional

from sqlalchemy import between

from ..models.smartphone import Smartphone
from .base import BaseRepository


class SmartphoneRepository(BaseRepository[Smartphone]):
    """Repository for smartphone operations."""

    @property
    def model_class(self):
        return Smartphone

    def get_by_brand(
        self,
        brand: str,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Smartphone]:
        """Get smartphones by brand."""
        return self.filter_by({"brand": brand}, skip=skip, limit=limit)

    def get_by_price_range(
        self,
        min_price: float,
        max_price: float,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Smartphone]:
        """Get smartphones within price range."""
        query = self.session.query(Smartphone).filter(
            between(Smartphone.price, min_price, max_price)
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
    ) -> List[Smartphone]:
        """Get smartphones by screen size range."""
        query = self.session.query(Smartphone).filter(
            between(Smartphone.screen_size_inches, min_size, max_size)
        ).offset(skip)

        if limit:
            query = query.limit(limit)

        return query.all()

    def search_smartphones(
        self,
        search_term: str,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Smartphone]:
        """Search smartphones by name, brand, or processor."""
        return self.search(
            search_term,
            ["name", "brand", "processor"],
            skip=skip,
            limit=limit
        )

    def get_available_smartphones(
        self,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Smartphone]:
        """Get smartphones that are in stock."""
        return self.filter_by({"availability_status": "in_stock"}, skip=skip, limit=limit)

    def create_smartphone(self, **kwargs) -> Smartphone:
        """Create a new smartphone."""
        return self.create(kwargs)

    def update_smartphone(self, id: int, **kwargs) -> Optional[Smartphone]:
        """Update smartphone information."""
        return self.update(id, kwargs)
