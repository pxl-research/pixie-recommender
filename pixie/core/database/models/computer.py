"""Computer model for desktop computer products."""

from sqlalchemy import Boolean, Column, DECIMAL, Integer, String, Text

from .base import BaseModel


class Computer(BaseModel):
    """Desktop computer product model."""

    __tablename__ = "computers"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    price_cents = Column(Integer)  # Generated column
    currency = Column(String(3), default="EUR")
    processor = Column(String(100))
    ram_gb = Column(Integer)
    storage_gb = Column(Integer)
    storage_type = Column(String(50))
    motherboard = Column(String(100))
    power_supply_watts = Column(Integer)
    case_type = Column(String(50))
    operating_system = Column(String(100))
    has_wifi = Column(Boolean, default=True)
    has_bluetooth = Column(Boolean, default=True)
    graphics_card = Column(String(100))
    cooling_system = Column(String(100))
    ports = Column(Text)  # JSON string or comma-separated
    warranty_years = Column(Integer)
    color = Column(String(50))
    availability_status = Column(String(50), default="in_stock")
    stock_level = Column(Integer, default=0)

    def __repr__(self):
        return f"<Computer(id={self.id}, name='{self.name}', brand='{self.brand}')>"
