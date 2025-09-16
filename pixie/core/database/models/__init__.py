# Database models for Pixie-Core products

from .attribute import Attribute
from .base import Base, BaseModel
from .category import Category
from .computer import Computer
from .laptop import Laptop
from .printer import Printer
from .schemas import (
    Attribute as AttributeSchema,
    AttributeBase,
    AttributeCreate,
    Category as CategorySchema,
    CategoryBase,
    CategoryCreate,
    Computer as ComputerSchema,
    ComputerBase,
    ComputerCreate,
    Laptop as LaptopSchema,
    LaptopBase,
    LaptopCreate,
    Printer as PrinterSchema,
    PrinterBase,
    PrinterCreate,
    Smartphone as SmartphoneSchema,
    SmartphoneBase,
    SmartphoneCreate,
)
from .smartphone import Smartphone

__all__ = [
    "Base",
    "BaseModel",
    "Category",
    "Attribute",
    "Printer",
    "Laptop",
    "Computer",
    "Smartphone",
    # Schemas
    "CategorySchema",
    "CategoryBase",
    "CategoryCreate",
    "AttributeSchema",
    "AttributeBase",
    "AttributeCreate",
    "PrinterSchema",
    "PrinterBase",
    "PrinterCreate",
    "LaptopSchema",
    "LaptopBase",
    "LaptopCreate",
    "ComputerSchema",
    "ComputerBase",
    "ComputerCreate",
    "SmartphoneSchema",
    "SmartphoneBase",
    "SmartphoneCreate",
]
