"""Smartphone model for smartphone products."""

from sqlalchemy import Boolean, Column, DECIMAL, Integer, String

from .base import BaseModel


class Smartphone(BaseModel):
    """Smartphone product model."""

    __tablename__ = "smartphones"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    price_cents = Column(Integer)  # Generated column
    currency = Column(String(3), default="EUR")
    screen_size_inches = Column(DECIMAL(4, 1))
    resolution = Column(String(50))
    processor = Column(String(100))
    ram_gb = Column(Integer)
    storage_gb = Column(Integer)
    battery_capacity_mah = Column(Integer)
    operating_system = Column(String(100))
    camera_mp = Column(DECIMAL(4, 1))
    has_5g = Column(Boolean, default=False)
    has_nfc = Column(Boolean, default=False)
    has_wireless_charging = Column(Boolean, default=False)
    water_resistance = Column(String(50))
    weight_g = Column(DECIMAL(6, 1))
    dimensions_mm = Column(String(50))
    color = Column(String(50))
    availability_status = Column(String(50), default="in_stock")
    stock_level = Column(Integer, default=0)

    def __repr__(self):
        return f"<Smartphone(id={self.id}, name='{self.name}', brand='{self.brand}')>"
