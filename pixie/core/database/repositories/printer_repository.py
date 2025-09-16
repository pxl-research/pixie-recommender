"""Printer repository for printer data access."""

from typing import Dict, List, Optional

from sqlalchemy import between

from ..models.printer import Printer
from .base import BaseRepository


class PrinterRepository(BaseRepository[Printer]):
    """Repository for printer operations."""

    @property
    def model_class(self):
        return Printer

    def get_by_brand(
        self, brand: str, skip: int = 0, limit: Optional[int] = None
    ) -> List[Printer]:
        """Get printers by brand."""
        return self.filter_by({"brand": brand}, skip=skip, limit=limit)

    def get_by_technology(
        self, technology: str, skip: int = 0, limit: Optional[int] = None
    ) -> List[Printer]:
        """Get printers by technology."""
        return self.filter_by({"technology": technology}, skip=skip, limit=limit)

    def get_by_price_range(
        self,
        min_price: float,
        max_price: float,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Printer]:
        """Get printers within price range."""
        return self.filter_by_price_range(min_price, max_price, skip, limit)

    def filter_by_price_range(
        self,
        min_price: float,
        max_price: float,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Printer]:
        """Filter printers by price range using between."""
        query = (
            self.session.query(Printer)
            .filter(between(Printer.price, min_price, max_price))
            .offset(skip)
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_multifunction_printers(
        self, skip: int = 0, limit: Optional[int] = None
    ) -> List[Printer]:
        """Get only multifunction printers."""
        return self.filter_by({"is_multifunction": True}, skip=skip, limit=limit)

    def get_color_printers(
        self, skip: int = 0, limit: Optional[int] = None
    ) -> List[Printer]:
        """Get only color printers."""
        return self.filter_by({"has_color": True}, skip=skip, limit=limit)

    def get_wifi_printers(
        self, skip: int = 0, limit: Optional[int] = None
    ) -> List[Printer]:
        """Get only WiFi-enabled printers."""
        return self.filter_by({"has_wifi": True}, skip=skip, limit=limit)

    def search_printers(
        self, search_term: str, skip: int = 0, limit: Optional[int] = None
    ) -> List[Printer]:
        """Search printers by name, brand, or description."""
        return self.search(
            search_term, ["name", "brand", "description"], skip=skip, limit=limit
        )

    def get_available_printers(
        self, skip: int = 0, limit: Optional[int] = None
    ) -> List[Printer]:
        """Get printers that are in stock."""
        return self.filter_by(
            {"availability_status": "in_stock"}, skip=skip, limit=limit
        )

    def advanced_filter(
        self, filters: Dict, skip: int = 0, limit: Optional[int] = None
    ) -> List[Printer]:
        """Advanced filtering with multiple criteria."""
        query = self.session.query(Printer)

        # Price range
        if "min_price" in filters and "max_price" in filters:
            query = query.filter(
                between(Printer.price, filters["min_price"], filters["max_price"])
            )

        # Brand filter
        if "brand" in filters:
            if isinstance(filters["brand"], list):
                query = query.filter(Printer.brand.in_(filters["brand"]))
            else:
                query = query.filter(Printer.brand == filters["brand"])

        # Technology filter
        if "technology" in filters:
            if isinstance(filters["technology"], list):
                query = query.filter(Printer.technology.in_(filters["technology"]))
            else:
                query = query.filter(Printer.technology == filters["technology"])

        # Feature filters
        if "has_wifi" in filters:
            query = query.filter(Printer.has_wifi == filters["has_wifi"])
        if "has_color" in filters:
            query = query.filter(Printer.has_color == filters["has_color"])
        if "is_multifunction" in filters:
            query = query.filter(
                Printer.is_multifunction == filters["is_multifunction"]
            )

        # Availability
        if "availability_status" in filters:
            query = query.filter(
                Printer.availability_status == filters["availability_status"]
            )

        query = query.offset(skip)
        if limit:
            query = query.limit(limit)

        return query.all()

    def create_printer(self, **kwargs) -> Printer:
        """Create a new printer."""
        return self.create(kwargs)

    def update_printer(self, id: int, **kwargs) -> Optional[Printer]:
        """Update printer information."""
        return self.update(id, kwargs)
