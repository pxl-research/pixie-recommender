"""Test script to validate database models."""

import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))

try:
    # Test imports
    from pixie.core.database.models import (
        Category,
        CategorySchema,
        Printer,
        PrinterSchema,
    )

    print("✓ All models imported successfully")

    # Test model instantiation (without database connection)
    category = Category(
        name="test_category",
        display_name="Test Category",
        description="Test category for validation",
    )
    print(f"✓ Category model created: {category}")

    printer = Printer(
        name="Test Printer",
        brand="Test Brand",
        technology="laser",
        price_cents=10000,
        price=100.00,
    )
    print(f"✓ Printer model created: {printer}")

    # Test Pydantic schemas
    test_datetime = datetime(2025, 1, 1, 0, 0, 0)
    category_schema = CategorySchema(
        id=1,
        name="test",
        display_name="Test",
        created_at=test_datetime,
        updated_at=test_datetime,
    )
    print(f"✓ Category schema created: {category_schema}")

    printer_schema = PrinterSchema(
        id=1,
        name="Test Printer",
        brand="Test Brand",
        technology="laser",
        price_cents=10000,
        price=100.00,
        created_at=test_datetime,
        updated_at=test_datetime,
    )
    print(f"✓ Printer schema created: {printer_schema}")

    print("\n🎉 All database models validation passed!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Validation error: {e}")
    sys.exit(1)
