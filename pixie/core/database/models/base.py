"""Flexible database models for dynamic product types with attributes."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ProductType(Base):
    """Product type/category definition."""

    __tablename__ = "product_types"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    products = relationship("Product", back_populates="product_type")
    attribute_definitions = relationship(
        "AttributeDefinition", back_populates="product_type"
    )

    def __repr__(self):
        return f"<ProductType(name='{self.name}', display_name='{self.display_name}')>"


class AttributeDefinition(Base):
    """Attribute definition for a product type."""

    __tablename__ = "attribute_definitions"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    product_type_id = Column(
        UUID(as_uuid=True), ForeignKey("product_types.id"), nullable=False
    )
    name = Column(String(100), nullable=False)
    display_name = Column(String(200), nullable=False)
    # Optional canonical name used by conversation layer to map attribute keys
    canonical_name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    data_type = Column(
        String(50), nullable=False
    )  # 'string', 'number', 'boolean', 'choice', 'range'
    is_required = Column(Boolean, default=False, nullable=False)
    is_searchable = Column(Boolean, default=True, nullable=False)
    is_filterable = Column(Boolean, default=True, nullable=False)
    options = Column(JSON, nullable=True)  # For choice type attributes
    validation_rules = Column(
        JSON, nullable=True
    )  # Min/max values, regex patterns, etc.
    display_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    product_type = relationship("ProductType", back_populates="attribute_definitions")
    values = relationship(
        "ProductAttributeValue", back_populates="attribute_definition"
    )

    __table_args__ = ({"schema": None},)

    def __repr__(self):
        return f"<AttributeDefinition(name='{self.name}', type='{self.data_type}')>"


class Product(Base):
    """Generic product model that can represent any product type."""

    __tablename__ = "products"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    product_type_id = Column(
        UUID(as_uuid=True), ForeignKey("product_types.id"), nullable=False
    )
    external_id = Column(
        String(100), nullable=True
    )  # For integration with external systems
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    brand = Column(String(200), nullable=True)
    model = Column(String(200), nullable=True)
    price_cents = Column(Integer, nullable=True)
    currency = Column(String(3), default="EUR", nullable=False)
    image_url = Column(String(1000), nullable=True)
    product_url = Column(String(1000), nullable=True)
    availability_status = Column(String(50), default="in_stock", nullable=False)
    stock_level = Column(Integer, default=0, nullable=False)
    product_metadata = Column(JSON, nullable=True)  # Additional flexible data
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    product_type = relationship("ProductType", back_populates="products")
    attribute_values = relationship("ProductAttributeValue", back_populates="product")

    def __repr__(self):
        type_name = self.product_type.name if self.product_type else None
        return f"<Product(name='{self.name}', type='{type_name}')>"

    # Price is stored as cents in price_cents column
    # Use price_cents / 100 to get euros, price_cents * 100 to store euros


class ProductAttributeValue(Base):
    """Values for product attributes."""

    __tablename__ = "product_attribute_values"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    attribute_definition_id = Column(
        UUID(as_uuid=True), ForeignKey("attribute_definitions.id"), nullable=False
    )
    string_value = Column(Text, nullable=True)
    number_value = Column(Float, nullable=True)
    boolean_value = Column(Boolean, nullable=True)
    json_value = Column(JSON, nullable=True)  # For complex values
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    product = relationship("Product", back_populates="attribute_values")
    attribute_definition = relationship("AttributeDefinition", back_populates="values")

    def __repr__(self):
        attr_name = (
            self.attribute_definition.name if self.attribute_definition else None
        )
        return f"<ProductAttributeValue(product_id='{self.product_id}', attr='{attr_name}')>"

    @property
    def value(self) -> Any:
        """Get the actual value based on data type."""
        if self.attribute_definition:
            data_type = self.attribute_definition.data_type
            if data_type == "string":
                return self.string_value
            elif data_type == "number":
                return self.number_value
            elif data_type == "boolean":
                return self.boolean_value
            elif data_type in ["choice", "range"]:
                return self.string_value
            else:
                return self.json_value
        return None

    @value.setter
    def value(self, val: Any):
        """Set the value based on data type."""
        if not self.attribute_definition:
            return

        data_type = self.attribute_definition.data_type
        if data_type == "string":
            self.string_value = str(val) if val is not None else None
        elif data_type == "number":
            self.number_value = float(val) if val is not None else None
        elif data_type == "boolean":
            self.boolean_value = bool(val) if val is not None else None
        else:
            # For choice, range, and other complex types
            if isinstance(val, (list, dict)):
                self.json_value = val
            else:
                self.string_value = str(val) if val is not None else None
