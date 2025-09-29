"""Database seeding script for flexible product system."""

import logging
from typing import Dict, List
from uuid import UUID

from .connection import get_db_session
from .models.base import AttributeDefinition, ProductType
from .repositories.flexible_repositories import (
    get_dynamic_repository,
)

logger = logging.getLogger(__name__)


def seed_product_types_with_session(session) -> List[ProductType]:
    """Seed initial product types using provided session."""
    logger.info("Seeding product types...")

    product_types_data = [
        {
            "name": "laptop",
            "display_name": "Laptop",
            "description": "Portable computers for work and entertainment",
            "is_active": True,
        },
        {
            "name": "smartphone",
            "display_name": "Smartphone",
            "description": "Mobile phones with advanced computing capabilities",
            "is_active": True,
        },
        {
            "name": "headphones",
            "display_name": "Headphones",
            "description": "Audio devices for listening to music and calls",
            "is_active": True,
        },
        {
            "name": "monitor",
            "display_name": "Monitor",
            "description": "Display devices for computers",
            "is_active": True,
        },
        {
            "name": "printers",
            "display_name": "Printers", 
            "description": "Various types of printers including inkjet and laser",
            "is_active": True,
        },
    ]

    created_types = []
    repo = get_dynamic_repository(session, "product_types")
    for pt_data in product_types_data:
        # Check if already exists
        existing = repo.find_by_column("name", pt_data["name"])
        if existing:
            logger.info(f"Product type '{pt_data['name']}' already exists")
            created_types.append(existing[0] if existing else None)
            continue
        if existing:
            logger.info(f"Product type '{pt_data['name']}' already exists")
            created_types.append(existing)
            continue

        pt = repo.create(pt_data)
        created_types.append(pt)
        logger.info(f"Created product type: {pt.name}")

    return created_types


