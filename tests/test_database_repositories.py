from sqlalchemy.orm import Session

from pixie.core.database.repositories.attribute_repository import AttributeRepository
from pixie.core.database.repositories.category_repository import CategoryRepository


class TestCategoryRepository:
    """Test cases for CategoryRepository database operations."""

    def test_get_all_categories(self, seeded_test_session: Session):
        """Test retrieving all categories from database."""
        repo = CategoryRepository(seeded_test_session)

        categories = repo.get_all()

        assert len(categories) == 4
        category_names = [cat.name for cat in categories]
        assert "printers" in category_names
        assert "laptops" in category_names
        assert "computers" in category_names
        assert "smartphones" in category_names

    def test_get_category_by_name(self, seeded_test_session: Session):
        """Test retrieving a category by name."""
        repo = CategoryRepository(seeded_test_session)

        category = repo.get_by_name("printers")

        assert category is not None
        assert category.name == "printers"
        assert category.display_name == "Printers"
        assert category.description == "Printer and multifunction devices"

    def test_get_category_by_name_not_found(self, seeded_test_session: Session):
        """Test retrieving a non-existent category."""
        repo = CategoryRepository(seeded_test_session)

        category = repo.get_by_name("nonexistent")

        assert category is None


class TestAttributeRepository:
    """Test cases for AttributeRepository database operations."""

    def test_get_attributes_by_category(self, seeded_test_session: Session):
        """Test retrieving attributes for a specific category."""
        category_repo = CategoryRepository(seeded_test_session)
        attr_repo = AttributeRepository(seeded_test_session)

        category = category_repo.get_by_name("printers")
        assert category is not None

        attributes = attr_repo.get_by_category(category.id)

        assert len(attributes) == 3
        attr_names = [attr.name for attr in attributes]
        assert "budget" in attr_names
        assert "brand" in attr_names
        assert "technology" in attr_names

    def test_get_attribute_by_name_and_category(self, seeded_test_session: Session):
        """Test retrieving a specific attribute by name and category."""
        category_repo = CategoryRepository(seeded_test_session)
        attr_repo = AttributeRepository(seeded_test_session)

        category = category_repo.get_by_name("printers")
        assert category is not None

        attribute = attr_repo.get_by_category_and_name(category.id, "budget")

        assert attribute is not None
        assert attribute.name == "budget"
        assert attribute.question == "Wat is je budget?"
        assert attribute.type == "range"

    def test_get_attribute_by_name_and_category_not_found(
        self, seeded_test_session: Session
    ):
        """Test retrieving a non-existent attribute."""
        category_repo = CategoryRepository(seeded_test_session)
        attr_repo = AttributeRepository(seeded_test_session)

        category = category_repo.get_by_name("printers")
        assert category is not None

        attribute = attr_repo.get_by_category_and_name(category.id, "nonexistent")

        assert attribute is None

    def test_get_attributes_by_type(self, seeded_test_session: Session):
        """Test retrieving attributes by type."""
        attr_repo = AttributeRepository(seeded_test_session)

        range_attributes = attr_repo.get_by_type("range")

        assert len(range_attributes) >= 1
        for attr in range_attributes:
            assert attr.type == "range"

        choice_attributes = attr_repo.get_by_type("choice")

        assert len(choice_attributes) >= 1
        for attr in choice_attributes:
            assert attr.type == "choice"
