"""Unit tests for FakeProductCatalog functionality."""

import pytest

from pixie.core.contracts import Product
from pixie.core.fake_catalog import FakeProductCatalog


class TestFakeProductCatalog:
    """Test FakeProductCatalog functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.catalog = FakeProductCatalog()

    def test_get_all_products(self):
        """Test getting all products."""
        products = self.catalog.get_all_products()
        assert len(products) >= 20
        assert all(isinstance(p, Product) for p in products)

    def test_product_schema_validation(self):
        """Test that all products have required fields."""
        products = self.catalog.get_all_products()

        for product in products:
            assert product.id
            assert product.name
            assert product.price > 0
            assert product.brand
            assert product.category
            assert product.description

    def test_budget_coverage(self):
        """Test that products cover all budget ranges."""
        products = self.catalog.get_all_products()

        under_150 = [p for p in products if p.price < 150]
        between_150_300 = [p for p in products if 150 <= p.price <= 300]
        over_300 = [p for p in products if p.price > 300]

        assert len(under_150) > 0
        assert len(between_150_300) > 0
        assert len(over_300) > 0

    def test_brand_coverage(self):
        """Test that multiple brands are represented."""
        products = self.catalog.get_all_products()
        brands = set(p.brand for p in products)

        expected_brands = {"Brother", "HP", "Kyocera", "Canon", "Epson"}
        assert expected_brands.issubset(brands)

    def test_technology_coverage(self):
        """Test that different technologies are represented."""
        products = self.catalog.get_all_products()
        technologies = set(p.technology for p in products if p.technology)

        expected_technologies = {"Laser", "Inkjet", "Thermal inkjet"}
        assert expected_technologies.issubset(technologies)

    def test_filter_by_budget(self):
        """Test budget filtering."""
        products = self.catalog.get_all_products()

        # Test under 150 filter
        filtered = self.catalog.filter_by_budget(products, 0, 150)
        assert all(p.price <= 150 for p in filtered)
        assert len(filtered) > 0

        # Test between 150-300 filter
        filtered = self.catalog.filter_by_budget(products, 150, 300)
        assert all(150 <= p.price <= 300 for p in filtered)
        assert len(filtered) > 0

    def test_filter_by_brand(self):
        """Test brand filtering."""
        products = self.catalog.get_all_products()

        # Test specific brand
        brother_products = self.catalog.filter_by_brand(products, "Brother")
        assert all(p.brand == "Brother" for p in brother_products)
        assert len(brother_products) > 0

        # Test case insensitive
        brother_products_lower = self.catalog.filter_by_brand(products, "brother")
        assert len(brother_products_lower) == len(brother_products)

        # Test "any" brand
        any_products = self.catalog.filter_by_brand(products, "any")
        assert len(any_products) == len(products)

    def test_filter_by_technology(self):
        """Test technology filtering."""
        products = self.catalog.get_all_products()

        # Test specific technology
        laser_products = self.catalog.filter_by_technology(products, "Laser")
        assert all(p.technology == "Laser" for p in laser_products)
        assert len(laser_products) > 0

        # Test "any" technology
        any_products = self.catalog.filter_by_technology(products, "any")
        assert len(any_products) == len(products)

    def test_filter_by_category(self):
        """Test category filtering."""
        products = self.catalog.get_all_products()

        # Test printer category
        printers = self.catalog.filter_by_category(products, "printer")
        assert all(p.category == "printer" for p in printers)
        assert len(printers) > 0

    def test_search_products_no_filters(self):
        """Test search without filters returns all products."""
        results = self.catalog.search_products()
        all_products = self.catalog.get_all_products()
        assert len(results) == len(all_products)

    def test_search_products_combined_filters(self):
        """Test search with multiple filters."""
        filters = {
            "category": "printer",
            "brand": "Brother",
            "budget": {"min": 0, "max": 200},
        }

        results = self.catalog.search_products(filters)

        assert all(p.category == "printer" for p in results)
        assert all(p.brand == "Brother" for p in results)
        assert all(p.price <= 200 for p in results)
        assert len(results) > 0

    def test_sort_products(self):
        """Test product sorting."""
        products = self.catalog.get_all_products()[:5]  # Take first 5

        # Test price sorting
        sorted_by_price = self.catalog.sort_products(products, "price")
        prices = [p.price for p in sorted_by_price]
        assert prices == sorted(prices)

        # Test price descending
        sorted_desc = self.catalog.sort_products(products, "price_desc")
        prices_desc = [p.price for p in sorted_desc]
        assert prices_desc == sorted(prices_desc, reverse=True)

        # Test name sorting
        sorted_by_name = self.catalog.sort_products(products, "name")
        names = [p.name.lower() for p in sorted_by_name]
        assert names == sorted(names)

    def test_sample_products(self):
        """Test product sampling."""
        products = self.catalog.get_all_products()

        # Test sampling less than total
        sample = self.catalog.sample_products(products, 5)
        assert len(sample) == 5
        assert all(p in products for p in sample)

        # Test sampling more than available
        large_sample = self.catalog.sample_products(products[:3], 10)
        assert len(large_sample) == 3

    def test_get_top_products(self):
        """Test getting top products."""
        products = self.catalog.get_all_products()

        # Test top 5 by price
        top_5 = self.catalog.get_top_products(products, 5, "price")
        assert len(top_5) == 5

        # Verify they're actually the cheapest
        all_sorted = self.catalog.sort_products(products, "price")
        expected_top_5 = all_sorted[:5]
        assert [p.id for p in top_5] == [p.id for p in expected_top_5]

    def test_result_threshold_configuration(self):
        """Test that result threshold is configurable."""
        assert self.catalog.result_threshold == 3

        # Test changing threshold
        self.catalog.result_threshold = 5
        assert self.catalog.result_threshold == 5
