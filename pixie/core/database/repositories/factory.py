"""Repository factory for dependency injection and clean architecture."""

from sqlalchemy.orm import Session

from .attribute_repository import AttributeRepository
from .category_repository import CategoryRepository
from .computer_repository import ComputerRepository
from .laptop_repository import LaptopRepository
from .printer_repository import PrinterRepository
from .smartphone_repository import SmartphoneRepository


class RepositoryFactory:
    """Factory for creating repository instances."""

    def __init__(self, session: Session):
        self.session = session

    def create_category_repository(self) -> CategoryRepository:
        """Create category repository."""
        return CategoryRepository(self.session)

    def create_attribute_repository(self) -> AttributeRepository:
        """Create attribute repository."""
        return AttributeRepository(self.session)

    def create_printer_repository(self) -> PrinterRepository:
        """Create printer repository."""
        return PrinterRepository(self.session)

    def create_laptop_repository(self) -> LaptopRepository:
        """Create laptop repository."""
        return LaptopRepository(self.session)

    def create_computer_repository(self) -> ComputerRepository:
        """Create computer repository."""
        return ComputerRepository(self.session)

    def create_smartphone_repository(self) -> SmartphoneRepository:
        """Create smartphone repository."""
        return SmartphoneRepository(self.session)

    def get_repository(self, repository_type: str):
        """Get repository by type string."""
        mapping = {
            "category": self.create_category_repository,
            "attribute": self.create_attribute_repository,
            "printer": self.create_printer_repository,
            "laptop": self.create_laptop_repository,
            "computer": self.create_computer_repository,
            "smartphone": self.create_smartphone_repository,
        }

        if repository_type in mapping:
            return mapping[repository_type]()
        else:
            raise ValueError(f"Unknown repository type: {repository_type}")


def get_repository_factory(session: Session) -> RepositoryFactory:
    """Factory function for RepositoryFactory."""
    return RepositoryFactory(session)
