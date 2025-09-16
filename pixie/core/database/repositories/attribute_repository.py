"""Attribute repository for attribute data access."""

from typing import List, Optional

from ..models.attribute import Attribute
from .base import BaseRepository


class AttributeRepository(BaseRepository[Attribute]):
    """Repository for attribute operations."""

    @property
    def model_class(self):
        return Attribute

    def get_by_category(self, category_id: int) -> List[Attribute]:
        """Get all attributes for a specific category."""
        return (
            self.session.query(Attribute)
            .filter(Attribute.category_id == category_id)
            .all()
        )

    def get_by_category_and_name(
        self, category_id: int, name: str
    ) -> Optional[Attribute]:
        """Get attribute by category and name."""
        return (
            self.session.query(Attribute)
            .filter(Attribute.category_id == category_id, Attribute.name == name)
            .first()
        )

    def get_by_type(self, attr_type: str) -> List[Attribute]:
        """Get all attributes of a specific type."""
        return self.session.query(Attribute).filter(Attribute.type == attr_type).all()

    def create_attribute(
        self,
        category_id: int,
        name: str,
        attr_type: str,
        question: str,
        description: Optional[str] = None,
        options: Optional[list] = None,
    ) -> Attribute:
        """Create a new attribute."""
        return self.create(
            {
                "category_id": category_id,
                "name": name,
                "type": attr_type,
                "question": question,
                "description": description,
                "options": options,
            }
        )

    def update_attribute(
        self,
        id: int,
        name: Optional[str] = None,
        attr_type: Optional[str] = None,
        question: Optional[str] = None,
        description: Optional[str] = None,
        options: Optional[list] = None,
    ) -> Optional[Attribute]:
        """Update attribute information."""
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if attr_type is not None:
            update_data["type"] = attr_type
        if question is not None:
            update_data["question"] = question
        if description is not None:
            update_data["description"] = description
        if options is not None:
            update_data["options"] = options

        return self.update(id, update_data)
