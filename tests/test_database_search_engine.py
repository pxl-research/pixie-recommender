"""Tests for database search engine."""

from unittest.mock import Mock, patch

from pixie.core.search.database_search_engine import DatabaseSearchEngine


class TestDatabaseSearchEngine:
    """Test cases for DatabaseSearchEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DatabaseSearchEngine()

    def test_init(self):
        """Test initialization."""
        assert self.engine._default_category == "printers"
        assert self.engine._default_page_size == 10

    def test_search_empty_attributes(self):
        """Test search with empty attributes returns default results."""
        with patch.object(self.engine, '_get_default_results') as mock_default:
            mock_default.return_value = [{"id": 1, "name": "Test Item", "price": 100.0}]

            result = self.engine.search("SELECT * FROM items", None)

            mock_default.assert_called_once_with("printers")
            assert result == [{"id": 1, "name": "Test Item", "price": 100.0}]

    def test_search_empty_dict_attributes(self):
        """Test search with empty dict attributes returns default results."""
        with patch.object(self.engine, '_get_default_results') as mock_default:
            mock_default.return_value = [{"id": 1, "name": "Test Item", "price": 100.0}]

            result = self.engine.search("SELECT * FROM items", {})

            mock_default.assert_called_once_with("printers")
            assert result == [{"id": 1, "name": "Test Item", "price": 100.0}]

    def test_search_printers_category(self):
        """Test search with printers category."""
        with patch.object(self.engine, '_search_printers') as mock_search:
            mock_search.return_value = [{"id": 1, "name": "Test Printer", "price": 200.0}]

            result = self.engine.search("SELECT * FROM printers", {"budget": "200"}, "printers")

            mock_search.assert_called_once()
            assert result == [{"id": 1, "name": "Test Printer", "price": 200.0}]

    def test_search_laptops_category(self):
        """Test search with laptops category."""
        with patch.object(self.engine, '_search_laptops') as mock_search:
            mock_search.return_value = [{"id": 1, "name": "Test Laptop", "price": 800.0}]

            result = self.engine.search("SELECT * FROM laptops", {"budget": "800"}, "laptops")

            mock_search.assert_called_once()
            assert result == [{"id": 1, "name": "Test Laptop", "price": 800.0}]

    def test_search_computers_category(self):
        """Test search with computers category."""
        with patch.object(self.engine, '_search_computers') as mock_search:
            mock_search.return_value = [{"id": 1, "name": "Test Computer", "price": 1200.0}]

            result = self.engine.search("SELECT * FROM computers", {"budget": "1200"}, "computers")

            mock_search.assert_called_once()
            assert result == [{"id": 1, "name": "Test Computer", "price": 1200.0}]

    def test_search_smartphones_category(self):
        """Test search with smartphones category."""
        with patch.object(self.engine, '_search_smartphones') as mock_search:
            mock_search.return_value = [{"id": 1, "name": "Test Smartphone", "price": 500.0}]

            result = self.engine.search(
                "SELECT * FROM smartphones", {"budget": "500"}, "smartphones"
            )

            mock_search.assert_called_once()
            assert result == [{"id": 1, "name": "Test Smartphone", "price": 500.0}]

    def test_search_unknown_category(self):
        """Test search with unknown category returns empty list."""
        result = self.engine.search("SELECT * FROM unknown", {"budget": "100"}, "unknown")

        assert result == []

    def test_parse_budget_numeric(self):
        """Test budget parsing with numeric values."""
        assert self.engine._parse_budget(100) == 100.0
        assert self.engine._parse_budget(100.5) == 100.5

    def test_parse_budget_string_single_number(self):
        """Test budget parsing with single number string."""
        assert self.engine._parse_budget("100") == 100.0
        assert self.engine._parse_budget("200 euro") == 200.0

    def test_parse_budget_string_range(self):
        """Test budget parsing with range string."""
        assert self.engine._parse_budget("100-200") == 200.0
        assert self.engine._parse_budget("50-150 euro") == 150.0

    def test_parse_budget_vague_response(self):
        """Test budget parsing with vague responses."""
        assert self.engine._parse_budget("weet ik niet") is None
        assert self.engine._parse_budget("geen idee") is None

    def test_is_vague_response(self):
        """Test vague response detection."""
        assert self.engine._is_vague_response("weet ik niet") is True
        assert self.engine._is_vague_response("geen idee") is True
        assert self.engine._is_vague_response("maakt niet uit") is True
        assert self.engine._is_vague_response("specific value") is False

    def test_get_categories(self):
        """Test get_categories method."""
        categories = self.engine.get_categories()
        expected = ["printers", "laptops", "computers", "smartphones"]
        assert categories == expected

    def test_get_category_metadata(self):
        """Test get_category_metadata method."""
        # Currently returns None for compatibility
        assert self.engine.get_category_metadata("printers") is None
        assert self.engine.get_category_metadata("laptops") is None

    def test_map_printer(self):
        """Test printer mapping to dict format."""
        mock_printer = Mock()
        mock_printer.id = 1
        mock_printer.name = "Test Printer"
        mock_printer.price = 150.0

        result = self.engine._map_printer(mock_printer)

        expected = {
            "id": 1,
            "name": "Test Printer",
            "price": 150.0
        }
        assert result == expected

    def test_map_laptop(self):
        """Test laptop mapping to dict format."""
        mock_laptop = Mock()
        mock_laptop.id = 2
        mock_laptop.name = "Test Laptop"
        mock_laptop.price = 800.0

        result = self.engine._map_laptop(mock_laptop)

        expected = {
            "id": 2,
            "name": "Test Laptop",
            "price": 800.0
        }
        assert result == expected

    def test_map_computer(self):
        """Test computer mapping to dict format."""
        mock_computer = Mock()
        mock_computer.id = 3
        mock_computer.name = "Test Computer"
        mock_computer.price = 1200.0

        result = self.engine._map_computer(mock_computer)

        expected = {
            "id": 3,
            "name": "Test Computer",
            "price": 1200.0
        }
        assert result == expected

    def test_map_smartphone(self):
        """Test smartphone mapping to dict format."""
        mock_smartphone = Mock()
        mock_smartphone.id = 4
        mock_smartphone.name = "Test Smartphone"
        mock_smartphone.price = 600.0

        result = self.engine._map_smartphone(mock_smartphone)

        expected = {
            "id": 4,
            "name": "Test Smartphone",
            "price": 600.0
        }
        assert result == expected


def test_create_database_search_engine():
    """Test factory function."""
    from pixie.core.search.database_search_engine import create_database_search_engine

    engine = create_database_search_engine()
    assert isinstance(engine, DatabaseSearchEngine)
