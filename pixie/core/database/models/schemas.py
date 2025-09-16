"""Pydantic schemas for data validation and API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# Base schema with common configuration
class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(from_attributes=True)


# Category schemas
class CategoryBase(BaseSchema):
    """Base category schema."""

    name: str
    display_name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    """Schema for creating categories."""

    pass


class Category(CategoryBase):
    """Full category schema."""

    id: int
    created_at: datetime
    updated_at: datetime


# Attribute schemas
class AttributeBase(BaseSchema):
    """Base attribute schema."""

    category_id: int
    name: str
    type: str  # 'range' or 'choice'
    question: str
    description: Optional[str] = None
    options: Optional[list] = None


class AttributeCreate(AttributeBase):
    """Schema for creating attributes."""

    pass


class Attribute(AttributeBase):
    """Full attribute schema."""

    id: int
    created_at: datetime
    updated_at: datetime


# Product base schemas
class ProductBase(BaseSchema):
    """Base product schema with common fields."""

    name: str
    brand: str
    price: float
    currency: str = "EUR"
    availability_status: str = "in_stock"
    stock_level: int = 0


# Printer schemas
class PrinterBase(ProductBase):
    """Base printer schema."""

    technology: str
    price_cents: int
    description: Optional[str] = None
    has_wifi: bool = False
    has_duplex: bool = False
    has_color: bool = False
    is_multifunction: bool = False
    print_speed_ppm: Optional[int] = None
    resolution_dpi: Optional[str] = None
    max_paper_size: Optional[str] = None


class PrinterCreate(PrinterBase):
    """Schema for creating printers."""

    pass


class Printer(PrinterBase):
    """Full printer schema."""

    id: int
    created_at: datetime
    updated_at: datetime


# Laptop schemas
class LaptopBase(ProductBase):
    """Base laptop schema."""

    screen_size_inches: Optional[float] = None
    processor: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    storage_type: Optional[str] = None
    battery_life_hours: Optional[float] = None
    operating_system: Optional[str] = None
    weight_kg: Optional[float] = None
    has_touchscreen: bool = False
    has_webcam: bool = True
    graphics_card: Optional[str] = None
    ports: Optional[str] = None
    warranty_years: Optional[int] = None
    color: Optional[str] = None


class LaptopCreate(LaptopBase):
    """Schema for creating laptops."""

    pass


class Laptop(LaptopBase):
    """Full laptop schema."""

    id: int
    created_at: datetime
    updated_at: datetime


# Computer schemas
class ComputerBase(ProductBase):
    """Base computer schema."""

    processor: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    storage_type: Optional[str] = None
    motherboard: Optional[str] = None
    power_supply_watts: Optional[int] = None
    case_type: Optional[str] = None
    operating_system: Optional[str] = None
    has_wifi: bool = True
    has_bluetooth: bool = True
    graphics_card: Optional[str] = None
    cooling_system: Optional[str] = None
    ports: Optional[str] = None
    warranty_years: Optional[int] = None
    color: Optional[str] = None


class ComputerCreate(ComputerBase):
    """Schema for creating computers."""

    pass


class Computer(ComputerBase):
    """Full computer schema."""

    id: int
    created_at: datetime
    updated_at: datetime


# Smartphone schemas
class SmartphoneBase(ProductBase):
    """Base smartphone schema."""

    screen_size_inches: Optional[float] = None
    resolution: Optional[str] = None
    processor: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    battery_capacity_mah: Optional[int] = None
    operating_system: Optional[str] = None
    camera_mp: Optional[float] = None
    has_5g: bool = False
    has_nfc: bool = False
    has_wireless_charging: bool = False
    water_resistance: Optional[str] = None
    weight_g: Optional[float] = None
    dimensions_mm: Optional[str] = None
    color: Optional[str] = None


class SmartphoneCreate(SmartphoneBase):
    """Schema for creating smartphones."""

    pass


class Smartphone(SmartphoneBase):
    """Full smartphone schema."""

    id: int
    created_at: datetime
    updated_at: datetime