def seed_attribute_definitions_with_session(
    session, product_types: List[ProductType]
) -> Dict[str, List[AttributeDefinition]]:
    """Seed attribute definitions for each product type."""
    logger.info("Seeding attribute definitions...")

    # Map product type names to their attribute definitions
    attributes_data = {
        "laptop": [
            {
                "name": "processor",
                "display_name": "Processor",
                "data_type": "choice",
                "is_required": True,
                "options": [
                    "Intel Core i3",
                    "Intel Core i5",
                    "Intel Core i7",
                    "Intel Core i9",
                    "AMD Ryzen 3",
                    "AMD Ryzen 5",
                    "AMD Ryzen 7",
                    "AMD Ryzen 9",
                ],
                "display_order": 1,
            },
            {
                "name": "ram_gb",
                "display_name": "RAM (GB)",
                "data_type": "number",
                "is_required": True,
                "validation_rules": {"min": 4, "max": 128},
                "display_order": 2,
            },
            {
                "name": "storage_gb",
                "display_name": "Storage (GB)",
                "data_type": "number",
                "is_required": True,
                "validation_rules": {"min": 128, "max": 4000},
                "display_order": 3,
            },
            {
                "name": "screen_size_inches",
                "display_name": "Screen Size (inches)",
                "data_type": "number",
                "is_required": True,
                "validation_rules": {"min": 11, "max": 17},
                "display_order": 4,
            },
            {
                "name": "has_touchscreen",
                "display_name": "Touchscreen",
                "data_type": "boolean",
                "is_required": False,
                "display_order": 5,
            },
        ],
        "smartphone": [
            {
                "name": "operating_system",
                "display_name": "Operating System",
                "data_type": "choice",
                "is_required": True,
                "options": ["Android", "iOS"],
                "display_order": 1,
            },
            {
                "name": "storage_gb",
                "display_name": "Storage (GB)",
                "data_type": "choice",
                "is_required": True,
                "options": ["64", "128", "256", "512", "1024"],
                "display_order": 2,
            },
            {
                "name": "ram_gb",
                "display_name": "RAM (GB)",
                "data_type": "number",
                "is_required": True,
                "validation_rules": {"min": 2, "max": 16},
                "display_order": 3,
            },
            {
                "name": "screen_size_inches",
                "display_name": "Screen Size (inches)",
                "data_type": "number",
                "is_required": True,
                "validation_rules": {"min": 4.7, "max": 7.0},
                "display_order": 4,
            },
            {
                "name": "camera_mp",
                "display_name": "Camera (MP)",
                "data_type": "number",
                "is_required": False,
                "validation_rules": {"min": 8, "max": 200},
                "display_order": 5,
            },
        ],
        "headphones": [
            {
                "name": "type",
                "display_name": "Type",
                "data_type": "choice",
                "is_required": True,
                "options": ["Over-ear", "On-ear", "In-ear", "Ear buds"],
                "display_order": 1,
            },
            {
                "name": "wireless",
                "display_name": "Wireless",
                "data_type": "boolean",
                "is_required": True,
                "display_order": 2,
            },
            {
                "name": "noise_cancelling",
                "display_name": "Noise Cancelling",
                "data_type": "boolean",
                "is_required": False,
                "display_order": 3,
            },
            {
                "name": "battery_life_hours",
                "display_name": "Battery Life (hours)",
                "data_type": "number",
                "is_required": False,
                "validation_rules": {"min": 1, "max": 100},
                "display_order": 4,
            },
        ],
        "monitor": [
            {
                "name": "screen_size_inches",
                "display_name": "Screen Size (inches)",
                "data_type": "number",
                "is_required": True,
                "validation_rules": {"min": 19, "max": 49},
                "display_order": 1,
            },
            {
                "name": "resolution",
                "display_name": "Resolution",
                "data_type": "choice",
                "is_required": True,
                "options": ["1920x1080", "2560x1440", "3840x2160", "5120x2880"],
                "display_order": 2,
            },
            {
                "name": "refresh_rate_hz",
                "display_name": "Refresh Rate (Hz)",
                "data_type": "number",
                "is_required": True,
                "validation_rules": {"min": 60, "max": 240},
                "display_order": 3,
            },
            {
                "name": "panel_type",
                "display_name": "Panel Type",
                "data_type": "choice",
                "is_required": False,
                "options": ["IPS", "TN", "VA", "OLED"],
                "display_order": 4,
            },
        ],
        # Add printers attributes via seed (present in JSON fallback but not earlier)
        "printers": [
            {
                "name": "pages_per_minute",
                "display_name": "Pages per minute",
                "data_type": "number",
                "is_required": False,
                "display_order": 5,
                "canonical_name": "pages_per_minute",
            },
            {
                "name": "print_type",
                "display_name": "Print technology",
                "data_type": "choice",
                "is_required": False,
                "display_order": 3,
                "canonical_name": "technology",
            },
            {
                "name": "color_support",
                "display_name": "Color support",
                "data_type": "choice",
                "is_required": False,
                "display_order": 4,
                "canonical_name": "color",
            },
            {
                "name": "brand",
                "display_name": "Brand",
                "data_type": "choice",
                "is_required": False,
                "display_order": 2,
                "canonical_name": "brand",
            },
            {
                "name": "budget",
                "display_name": "Budget",
                "data_type": "number",
                "is_required": True,
                "display_order": 1,
                "canonical_name": "budget",
            },
        ],
    }

    created_attributes = {}
    attr_repo = get_dynamic_repository(session, "attribute_definitions")

    for pt in product_types:
        pt_attributes = []
        pt_name = str(pt.name)  # Convert to string
        if pt_name in attributes_data:
            for attr_data in attributes_data[pt_name]:
                # Check if already exists
                existing_list = attr_repo.filter_by_attributes(
                    {"name": attr_data["name"], "product_type_id": str(pt.id)}
                )
                existing = existing_list[0] if existing_list else None
                if existing:
                    logger.info(
                        f"Attribute '{attr_data['name']}' already exists for {pt_name}"
                    )
                    pt_attributes.append(existing)
                    continue

                attr_data_copy = attr_data.copy()
                attr_data_copy["product_type_id"] = UUID(str(pt.id))
                # Preserve optional canonical_name when present
                if "canonical_name" in attr_data:
                    attr_data_copy["canonical_name"] = attr_data["canonical_name"]
                attr = attr_repo.create(attr_data_copy)
                pt_attributes.append(attr)
                logger.info(f"Created attribute '{attr.name}' for {pt_name}")

        created_attributes[pt_name] = pt_attributes

    return created_attributes


