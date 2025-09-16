"""Category repository for category data access."""

from typing import List, Optional

from ..models.category import Category
from .base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository for category operations."""

    @property
    def model_class(self):
        return Category

    def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name."""
        return self.session.query(Category).filter(Category.name == name).first()

    def get_all_active(self) -> List[Category]:
        """Get all categories (they're all active by default)."""
        return self.get_all()

    def create_category(
        self, name: str, display_name: str, description: Optional[str] = None
    ) -> Category:
        """Create a new category."""
        return self.create(
            {"name": name, "display_name": display_name, "description": description}
        )

    def update_category(
        self,
        id: int,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Category]:
        """Update category information."""
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if display_name is not None:
            update_data["display_name"] = display_name
        if description is not None:
            update_data["description"] = description

        return self.update(id, update_data)
