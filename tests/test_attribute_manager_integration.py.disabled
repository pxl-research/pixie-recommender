from sqlalchemy.orm import Session

from pixie.core.utils.attributes import AttributeManager


class TestAttributeManagerIntegration:
    """Integration tests for AttributeManager with database."""

    def test_get_attributes_for_category(self, seeded_test_session: Session):
        """Test getting attributes for a specific category."""
        manager = AttributeManager()

        # Test printers category
        printer_attrs = manager.get_attributes_for_category("printers")

        assert len(printer_attrs) == 3
        attr_names = [attr["name"] for attr in printer_attrs]
        assert "budget" in attr_names
        assert "brand" in attr_names
        assert "technology" in attr_names

        # Verify attribute structure
        budget_attr = next(attr for attr in printer_attrs if attr["name"] == "budget")
        assert budget_attr["question"] == "Wat is je budget?"
        assert budget_attr["type"] == "range"

    def test_get_attributes_for_nonexistent_category(
        self, seeded_test_session: Session
    ):
        """Test getting attributes for a non-existent category."""
        manager = AttributeManager()

        attrs = manager.get_attributes_for_category("nonexistent")

        assert attrs == []

    def test_get_next_missing_attribute(self, seeded_test_session: Session):
        """Test finding the next missing attribute."""
        manager = AttributeManager()

        # Test with empty context
        next_attr = manager.get_next_missing_attribute("printers", {})
        assert next_attr is not None
        assert next_attr["name"] == "budget"

        # Test with partial context
        context = {"budget": "1000"}
        next_attr = manager.get_next_missing_attribute("printers", context)
        assert next_attr is not None
        assert next_attr["name"] == "brand"

        # Test with all attributes collected
        context = {"budget": "1000", "brand": "HP", "technology": "Laser"}
        next_attr = manager.get_next_missing_attribute("printers", context)
        assert next_attr is None

    def test_get_attribute_question(self, seeded_test_session: Session):
        """Test getting question for an attribute."""
        manager = AttributeManager()

        attribute = {"name": "budget", "question": "Wat is je budget?", "type": "range"}

        question = manager.get_attribute_question(attribute)
        assert question == "Wat is je budget?"

        # Test with missing question
        attribute_no_question = {"name": "test", "type": "choice"}
        question = manager.get_attribute_question(attribute_no_question)
        assert question == "What is your preference for test?"

    def test_get_available_categories(self, seeded_test_session: Session):
        """Test getting all available categories."""
        manager = AttributeManager()

        categories = manager.get_available_categories()

        assert len(categories) == 4
        assert "printers" in categories
        assert "laptops" in categories
        assert "computers" in categories
        assert "smartphones" in categories

    def test_cache_invalidation(self, seeded_test_session: Session):
        """Test that cache invalidation works properly."""
        manager = AttributeManager()

        # Load categories to populate cache
        categories1 = manager.get_available_categories()
        assert len(categories1) == 4

        # Invalidate cache
        manager.invalidate_cache()

        # Cache should be reloaded
        categories2 = manager.get_available_categories()
        assert len(categories2) == 4
        assert categories1 == categories2

    def test_laptops_category_attributes(self, seeded_test_session: Session):
        """Test attributes for laptops category."""
        manager = AttributeManager()

        laptop_attrs = manager.get_attributes_for_category("laptops")

        assert len(laptop_attrs) == 2
        attr_names = [attr["name"] for attr in laptop_attrs]
        assert "budget" in attr_names
        assert "screen_size" in attr_names

        # Verify screen_size attribute
        screen_attr = next(
            attr for attr in laptop_attrs if attr["name"] == "screen_size"
        )
        assert screen_attr["type"] == "choice"
        assert "13 inch" in screen_attr["options"]
