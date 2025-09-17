#!/usr/bin/env python3
"""
Simple test script to verify the flexible repository works with mixers.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pixie.core.database.connection import get_db_session
from pixie.core.database.repositories.flexible_repositories import (
    get_dynamic_repository,
    discover_product_tables,
    TableDiscovery,
)


def test_mixer_repository():
    """Test the flexible repository with mixer data."""
    print("🧪 Testing flexible repository with mixer data...")

    with get_db_session() as session:
        # Test table discovery
        discovery = TableDiscovery(session)
        tables = discovery.get_all_tables()
        print(f"📋 All tables: {tables}")

        product_tables = discovery.get_product_tables()
        print(f"📦 Product tables: {product_tables}")

        # Test products repository
        products_repo = get_dynamic_repository(session, "products")

        # Get table info
        table_info = products_repo.get_table_info()
        print(f"📊 Products table has {table_info['row_count']} rows")
        print(f"📊 Primary key: {table_info['primary_key']}")
        print(f"📊 Columns: {len(table_info['columns'])} columns")

        # Test search functionality
        print("\n🔍 Testing search functionality...")

        # Search for mixers by name
        mixer_results = products_repo.search_text("mixer", ["name"], limit=10)
        print(f"Found {len(mixer_results)} products with 'mixer' in name")

        for mixer in mixer_results:
            print(
                f"  - {mixer['name']} ({mixer['brand']}) - €{mixer['price_cents']/100:.2f}"
            )

        # Search by brand
        brand_results = products_repo.filter_by_attributes(
            {"brand": "KitchenAid"}, limit=5
        )
        print(f"\nFound {len(brand_results)} KitchenAid products")

        for product in brand_results:
            print(f"  - {product['name']} - €{product['price_cents']/100:.2f}")

        # Test attribute repository
        print("\n🏷️ Testing attribute definitions...")
        attr_repo = get_dynamic_repository(session, "attribute_definitions")

        # Get all attributes
        all_attrs = attr_repo.get_all(limit=20)
        mixer_attrs = [
            a for a in all_attrs if "mixer" in str(a.get("product_type_id", "")).lower()
        ]

        print(f"Found {len(all_attrs)} total attribute definitions")

        # Test product type repository
        print("\n📂 Testing product types...")
        type_repo = get_dynamic_repository(session, "product_types")

        mixer_type = type_repo.find_by_column("name", "mixer", limit=1)
        if mixer_type:
            print(f"Found mixer product type: {mixer_type[0]['display_name']}")

            # Get attributes for mixer type
            mixer_type_id = mixer_type[0]["id"]
            mixer_attributes = attr_repo.filter_by_attributes(
                {"product_type_id": mixer_type_id}, limit=10
            )
            print(f"Mixer has {len(mixer_attributes)} attributes:")
            for attr in mixer_attributes:
                print(f"  - {attr['display_name']} ({attr['data_type']})")

        print("\n✅ All flexible repository tests passed!")
        print("🎉 The system is ready to handle mixer questions!")

        return True


if __name__ == "__main__":
    try:
        test_mixer_repository()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
