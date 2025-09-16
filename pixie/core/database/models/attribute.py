"""Attribute model for conversational attribute configurations."""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import BaseModel


class Attribute(BaseModel):
    """Attribute model for conversational configurations."""

    __tablename__ = "attributes"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # 'range' or 'choice'
    question = Column(Text, nullable=False)
    description = Column(Text)
    options = Column(JSONB)  # For choice type attributes

    # Relationship to category
    category = relationship("Category", backref="attributes")

    __table_args__ = (
        {"schema": None},  # Default schema
    )

    def __repr__(self):
        return f"<Attribute(id={self.id}, name='{self.name}', category_id={self.category_id})>"
