from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class AttributeDefinition:
    name: str
    display_name: str
    question: str
    type: str = "string"
    required: bool = False
    description: str = ""
    options: Optional[List[str]] = None


@dataclass(frozen=True)
class ProductType:
    name: str
    display_name: str
    description: str
    attributes: List[AttributeDefinition]


_PRODUCT_TYPES: Dict[str, ProductType] = {
    "printers": ProductType(
        name="printers",
        display_name="Printers",
        description="Inkjet en laser printers",
        attributes=[
            AttributeDefinition("budget", "Budget", "Wat is je budget voor een printer?", type="number", required=True),
            AttributeDefinition("brand", "Merk", "Heb je een voorkeur voor een merk?", type="choice", options=["HP", "Canon", "Brother", "Epson"]),
            AttributeDefinition("technology", "Printtechnologie", "Welke printtechnologie zoek je (inkjet of laser)?", type="choice", options=["inkjet", "laser"]),
        ],
    ),
    "laptops": ProductType(
        name="laptop",
        display_name="Laptops",
        description="Draagbare computers",
        attributes=[
            AttributeDefinition("budget", "Budget", "Wat is je budget voor een laptop?", type="number", required=True),
            AttributeDefinition("brand", "Merk", "Heb je een voorkeursmerk, zoals Dell of Apple?", type="choice", options=["Dell", "Apple", "Lenovo", "ASUS", "HP"]),
            AttributeDefinition("screen_size", "Schermgrootte", "Welke schermgrootte zoek je?", type="number"),
        ],
    ),
    "smartphones": ProductType(
        name="smartphone",
        display_name="Smartphones",
        description="Telefoons voor dagelijks gebruik",
        attributes=[
            AttributeDefinition("budget", "Budget", "Wat is je budget voor een smartphone?", type="number", required=True),
            AttributeDefinition("brand", "Merk", "Welk merk prefereer je?", type="choice", options=["Samsung", "Apple", "Google", "OnePlus"]),
            AttributeDefinition("screen_size", "Schermgrootte", "Welke schermgrootte wil je?", type="number"),
        ],
    ),
    "computers": ProductType(
        name="computer",
        display_name="Computers",
        description="Desktop systemen",
        attributes=[
            AttributeDefinition("budget", "Budget", "Wat is je budget voor een computer?", type="number", required=True),
            AttributeDefinition("brand", "Merk", "Heb je een voorkeursmerk voor de computer?", type="choice", options=["HP", "Dell", "Lenovo", "Acer"]),
            AttributeDefinition("processor", "Processor", "Welke processor heeft je voorkeur?", type="choice", options=["Intel", "AMD"]),
        ],
    ),
}

DEFAULT_SCHEMA_DESCRIPTION = """
Table: products (id, name, description, price_cents, currency, product_type_id, created_at, updated_at)
Table: product_types (id, name, display_name, description, is_active)
Table: attribute_definitions (id, name, display_name, canonical_name, data_type, is_required, product_type_id)
Table: product_attribute_values (id, product_id, attribute_definition_id, value)
""".strip()


def list_product_types() -> Iterable[ProductType]:
    return _PRODUCT_TYPES.values()


def get_product_type(name: str) -> Optional[ProductType]:
    return _PRODUCT_TYPES.get(name)


def get_attribute_definitions(category: str) -> List[AttributeDefinition]:
    product = _PRODUCT_TYPES.get(category)
    if product:
        return product.attributes
    for candidate in _PRODUCT_TYPES.values():
        if candidate.name == category:
            return candidate.attributes
    return []


def list_attribute_names(category: str) -> List[str]:
    return [attr.name for attr in get_attribute_definitions(category)]


def get_schema_description() -> str:
    return DEFAULT_SCHEMA_DESCRIPTION
