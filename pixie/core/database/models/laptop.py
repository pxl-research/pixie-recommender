"""Laptop model for laptop products."""

from sqlalchemy import DECIMAL, Boolean, Column, Integer, String, Text

from .base import BaseModel


class Laptop(BaseModel):
    """Laptop product model."""

    __tablename__ = "laptops"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    price_cents = Column(Integer)  # Generated column
    currency = Column(String(3), default="EUR")
    screen_size_inches = Column(DECIMAL(4, 1))
    processor = Column(String(100))
    ram_gb = Column(Integer)
    storage_gb = Column(Integer)
    storage_type = Column(String(50))
    battery_life_hours = Column(DECIMAL(4, 1))
    operating_system = Column(String(100))
    weight_kg = Column(DECIMAL(5, 2))
    has_touchscreen = Column(Boolean, default=False)
    has_webcam = Column(Boolean, default=True)
    graphics_card = Column(String(100))
    ports = Column(Text)  # JSON string or comma-separated
    warranty_years = Column(Integer)
    color = Column(String(50))
    availability_status = Column(String(50), default="in_stock")
    stock_level = Column(Integer, default=0)

    def __repr__(self):
        return f"<Laptop(id={self.id}, name='{self.name}', brand='{self.brand}')>"
