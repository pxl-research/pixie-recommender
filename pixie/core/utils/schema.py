from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class SchemaManager:
    """Manages database schema information for SQL generation."""

    def __init__(self, schema_file: str = "pixie/core/data/schema.json"):
        self.schema_file = Path(schema_file)
        self._schema_cache: Optional[Dict[str, Any]] = None

    def _load_schema(self) -> Dict[str, Any]:
        """Load schema configuration from JSON file."""
        if self._schema_cache is None:
            try:
                with open(self.schema_file, "r", encoding="utf-8") as f:
                    self._schema_cache = json.load(f)
            except Exception:
                # Fallback to empty schema
                self._schema_cache = {}
        return self._schema_cache or {}

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a specific table."""
        schema = self._load_schema()

        # Navigate to the table definition in the JSON schema
        properties = schema.get("properties", {})
        table_def = properties.get(table_name, {})

        if "items" in table_def and "properties" in table_def["items"]:
            return table_def["items"]["properties"]

        return {}

    def generate_table_description(self, table_name: str) -> str:
        """Generate a human-readable table description for LLM prompts."""
        table_schema = self.get_table_schema(table_name)

        if not table_schema:
            return f"Table: {table_name} (schema not found)"

        description_lines = [f"Available table: {table_name}", "Columns:"]

        for column_name, column_def in table_schema.items():
            column_type = column_def.get("type", "unknown")
            column_desc = self._get_column_description(column_name, column_def)
            description_lines.append(f"- {column_name} ({column_type}): {column_desc}")

        return "\n".join(description_lines)

    def _get_column_description(
        self, column_name: str, column_def: Dict[str, Any]
    ) -> str:
        """Generate a description for a specific column."""
        # Use explicit description if available
        if "description" in column_def:
            return column_def["description"]

        # Generate description based on column name
        descriptions = {
            "id": "unique identifier",
            "name": "name or title",
            "brand": "manufacturer brand",
            "technology": "technology type",
            "price": "price in euros",
            "price_cents": "price in cents",
            "description": "product description",
            "has_color": "supports color printing",
            "is_multifunction": "has scan/copy functions",
            "has_wifi": "wireless connectivity",
            "has_duplex": "double-sided printing",
            "print_speed_ppm": "pages per minute",
            "resolution_dpi": "print resolution",
            "max_paper_size": "maximum paper size",
            "availability_status": "availability status",
            "stock_level": "items in stock",
            "created_at": "creation timestamp",
            "updated_at": "last update timestamp",
        }

        return descriptions.get(column_name, f"{column_name} field")

    def get_required_columns(self, table_name: str) -> List[str]:
        """Get list of required columns for a table."""
        schema = self._load_schema()
        properties = schema.get("properties", {})
        table_def = properties.get(table_name, {})

        if "items" in table_def:
            return table_def["items"].get("required", [])

        return []

    def get_column_info(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific column."""
        table_schema = self.get_table_schema(table_name)
        return table_schema.get(column_name, {})

    def get_searchable_columns(self, table_name: str) -> List[str]:
        """Get columns that are typically used for searching/filtering."""
        table_schema = self.get_table_schema(table_name)

        # Define searchable column patterns
        searchable_patterns = [
            "name",
            "brand",
            "technology",
            "price",
            "has_",
            "is_",
            "description",
            "category",
            "type",
        ]

        searchable_cols = []
        for col_name in table_schema.keys():
            if any(pattern in col_name.lower() for pattern in searchable_patterns):
                searchable_cols.append(col_name)

        return searchable_cols

    def generate_query_hints(self, table_name: str) -> str:
        """Generate helpful hints for SQL query generation."""
        searchable = self.get_searchable_columns(table_name)
        required = self.get_required_columns(table_name)

        # Format searchable columns with truncation
        searchable_str = ", ".join(searchable[:5])
        if len(searchable) > 5:
            searchable_str += "..."

        hints = [
            f"Primary table: {table_name}",
            f"Required columns: {', '.join(required)}",
            f"Searchable columns: {searchable_str}",
            "Common filters: price ranges, brand matching, boolean flags",
        ]

        return "\n".join(hints)


# Global instance
_schema_manager: Optional[SchemaManager] = None


def get_schema_manager() -> SchemaManager:
    """Get the global schema manager instance."""
    global _schema_manager
    if _schema_manager is None:
        _schema_manager = SchemaManager()
    return _schema_manager
