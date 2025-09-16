# Database repositories for data access layer

from .attribute_repository import AttributeRepository
from .base import BaseRepository
from .category_repository import CategoryRepository
from .computer_repository import ComputerRepository
from .factory import RepositoryFactory, get_repository_factory
from .laptop_repository import LaptopRepository
from .printer_repository import PrinterRepository
from .smartphone_repository import SmartphoneRepository

__all__ = [
    "BaseRepository",
    "CategoryRepository",
    "AttributeRepository",
    "PrinterRepository",
    "LaptopRepository",
    "ComputerRepository",
    "SmartphoneRepository",
    "RepositoryFactory",
    "get_repository_factory",
]
