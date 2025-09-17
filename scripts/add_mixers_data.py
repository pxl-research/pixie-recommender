#!/usr/bin/env python3
"""
Script to add mixers data to the PostgreSQL database.
This tests the flexible repository system by adding a new product category.
"""

import json
import os
import sys
from datetime import datetime
from uuid import uuid4

import psycopg2
from psycopg2.extras import RealDictCursor

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host="localhost",
        port="5432",
        database="pixie_dev",
        user="pixie_user",
        password="pixie_password",
    )


def add_mixers_data():
    """Add mixers product type, attributes, and sample products."""

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. Create mixer product type
        mixer_type_id = str(uuid4())
        now = datetime.now()

        print("Creating mixer product type...")
        cur.execute(
            """
            INSERT INTO product_types 
            (id, name, display_name, description, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
            (
                mixer_type_id,
                "mixer",
                "Mixer",
                "Kitchen mixers for food preparation",
                True,
                now,
                now,
            ),
        )

        # 2. Create attribute definitions for mixers
        print("Creating mixer attribute definitions...")

        attributes = [
            {
                "name": "budget",
                "display_name": "Budget",
                "description": "Maximum budget for the mixer",
                "data_type": "range",
                "is_required": False,
                "is_searchable": True,
                "is_filterable": True,
                "options": json.dumps(
                    {"min": 50, "max": 2000, "step": 10, "unit": "€"}
                ),
                "display_order": 1,
            },
            {
                "name": "type",
                "display_name": "Mixer Type",
                "description": "Type of mixer",
                "data_type": "choice",
                "is_required": False,
                "is_searchable": True,
                "is_filterable": True,
                "options": json.dumps(
                    [
                        "Handmixer",
                        "Staafmixer",
                        "Planetmixer",
                        "Blender",
                        "Keukenmachine",
                    ]
                ),
                "display_order": 2,
            },
            {
                "name": "power",
                "display_name": "Power",
                "description": "Motor power in watts",
                "data_type": "choice",
                "is_required": False,
                "is_searchable": True,
                "is_filterable": True,
                "options": json.dumps(
                    ["200-400W", "400-600W", "600-800W", "800-1000W", "1000W+"]
                ),
                "display_order": 3,
            },
            {
                "name": "brand",
                "display_name": "Brand",
                "description": "Mixer brand",
                "data_type": "choice",
                "is_required": False,
                "is_searchable": True,
                "is_filterable": True,
                "options": json.dumps(
                    [
                        "KitchenAid",
                        "Bosch",
                        "Philips",
                        "Braun",
                        "Kenwood",
                        "Smeg",
                        "Sage",
                    ]
                ),
                "display_order": 4,
            },
            {
                "name": "bowl_capacity",
                "display_name": "Bowl Capacity",
                "description": "Mixing bowl capacity in liters",
                "data_type": "choice",
                "is_required": False,
                "is_searchable": True,
                "is_filterable": True,
                "options": json.dumps(["1-2L", "3-4L", "5-6L", "7L+"]),
                "display_order": 5,
            },
            {
                "name": "attachments",
                "display_name": "Attachments",
                "description": "Available attachments",
                "data_type": "choice",
                "is_required": False,
                "is_searchable": True,
                "is_filterable": True,
                "options": json.dumps(
                    [
                        "Deeghaak",
                        "Garde",
                        "Platte beater",
                        "Blender attachment",
                        "Vleesmolen",
                        "Pasta roller",
                    ]
                ),
                "display_order": 6,
            },
        ]

        attribute_ids = {}
        for attr in attributes:
            attr_id = str(uuid4())
            attribute_ids[attr["name"]] = attr_id

            cur.execute(
                """
                INSERT INTO attribute_definitions 
                (id, product_type_id, name, display_name, description, data_type, 
                 is_required, is_searchable, is_filterable, options, validation_rules, 
                 display_order, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    attr_id,
                    mixer_type_id,
                    attr["name"],
                    attr["display_name"],
                    attr["description"],
                    attr["data_type"],
                    attr["is_required"],
                    attr["is_searchable"],
                    attr["is_filterable"],
                    (
                        json.dumps(attr["options"])
                        if isinstance(attr["options"], (list, dict))
                        else attr["options"]
                    ),
                    None,  # validation_rules
                    attr["display_order"],
                    now,
                    now,
                ),
            )

        # 3. Create sample mixer products
        print("Creating sample mixer products...")

        mixers = [
            {
                "external_id": "MIX001",
                "name": "KitchenAid Artisan Stand Mixer",
                "description": "Iconische planetmixer met 4,8L roestvrijstalen kom",
                "brand": "KitchenAid",
                "model": "5KSM175PS",
                "price_cents": 59999,  # €599.99
                "image_url": "https://example.com/kitchenaid-artisan.jpg",
                "product_url": "https://example.com/product/kitchenaid-artisan",
                "attributes": {
                    "type": "Planetmixer",
                    "power": "600-800W",
                    "brand": "KitchenAid",
                    "bowl_capacity": "5-6L",
                    "attachments": "Deeghaak",
                },
            },
            {
                "external_id": "MIX002",
                "name": "Bosch MUM5 CreationLine",
                "description": "Veelzijdige keukenmachine met planetair mengwerk",
                "brand": "Bosch",
                "model": "MUM58L20",
                "price_cents": 34999,  # €349.99
                "image_url": "https://example.com/bosch-mum5.jpg",
                "product_url": "https://example.com/product/bosch-mum5",
                "attributes": {
                    "type": "Keukenmachine",
                    "power": "1000W+",
                    "brand": "Bosch",
                    "bowl_capacity": "3-4L",
                    "attachments": "Deeghaak",
                },
            },
            {
                "external_id": "MIX003",
                "name": "Philips Viva Collection Handmixer",
                "description": "Lichtgewicht handmixer met 5 snelheden",
                "brand": "Philips",
                "model": "HR3741/00",
                "price_cents": 4999,  # €49.99
                "image_url": "https://example.com/philips-handmixer.jpg",
                "product_url": "https://example.com/product/philips-handmixer",
                "attributes": {
                    "type": "Handmixer",
                    "power": "400-600W",
                    "brand": "Philips",
                    "bowl_capacity": "1-2L",
                    "attachments": "Garde",
                },
            },
            {
                "external_id": "MIX004",
                "name": "Braun MultiQuick 7 Staafmixer",
                "description": "Krachtige staafmixer met SmartSpeed technologie",
                "brand": "Braun",
                "model": "MQ7087X",
                "price_cents": 12999,  # €129.99
                "image_url": "https://example.com/braun-multiquick.jpg",
                "product_url": "https://example.com/product/braun-multiquick",
                "attributes": {
                    "type": "Staafmixer",
                    "power": "600-800W",
                    "brand": "Braun",
                    "bowl_capacity": "1-2L",
                    "attachments": "Blender attachment",
                },
            },
            {
                "external_id": "MIX005",
                "name": "Kenwood Chef Titanium",
                "description": "Professionele keukenmachine met titanium beslag-unit",
                "brand": "Kenwood",
                "model": "KVC7300S",
                "price_cents": 89999,  # €899.99
                "image_url": "https://example.com/kenwood-chef.jpg",
                "product_url": "https://example.com/product/kenwood-chef",
                "attributes": {
                    "type": "Planetmixer",
                    "power": "1000W+",
                    "brand": "Kenwood",
                    "bowl_capacity": "7L+",
                    "attachments": "Deeghaak",
                },
            },
            {
                "external_id": "MIX006",
                "name": "Smeg Stand Mixer Pastel Green",
                "description": "Retro design planetmixer met 4,8L kom",
                "brand": "Smeg",
                "model": "SMF03PGEU",
                "price_cents": 74999,  # €749.99
                "image_url": "https://example.com/smeg-mixer.jpg",
                "product_url": "https://example.com/product/smeg-mixer",
                "attributes": {
                    "type": "Planetmixer",
                    "power": "600-800W",
                    "brand": "Smeg",
                    "bowl_capacity": "5-6L",
                    "attachments": "Garde",
                },
            },
            {
                "external_id": "MIX007",
                "name": "Sage The Scraper Mixer Pro",
                "description": "Intelligente planetmixer met scraper beater",
                "brand": "Sage",
                "model": "BEM800BSS",
                "price_cents": 119999,  # €1199.99
                "image_url": "https://example.com/sage-mixer.jpg",
                "product_url": "https://example.com/product/sage-mixer",
                "attributes": {
                    "type": "Planetmixer",
                    "power": "1000W+",
                    "brand": "Sage",
                    "bowl_capacity": "5-6L",
                    "attachments": "Platte beater",
                },
            },
            {
                "external_id": "MIX008",
                "name": "Philips Daily Collection Blender",
                "description": "Compacte blender voor smoothies en shakes",
                "brand": "Philips",
                "model": "HR2105/00",
                "price_cents": 7999,  # €79.99
                "image_url": "https://example.com/philips-blender.jpg",
                "product_url": "https://example.com/product/philips-blender",
                "attributes": {
                    "type": "Blender",
                    "power": "400-600W",
                    "brand": "Philips",
                    "bowl_capacity": "1-2L",
                    "attachments": "Blender attachment",
                },
            },
        ]

        for mixer in mixers:
            product_id = str(uuid4())

            # Insert product
            cur.execute(
                """
                INSERT INTO products 
                (id, product_type_id, external_id, name, description, brand, model, 
                 price_cents, currency, image_url, product_url, availability_status, 
                 stock_level, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    product_id,
                    mixer_type_id,
                    mixer["external_id"],
                    mixer["name"],
                    mixer["description"],
                    mixer["brand"],
                    mixer["model"],
                    mixer["price_cents"],
                    "EUR",
                    mixer["image_url"],
                    mixer["product_url"],
                    "in_stock",
                    10,  # stock_level
                    True,
                    now,
                    now,
                ),
            )

            # Insert attribute values
            for attr_name, attr_value in mixer["attributes"].items():
                if attr_name in attribute_ids:
                    attr_value_id = str(uuid4())

                    cur.execute(
                        """
                        INSERT INTO product_attribute_values 
                        (id, product_id, attribute_definition_id, string_value, created_at, 
                        updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                        (
                            attr_value_id,
                            product_id,
                            attribute_ids[attr_name],
                            attr_value,
                            now,
                            now,
                        ),
                    )

        # Commit all changes
        conn.commit()
        print("✅ Successfully added mixers data to the database!")

        # Show summary
        cur.execute(
            "SELECT COUNT(*) FROM products WHERE product_type_id = %s", (mixer_type_id,)
        )
        product_count = cur.fetchone()[0]
        print(f"Added {product_count} mixer products")

        cur.execute(
            "SELECT COUNT(*) FROM attribute_definitions WHERE product_type_id = %s",
            (mixer_type_id,),
        )
        attr_count = cur.fetchone()[0]
        print(f"Added {attr_count} attribute definitions")

        cur.execute(
            """
            SELECT COUNT(*) FROM product_attribute_values pav
            JOIN products p ON pav.product_id = p.id
            WHERE p.product_type_id = %s
        """,
            (mixer_type_id,),
        )
        value_count = cur.fetchone()[0]
        print(f"Added {value_count} attribute values")

    except Exception as e:
        print(f"❌ Error adding mixers data: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def test_flexible_repository():
    """Test the flexible repository with mixers data."""
    print("\n🧪 Testing flexible repository with mixers...")

    try:
        # Import the flexible repository classes
        from pixie.core.database.connection import get_db_session
        from pixie.core.database.repositories.flexible_repositories import (
            discover_product_tables,
            get_dynamic_repository,
        )

        with get_db_session() as session:
            # Test table discovery
            tables = discover_product_tables(session)
            print(f"Discovered tables: {tables}")

            # Test products table access
            products_repo = get_dynamic_repository(session, "products")

            # Get all mixers
            all_products = products_repo.get_all(limit=20)
            mixer_products = [
                p
                for p in all_products
                if "mixer" in p.get("name", "").lower()
                or "blender" in p.get("name", "").lower()
            ]
            print(f"Found {len(mixer_products)} mixer products")

            # Test search functionality
            search_results = products_repo.search_text(
                "KitchenAid", ["name", "brand"], limit=5
            )
            print(f"Search for 'KitchenAid': {len(search_results)} results")

            # Test attribute filtering
            brand_filter = products_repo.filter_by_attributes(
                {"brand": "Philips"}, limit=5
            )
            print(f"Filter by brand 'Philips': {len(brand_filter)} results")

            print("✅ Flexible repository tests passed!")

    except Exception as e:
        print(f"❌ Error testing flexible repository: {e}")
        raise


if __name__ == "__main__":
    print("🔧 Adding mixers data to test flexible repository system...")
    add_mixers_data()
    test_flexible_repository()
    print(
        "\n🎉 Mixers data added successfully! You can now ask questions about mixers."
    )
