"""Static attribute catalog used for conversation and LLM prompts.

The project previously loaded attribute metadata from a local PostgreSQL
instance. To keep the conversation flow intact without a bundled database,
we define a small static catalog that captures the supported product types
and their key attributes. The structures here are intentionally simple so
future integrations can swap them for dynamic providers (e.g. an HTTP API
backed by the external database container).
"""

from __future__ import annotations

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


# Minimal but descriptive catalog that mirrors the old seed data.
_PRODUCT_TYPES: Dict[str, ProductType] = {
    "printers": ProductType(
        name="printers",
        display_name="Printers",
        description="Inkjet en laser printers voor kantoor en thuisgebruik",
        attributes=[
            AttributeDefinition(
                name="budget",
                display_name="Budget",
                question="Wat is je budget voor een printer?",
                type="number",
                required=True,
                description="Maximale prijs in euro's"
            ),
            AttributeDefinition(
                name="brand",
                display_name="Merk",
                question="Heb je een voorkeur voor een merk, zoals HP of Canon?",
                type="choice",
                options=["HP", "Canon", "Brother", "Epson"],
                description="Voorkeursmerk van de gebruiker"
            ),
            AttributeDefinition(
                name="technology",
                display_name="Printtechnologie",
                question="Welke printtechnologie zoek je (inkjet of laser)?",
                type="choice",
                options=["inkjet", "laser"],
                description="Voorkeursprinttechnologie"
            ),
        ],
    ),
    "laptops": ProductType(
        name="laptop",
        display_name="Laptops",
        description="Draagbare computers voor dagelijks gebruik",
        attributes=[
            AttributeDefinition(
                name="budget",
                display_name="Budget",
                question="Wat is je budget voor een laptop?",
                type="number",
                required=True,
                description="Maximale prijs in euro's"
            ),
            AttributeDefinition(
                name="brand",
                display_name="Merk",
                question="Heb je een voorkeursmerk, zoals Dell of Apple?",
                type="choice",
                options=["Dell", "Apple", "Lenovo", "ASUS", "HP"],
                description="Voorkeursmerk van de gebruiker"
            ),
            AttributeDefinition(
                name="screen_size",
                display_name="Schermgrootte",
                question="Welke schermgrootte zoek je?",
                type="number",
                description="Gewenste schermgrootte in inches"
            ),
        ],
    ),
    "smartphones": ProductType(
        name="smartphone",
        display_name="Smartphones",
        description="Mobiele telefoons voor communicatie en entertainment",
        attributes=[
            AttributeDefinition(
                name="budget",
                display_name="Budget",
                question="Wat is je budget voor een smartphone?",
                type="number",
                required=True,
                description="Maximale prijs in euro's"
            ),
            AttributeDefinition(
                name="brand",
                display_name="Merk",
                question="Welk merk prefereer je (bijvoorbeeld Samsung of Apple)?",
                type="choice",
                options=["Samsung", "Apple", "Google", "OnePlus"],
                description="Voorkeursmerk van de gebruiker"
            ),
            AttributeDefinition(
                name="screen_size",
                display_name="Schermgrootte",
                question="Welke schermgrootte wil je?",
                type="number",
                description="Gewenste schermgrootte in inches"
            ),
        ],
    ),
    "computers": ProductType(
        name="computer",
        display_name="Computers",
        description="Desktop computers voor werk en gaming",
        attributes=[
            AttributeDefinition(
                name="budget",
                display_name="Budget",
                question="Wat is je budget voor een computer?",
                type="number",
                required=True,
                description="Maximale prijs in euro's"
            ),
            AttributeDefinition(
                name="brand",
                display_name="Merk",
                question="Heb je een voorkeursmerk voor de computer?",
                type="choice",
                options=["HP", "Dell", "Lenovo", "Acer"],
                description="Voorkeursmerk van de gebruiker"
            ),
            AttributeDefinition(
                name="processor",
                display_name="Processor",
                question="Welke processor heeft je voorkeur (bijv. Intel i7 of AMD Ryzen)?",
                type="choice",
                options=["Intel", "AMD"],
                description="Gewenste processorfamilie"
            ),
        ],
    ),
}


DEFAULT_SCHEMA_DESCRIPTION = """
Table: products
Columns:
- id (uuid): unieke identifier
- name (text): productnaam
- description (text): korte omschrijving
- price_cents (integer): prijs in eurocenten
- currency (text): valutacode, standaard 'EUR'
- product_type_id (uuid): verwijzing naar het producttype
- created_at (timestamp): aanmaakdatum
- updated_at (timestamp): laatst bijgewerkt

Table: product_types
Columns:
- id (uuid)
- name (text)
- display_name (text)
- description (text)
- is_active (boolean)

Table: attribute_definitions
Columns:
- id (uuid)
- name (text)
- display_name (text)
- canonical_name (text)
- data_type (text)
- is_required (boolean)
- product_type_id (uuid)

Table: product_attribute_values
Columns:
- id (uuid)
- product_id (uuid)
- attribute_definition_id (uuid)
- value (text)
""".strip()


def list_product_types() -> Iterable[ProductType]:
    return _PRODUCT_TYPES.values()


def get_product_type(name: str) -> Optional[ProductType]:
    return _PRODUCT_TYPES.get(name)


def get_attribute_definitions(category: str) -> List[AttributeDefinition]:
    product_type = _PRODUCT_TYPES.get(category)
    if product_type:
        return product_type.attributes
    # The legacy naming used singular identifiers in some places
    for candidate in _PRODUCT_TYPES.values():
        if candidate.name == category:
            return candidate.attributes
    return []


def list_attribute_names(category: str) -> List[str]:
    return [attr.name for attr in get_attribute_definitions(category)]


def get_schema_description() -> str:
    return DEFAULT_SCHEMA_DESCRIPTION