def seed_sample_products_with_session(
    session,
    product_types: List[ProductType],
    attributes: Dict[str, List[AttributeDefinition]],
) -> None:
    """Seed sample products for each product type."""
    logger.info("Seeding sample products...")

    # Sample products data
    products_data = {
        "laptop": [
            {
                "external_id": "DELL-XPS-13-1",
                "name": "Dell XPS 13",
                "description": "Ultra-portable laptop with stunning display",
                "brand": "Dell",
                "model": "XPS 13",
                "price_cents": 129900,  # €1299.00
                "attributes": {
                    "processor": "Intel Core i7",
                    "ram_gb": 16,
                    "storage_gb": 512,
                    "screen_size_inches": 13.3,
                    "has_touchscreen": True,
                },
            },
            {
                "external_id": "MAC-MACBOOK-AIR-1",
                "name": "MacBook Air M2",
                "description": "Apple's thinnest laptop with M2 chip",
                "brand": "Apple",
                "model": "MacBook Air",
                "price_cents": 119900,  # €1199.00
                "attributes": {
                    "processor": "Apple M2",
                    "ram_gb": 8,
                    "storage_gb": 256,
                    "screen_size_inches": 13.6,
                    "has_touchscreen": False,
                },
            },
        ],
        "smartphone": [
            {
                "external_id": "IPHONE-14-PRO-1",
                "name": "iPhone 14 Pro",
                "description": "Latest iPhone with Dynamic Island",
                "brand": "Apple",
                "model": "iPhone 14 Pro",
                "price_cents": 129900,  # €1299.00
                "attributes": {
                    "operating_system": "iOS",
                    "storage_gb": "256",
                    "ram_gb": 6,
                    "screen_size_inches": 6.1,
                    "camera_mp": 48,
                },
            },
            {
                "external_id": "SAMSUNG-S23-ULTRA-1",
                "name": "Samsung Galaxy S23 Ultra",
                "description": "Android flagship with S Pen",
                "brand": "Samsung",
                "model": "Galaxy S23 Ultra",
                "price_cents": 119900,  # €1199.00
                "attributes": {
                    "operating_system": "Android",
                    "storage_gb": "512",
                    "ram_gb": 12,
                    "screen_size_inches": 6.8,
                    "camera_mp": 200,
                },
            },
        ],
        "headphones": [
            {
                "external_id": "SONY-WH-1000XM5-1",
                "name": "Sony WH-1000XM5",
                "description": "Industry-leading noise cancelling headphones",
                "brand": "Sony",
                "model": "WH-1000XM5",
                "price_cents": 34900,  # €349.00
                "attributes": {
                    "type": "Over-ear",
                    "wireless": True,
                    "noise_cancelling": True,
                    "battery_life_hours": 30,
                },
            },
        ],
        "monitor": [
            {
                "external_id": "LG-27UK650-W-1",
                "name": "LG 27UK650-W",
                "description": "27-inch 4K UHD IPS monitor",
                "brand": "LG",
                "model": "27UK650-W",
                "price_cents": 34900,  # €349.00
                "attributes": {
                    "screen_size_inches": 27,
                    "resolution": "3840x2160",
                    "refresh_rate_hz": 60,
                    "panel_type": "IPS",
                },
            },
        ],
        "printers": [
            {
                "external_id": "BROTHER-XC-2570-1",
                "name": "Brother XC 2570",
                "description": "Reliable laser printer for home and office use",
                "brand": "Brother", 
                "model": "XC 2570",
                "price_cents": 19900,  # €199.00
                "attributes": {
                    "print_type": "laser",
                    "color_support": "monochrome", 
                    "pages_per_minute": 28,
                    "brand": "Brother",
                    "budget": 19900,
                },
            },
            {
                "external_id": "BROTHER-XT-3560-1", 
                "name": "Brother XT 3560",
                "description": "Compact laser printer with wireless connectivity",
                "brand": "Brother",
                "model": "XT 3560", 
                "price_cents": 15900,  # €159.00
                "attributes": {
                    "print_type": "laser",
                    "color_support": "monochrome",
                    "pages_per_minute": 32,
                    "brand": "Brother",
                    "budget": 15900,
                },
            },
            {
                "external_id": "HP-LASERJET-PRO-1",
                "name": "HP LaserJet Pro M404n",
                "description": "Professional laser printer with fast printing speeds",
                "brand": "HP",
                "model": "LaserJet Pro M404n",
                "price_cents": 17900,  # €179.00
                "attributes": {
                    "print_type": "laser", 
                    "color_support": "monochrome",
                    "pages_per_minute": 40,
                    "brand": "HP",
                    "budget": 17900,
                },
            },
            {
                "external_id": "CANON-INKJET-1",
                "name": "Canon PIXMA TS3350",
                "description": "All-in-one inkjet printer for home use", 
                "brand": "Canon",
                "model": "PIXMA TS3350",
                "price_cents": 8900,  # €89.00
                "attributes": {
                    "print_type": "inkjet",
                    "color_support": "color",
                    "pages_per_minute": 15,
                    "brand": "Canon", 
                    "budget": 8900,
                },
            },
        ],
    }

    product_repo = get_dynamic_repository(session, "products")
    attr_value_repo = get_dynamic_repository(session, "product_attribute_values")

    for pt in product_types:
        pt_name = str(pt.name)  # Explicit string conversion
        if pt_name in products_data:
            pt_attributes = attributes.get(pt_name, [])

            # Create attribute definition lookup
            attr_lookup = {str(attr.name): attr for attr in pt_attributes}

            for product_data in products_data[pt_name]:
                # Check if product already exists
                existing = product_repo.get_by_external_id(product_data["external_id"])
                if existing:
                    logger.info(f"Product '{product_data['name']}' already exists")
                    continue

                # Create product
                product_attrs = product_data.copy()
                product_attrs["product_type_id"] = UUID(str(pt.id))
                del product_attrs["attributes"]

                product = product_repo.create(product_attrs)
                logger.info(f"Created product: {product.name}")

                # Create attribute values
                for attr_name, value in product_data["attributes"].items():
                    if attr_name in attr_lookup:
                        attr_def = attr_lookup[attr_name]
                        attr_value_repo.set_value(
                            UUID(str(product.id)), UUID(str(attr_def.id)), value
                        )
                        logger.info(f"Set {attr_name} = {value} for {product.name}")


def seed_database() -> None:
    """Main function to seed the database with initial data."""
    logger.info("Starting database seeding...")

    try:
        with get_db_session() as session:
            # Seed product types
            product_types = seed_product_types_with_session(session)

            # Seed attribute definitions
            attributes = seed_attribute_definitions_with_session(session, product_types)

            # Seed sample products
            seed_sample_products_with_session(session, product_types, attributes)

        logger.info("Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise


if __name__ == "__main__":
    # Run seeding when script is executed directly
    seed_database()
