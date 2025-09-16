"""Attribute model for conversational attribute configurations."""

import json
from typing import Any, Dict, Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class Attribute(BaseModel):
    """Attribute model for conversational configurations."""

    __tablename__ = "attributes"

    id = Column(Integer, primary_key=True)
    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # 'range' or 'choice'
    question = Column(Text, nullable=False)
    description = Column(Text)
    options = Column(Text)  # For choice type attributes - stored as JSON string

    # Relationship to category
    category = relationship("Category", backref="attributes")

    __table_args__ = ({"schema": None},)  # Default schema

    @property
    def options_dict(self) -> Optional[Dict[str, Any]]:
        """Get options as dictionary."""
        if self.options:
            try:
                return json.loads(self.options)
            except json.JSONDecodeError:
                return None
        return None

    @options_dict.setter
    def options_dict(self, value: Optional[Dict[str, Any]]) -> None:
        """Set options from dictionary."""
        if value is not None:
            self.options = json.dumps(value)
        else:
            self.options = None

    def __repr__(self):
        return f"<Attribute(id={self.id}, name='{self.name}', category_id={self.category_id})>"
