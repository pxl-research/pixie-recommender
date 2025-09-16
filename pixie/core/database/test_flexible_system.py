"""Test script for flexible product system."""

import logging

from .connection import get_db_session
from .repositories.flexible_repositories import (
    get_attribute_definition_repository,
    get_product_attribute_value_repository,
    get_product_repository,
    get_product_type_repository,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_product_types():
    """Test product type operations."""
    logger.info("Testing product type operations...")

    with get_db_session() as session:
        repo = get_product_type_repository(session)

        # Get all product types
        product_types = repo.get_all()
        logger.info(f"Found {len(product_types)} product types")

        for pt in product_types:
            logger.info(f"- {pt.name}: {pt.display_name}")

        # Test getting by name
        laptop_type = repo.get_by_name("laptop")
        if laptop_type:
            logger.info(f"Found laptop type: {laptop_type.display_name}")
        else:
            logger.warning("Laptop type not found")


def test_attribute_definitions():
    """Test attribute definition operations."""
    logger.info("Testing attribute definition operations...")

    with get_db_session() as session:
        pt_repo = get_product_type_repository(session)
        attr_repo = get_attribute_definition_repository(session)

        # Get laptop type
        laptop_type = pt_repo.get_by_name("laptop")
        if not laptop_type:
            logger.error("Laptop type not found, skipping attribute tests")
            return

        # Get attributes for laptop
        attributes = attr_repo.get_by_product_type(laptop_type.id)
        logger.info(f"Found {len(attributes)} attributes for laptop")

        for attr in attributes:
            logger.info(f"- {attr.name}: {attr.display_name} ({attr.data_type})")


def test_products():
    """Test product operations."""
    logger.info("Testing product operations...")

    with get_db_session() as session:
        product_repo = get_product_repository(session)

        # Get all products
        products = product_repo.get_all()
        logger.info(f"Found {len(products)} products")

        for product in products:
            logger.info(f"- {product.name} ({product.product_type.name})")

        # Test search
        dell_products = product_repo.search_by_name("Dell")
        logger.info(f"Found {len(dell_products)} Dell products")


def test_attribute_values():
    """Test attribute value operations."""
    logger.info("Testing attribute value operations...")

    with get_db_session() as session:
        product_repo = get_product_repository(session)
        attr_value_repo = get_product_attribute_value_repository(session)

        # Get first product
        products = product_repo.get_all()
        if not products:
            logger.warning("No products found, skipping attribute value tests")
            return

        product = products[0]
        logger.info(f"Testing attribute values for: {product.name}")

        # Get all attribute values for this product
        values = attr_value_repo.get_by_product(product.id)
        logger.info(f"Found {len(values)} attribute values")

        for value in values:
            attr_name = value.attribute_definition.name
            logger.info(f"- {attr_name}: {value.value}")


def test_flexible_product_creation():
    """Test creating a new product type and products dynamically."""
    logger.info("Testing flexible product creation...")

    with get_db_session() as session:
        pt_repo = get_product_type_repository(session)
        attr_repo = get_attribute_definition_repository(session)
        product_repo = get_product_repository(session)
        attr_value_repo = get_product_attribute_value_repository(session)

        # Create a new product type
        tablet_type = pt_repo.create(
            {
                "name": "tablet",
                "display_name": "Tablet",
                "description": "Portable tablet devices",
            }
        )
        logger.info(f"Created new product type: {tablet_type.name}")

        # Create attributes for tablets
        attributes_data = [
            {
                "name": "operating_system",
                "display_name": "Operating System",
                "data_type": "choice",
                "is_required": True,
                "options": ["Android", "iOS"],
                "product_type_id": tablet_type.id,
                "display_order": 1,
            },
            {
                "name": "screen_size_inches",
                "display_name": "Screen Size (inches)",
                "data_type": "number",
                "is_required": True,
                "validation_rules": {"min": 7, "max": 13},
                "product_type_id": tablet_type.id,
                "display_order": 2,
            },
        ]

        created_attributes = []
        for attr_data in attributes_data:
            attr = attr_repo.create(attr_data)
            created_attributes.append(attr)
            logger.info(f"Created attribute: {attr.name}")

        # Create a tablet product
        tablet = product_repo.create(
            {
                "product_type_id": tablet_type.id,
                "external_id": "IPAD-AIR-1",
                "name": "iPad Air",
                "description": "Apple's versatile tablet",
                "brand": "Apple",
                "model": "iPad Air",
                "price_cents": 59900,  # €599.00
            }
        )
        logger.info(f"Created tablet product: {tablet.name}")

        # Set attribute values
        attr_lookup = {attr.name: attr for attr in created_attributes}
        attr_value_repo.set_value(tablet.id, attr_lookup["operating_system"].id, "iOS")
        attr_value_repo.set_value(tablet.id, attr_lookup["screen_size_inches"].id, 10.9)

        logger.info("Set attribute values for tablet")


def run_all_tests():
    """Run all tests."""
    logger.info("Starting flexible product system tests...")

    try:
        test_product_types()
        print()

        test_attribute_definitions()
        print()

        test_products()
        print()

        test_attribute_values()
        print()

        test_flexible_product_creation()
        print()

        logger.info("All tests completed successfully!")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
