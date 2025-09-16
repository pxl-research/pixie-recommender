"""Generic repository for flexible product system."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..connection import get_db_session
from ..models.base import (
    AttributeDefinition,
    Product,
    ProductAttributeValue,
    ProductType,
)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic base repository with common CRUD operations."""

    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self.model_class = model_class

    def get_all(self) -> List[T]:
        """Get all records."""
        return self.session.query(self.model_class).all()

    def get_by_id(self, id: UUID) -> Optional[T]:
        """Get record by ID."""
        return (
            self.session.query(self.model_class)
            .filter(self.model_class.id == id)
            .first()
        )

    def create(self, data: Dict[str, Any]) -> T:
        """Create a new record."""
        instance = self.model_class(**data)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def update(self, id: UUID, data: Dict[str, Any]) -> Optional[T]:
        """Update a record."""
        instance = self.get_by_id(id)
        if instance:
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            self.session.commit()
            self.session.refresh(instance)
        return instance

    def delete(self, id: UUID) -> bool:
        """Delete a record."""
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.commit()
            return True
        return False


class ProductTypeRepository(BaseRepository[ProductType]):
    """Repository for product types."""

    def __init__(self, session: Session):
        super().__init__(session, ProductType)

    def get_by_name(self, name: str) -> Optional[ProductType]:
        """Get product type by name."""
        return self.session.query(ProductType).filter(ProductType.name == name).first()

    def get_active(self) -> List[ProductType]:
        """Get all active product types."""
        return self.session.query(ProductType).filter(ProductType.is_active).all()


class AttributeDefinitionRepository(BaseRepository[AttributeDefinition]):
    """Repository for attribute definitions."""

    def __init__(self, session: Session):
        super().__init__(session, AttributeDefinition)

    def get_by_product_type(self, product_type_id: UUID) -> List[AttributeDefinition]:
        """Get all attribute definitions for a product type."""
        return (
            self.session.query(AttributeDefinition)
            .filter(AttributeDefinition.product_type_id == product_type_id)
            .order_by(AttributeDefinition.display_order)
            .all()
        )

    def get_by_name_and_type(
        self, name: str, product_type_id: UUID
    ) -> Optional[AttributeDefinition]:
        """Get attribute definition by name and product type."""
        return (
            self.session.query(AttributeDefinition)
            .filter(
                and_(
                    AttributeDefinition.name == name,
                    AttributeDefinition.product_type_id == product_type_id,
                )
            )
            .first()
        )


class ProductRepository(BaseRepository[Product]):
    """Repository for products."""

    def __init__(self, session: Session):
        super().__init__(session, Product)

    def get_by_product_type(self, product_type_id: UUID) -> List[Product]:
        """Get all products of a specific type."""
        return (
            self.session.query(Product)
            .filter(Product.product_type_id == product_type_id)
            .all()
        )

    def get_by_external_id(self, external_id: str) -> Optional[Product]:
        """Get product by external ID."""
        return (
            self.session.query(Product)
            .filter(Product.external_id == external_id)
            .first()
        )

    def search_by_name(self, name_query: str) -> List[Product]:
        """Search products by name."""
        return (
            self.session.query(Product)
            .filter(Product.name.ilike(f"%{name_query}%"))
            .all()
        )

    def get_active(self) -> List[Product]:
        """Get all active products."""
        return self.session.query(Product).filter(Product.is_active).all()


class ProductAttributeValueRepository(BaseRepository[ProductAttributeValue]):
    """Repository for product attribute values."""

    def __init__(self, session: Session):
        super().__init__(session, ProductAttributeValue)

    def get_by_product(self, product_id: UUID) -> List[ProductAttributeValue]:
        """Get all attribute values for a product."""
        return (
            self.session.query(ProductAttributeValue)
            .join(AttributeDefinition)
            .filter(ProductAttributeValue.product_id == product_id)
            .order_by(AttributeDefinition.display_order)
            .all()
        )

    def get_by_attribute_definition(
        self, attribute_definition_id: UUID
    ) -> List[ProductAttributeValue]:
        """Get all values for a specific attribute definition."""
        return (
            self.session.query(ProductAttributeValue)
            .filter(
                ProductAttributeValue.attribute_definition_id == attribute_definition_id
            )
            .all()
        )

    def get_value(
        self, product_id: UUID, attribute_definition_id: UUID
    ) -> Optional[ProductAttributeValue]:
        """Get a specific attribute value."""
        return (
            self.session.query(ProductAttributeValue)
            .filter(
                and_(
                    ProductAttributeValue.product_id == product_id,
                    ProductAttributeValue.attribute_definition_id
                    == attribute_definition_id,
                )
            )
            .first()
        )

    def set_value(
        self, product_id: UUID, attribute_definition_id: UUID, value: Any
    ) -> ProductAttributeValue:
        """Set or update an attribute value."""
        existing = self.get_value(product_id, attribute_definition_id)
        if existing:
            existing.value = value
            self.session.commit()
            self.session.refresh(existing)
            return existing
        else:
            return self.create(
                {
                    "product_id": product_id,
                    "attribute_definition_id": attribute_definition_id,
                    "value": value,
                }
            )


# Convenience functions for getting repositories
def get_product_type_repository(
    session: Optional[Session] = None,
) -> ProductTypeRepository:
    """Get product type repository."""
    if session is None:
        with get_db_session() as s:
            return ProductTypeRepository(s)
    return ProductTypeRepository(session)


def get_attribute_definition_repository(
    session: Optional[Session] = None,
) -> AttributeDefinitionRepository:
    """Get attribute definition repository."""
    if session is None:
        with get_db_session() as s:
            return AttributeDefinitionRepository(s)
    return AttributeDefinitionRepository(session)


def get_product_repository(session: Optional[Session] = None) -> ProductRepository:
    """Get product repository."""
    if session is None:
        with get_db_session() as s:
            return ProductRepository(s)
    return ProductRepository(session)


def get_product_attribute_value_repository(
    session: Optional[Session] = None,
) -> ProductAttributeValueRepository:
    """Get product attribute value repository."""
    if session is None:
        with get_db_session() as s:
            return ProductAttributeValueRepository(s)
    return ProductAttributeValueRepository(session)
