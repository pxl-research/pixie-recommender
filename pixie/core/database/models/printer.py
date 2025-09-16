"""Printer model for printer products."""

from sqlalchemy import Boolean, Column, DECIMAL, Integer, String, Text

from .base import BaseModel


class Printer(BaseModel):
    """Printer product model."""

    __tablename__ = "printers"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=False)
    technology = Column(String(50), nullable=False)
    price_cents = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    description = Column(Text)
    has_wifi = Column(Boolean, default=False)
    has_duplex = Column(Boolean, default=False)
    has_color = Column(Boolean, default=False)
    is_multifunction = Column(Boolean, default=False)
    print_speed_ppm = Column(Integer)
    resolution_dpi = Column(String(50))
    max_paper_size = Column(String(50))
    availability_status = Column(String(50), default="in_stock")
    stock_level = Column(Integer, default=0)

    def __repr__(self):
        return f"<Printer(id={self.id}, name='{self.name}', brand='{self.brand}')>"
