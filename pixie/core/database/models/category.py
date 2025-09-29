"""Category model for product type metadata."""

from sqlalchemy import Column, Integer, String, Text

from .base import BaseModel


class Category(BaseModel):
    """Category model for product types."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"
