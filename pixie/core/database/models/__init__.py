# Database models for Pixie-Core products

from .attribute import Attribute
from .base import Base, BaseModel
from .category import Category
from .computer import Computer
from .laptop import Laptop
from .printer import Printer
from .schemas import (
    Attribute as AttributeSchema,
)
from .schemas import (
    AttributeBase,
    AttributeCreate,
    CategoryBase,
    CategoryCreate,
    ComputerBase,
    ComputerCreate,
    LaptopBase,
    LaptopCreate,
    PrinterBase,
    PrinterCreate,
    SmartphoneBase,
    SmartphoneCreate,
)
from .schemas import (
    Category as CategorySchema,
)
from .schemas import (
    Computer as ComputerSchema,
)
from .schemas import (
    Laptop as LaptopSchema,
)
from .schemas import (
    Printer as PrinterSchema,
)
from .schemas import (
    Smartphone as SmartphoneSchema,
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
