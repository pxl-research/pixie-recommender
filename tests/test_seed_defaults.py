"""Unit tests for seeding helpers."""

from pixie.core.database.seed import _apply_product_defaults


def test_apply_product_defaults_adds_missing_values():
    base_attrs = {
        "name": "Sample Product",
        "currency": "USD",
    }
    available_columns = {"currency", "availability_status", "stock_level", "is_active"}

    result = _apply_product_defaults(base_attrs, available_columns)

    assert result["currency"] == "USD"
    assert result["availability_status"] == "in_stock"
    assert result["stock_level"] == 0
    assert result["is_active"] is True


def test_apply_product_defaults_retains_explicit_values():
    base_attrs = {
        "availability_status": "preorder",
        "stock_level": 42,
        "is_active": False,
    }
    available_columns = {"currency", "availability_status", "stock_level", "is_active"}

    result = _apply_product_defaults(base_attrs, available_columns)

    assert result["availability_status"] == "preorder"
    assert result["stock_level"] == 42
    assert result["is_active"] is False
    assert result["currency"] == "EUR"


def test_apply_product_defaults_skips_unavailable_columns():
    base_attrs = {}
    available_columns = {"currency"}

    result = _apply_product_defaults(base_attrs, available_columns)

    assert result["currency"] == "EUR"
    assert "availability_status" not in result
