"""Database-driven search engine for Pixie Core (renamed from unified_search_engine).

This module exposes the `SearchEngine` class and `create_search_engine`
factory using a clearer module name.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy import text

from ..database.connection import get_db_session
from ..database.repositories.flexible_repositories import (
    get_dynamic_repository,
    get_table_discovery,
)

logger = logging.getLogger(__name__)


class SearchEngine:
    """Database-driven search engine for Pixie Core.

    This engine provides unified search functionality across product categories
    using a PostgreSQL database and dynamic repository helpers.
    """

    def __init__(self):
        self._default_page_size = 10
        logger.info("Initialized flexible database-driven search engine")

    def search(
        self,
        sql: str,
        attributes: Optional[Dict[str, Any]],
        category: Optional[str] = None,
    ) -> list:
        """Search products using either an SQL string or attribute-based filters."""
        logger.info(
            f"Search called with sql='{sql}', attributes={attributes}, category='{category}'"
        )

        # If a meaningful SQL query is provided, try executing it.
        if sql and sql.strip() and sql.strip().lower() != "select":
            try:
                return self._execute_sql_query(sql)
            except Exception as e:
                logger.warning(f"Failed to execute SQL query: {e}")

        # If there are no attributes, return default products
        if attributes is None or (
            isinstance(attributes, dict) and len(attributes) == 0
        ):
            return self._get_default_results(category)

        # Otherwise, filter by attributes
        return self._filter_results_by_attributes(attributes, category)

    def _execute_sql_query(self, sql: str) -> list:
        """Execute a SQL query and return mapped results."""
        logger.info(f"Executing SQL query: {sql}")

        with get_db_session() as session:
            try:
                # Attempt to rewrite naive queries that reference product types as tables
                rewritten_sql = self._rewrite_product_type_queries(session, sql)

                # Execute the (possibly rewritten) SQL query
                return self._execute_and_map_sql(session, rewritten_sql)

            except Exception as e:
                logger.error(f"Error executing SQL query: {e}")
                raise

    def _rewrite_product_type_queries(self, session, sql: str) -> str:
        """Rewrite queries that reference product types as table names."""
        import re

        # Check if query references a table name that might be a product type
        table_match = re.search(r"from\s+([a-zA-Z_][\w]*)", sql, re.IGNORECASE)
        if not table_match:
            return sql

        referenced_table = table_match.group(1).lower()

        # Check if this table actually exists in the database
        if self._table_exists(session, referenced_table):
            return sql

        # Check if it's a product type instead
        if self._is_product_type(session, referenced_table):
            return self._rewrite_as_product_type_query(sql, referenced_table)

        return sql

    def _table_exists(self, session, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            discovery = get_table_discovery(session)
            if hasattr(discovery, "get_all_tables"):
                discovered_iter = discovery.get_all_tables()
            elif hasattr(discovery, "get_product_tables"):
                discovered_iter = discovery.get_product_tables()
            elif isinstance(discovery, (list, tuple, set)):
                discovered_iter = discovery
            else:
                return False

            discovered_names = {str(t).lower() for t in discovered_iter}
            return table_name in discovered_names

        except Exception:
            return False

    def _is_product_type(self, session, type_name: str) -> bool:
        """Check if a name corresponds to a product type."""
        try:
            type_repo = get_dynamic_repository(session, "product_types")
            product_types = type_repo.filter_by_attributes({"name": type_name})
            return len(product_types) > 0
        except Exception:
            return False

    def _rewrite_as_product_type_query(self, sql: str, product_type: str) -> str:
        """Rewrite SQL to use products table with product type join."""
        import re

        logger.info(
            f"Rewriting SQL: referenced table '{product_type}' is a "
            "product_type; using products join instead"
        )

        # Extract WHERE clause if present
        where_match = re.search(r"where\s+(.*)$", sql, re.IGNORECASE | re.DOTALL)
        original_where = None
        if where_match:
            original_where = where_match.group(1).strip()
            if original_where.endswith(";"):
                original_where = original_where[:-1].strip()

        # Build new query with product type join
        base_sql = (
            "SELECT p.* FROM products p "
            "JOIN product_types pt ON p.product_type_id = pt.id "
            f"WHERE pt.name = '{product_type}'"
        )

        if original_where:
            return f"{base_sql} AND ({original_where})"
        else:
            return base_sql

    def _execute_and_map_sql(self, session, sql: str) -> list:
        """Execute SQL and map results to product format."""
        result = session.execute(text(sql))
        rows = result.fetchall()

        if not rows:
            logger.info("SQL query returned no results")
            return []

        # Map rows to product dictionaries
        columns = result.keys()
        results = []
        for row in rows:
            row_dict = {col_name: row[i] for i, col_name in enumerate(columns)}
            results.append(self._map_product(row_dict))

        logger.info(f"SQL query returned {len(results)} results")
        return results

    def _get_default_results(self, category: Optional[str]) -> list:
        """Get default results when no attributes are provided."""
        logger.info(f"Getting default results for category: {category}")

        with get_db_session() as session:
            try:
                product_repo = get_dynamic_repository(session, "products")

                if category:
                    type_repo = get_dynamic_repository(session, "product_types")
                    product_types = type_repo.filter_by_attributes({"name": category})

                    if product_types:
                        type_id = product_types[0]["id"]
                        products = product_repo.filter_by_attributes(
                            {"product_type_id": type_id}
                        )
                    else:
                        logger.warning(f"Product type '{category}' not found")
                        products = []
                else:
                    products = product_repo.get_all()

                results = [self._map_product(p) for p in products]
                logger.info(f"Found {len(results)} products")
                return results

            except Exception as e:
                logger.error(f"Error getting default results: {e}")
                return []

    def _filter_results_by_attributes(
        self, attributes: Dict[str, Any], category: Optional[str]
    ) -> list:
        """Filter products based on collected attributes."""
        logger.info(
            f"Filtering results by attributes: {attributes}, category: {category}"
        )

        with get_db_session() as session:
            try:
                product_repo = get_dynamic_repository(session, "products")

                filter_attributes = self._extract_filter_attributes(session, attributes)

                if category:
                    type_repo = get_dynamic_repository(session, "product_types")
                    product_types = type_repo.filter_by_attributes({"name": category})

                    if product_types:
                        type_id = product_types[0]["id"]
                        base_products = product_repo.filter_by_attributes(
                            {"product_type_id": type_id}
                        )
                    else:
                        logger.warning(f"Product type '{category}' not found")
                        return []
                else:
                    base_products = product_repo.get_all()

                filtered_products = self._apply_attribute_filters(
                    session, base_products, filter_attributes
                )

                results = [self._map_product(p) for p in filtered_products]
                logger.info(f"Filtered to {len(results)} products")

                return results

            except Exception as e:
                logger.error(f"Error filtering results by attributes: {e}")
                return []

    def _extract_filter_attributes(
        self, session, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine which keys from context are usable filters."""
        product_columns = set()
        try:
            from sqlalchemy import inspect

            inspector = inspect(session.bind)
            cols = inspector.get_columns("products")
            product_columns = {c["name"] for c in cols}
        except Exception:
            product_columns = set()

        attr_names = set()
        try:
            attr_def_repo = get_dynamic_repository(session, "attribute_definitions")
            defs = attr_def_repo.get_all()
            for d in defs:
                name = d.get("name")
                if name:
                    attr_names.add(name)
        except Exception:
            attr_names = set()

        filter_attributes = {}
        for key, value in context.items():
            if value is None:
                continue
            if key == "budget" or key in product_columns or key in attr_names:
                filter_attributes[key] = value

        logger.info(f"Dynamically extracted filter attributes: {filter_attributes}")
        return filter_attributes

    def _apply_attribute_filters(
        self, session, base_products: list, filter_attributes: Dict[str, Any]
    ) -> list:
        """Apply attribute filters using the normalized database structure."""
        if not filter_attributes:
            return base_products

        logger.info(f"Applying attribute filters: {filter_attributes}")

        try:
            base_product_ids = [p["id"] for p in base_products]
            if not base_product_ids:
                return []

            filtered_product_ids = set(base_product_ids)

            # Apply each filter sequentially
            for attr_name, attr_value in filter_attributes.items():
                if attr_value is None:
                    continue

                filtered_product_ids = self._apply_single_attribute_filter(
                    session, filtered_product_ids, attr_name, attr_value
                )

                if not filtered_product_ids:
                    return []

            # Return filtered products
            filtered_products = [
                p for p in base_products if p["id"] in filtered_product_ids
            ]

            logger.info(
                "Attribute filtering reduced results from "
                f"{len(base_products)} to {len(filtered_products)}"
            )
            return filtered_products

        except Exception as e:
            logger.error(f"Error applying attribute filters: {e}")
            return base_products

    def _apply_single_attribute_filter(
        self, session, current_product_ids: set, attr_name: str, attr_value: Any
    ) -> set:
        """Apply a single attribute filter and return matching product IDs."""
        # Special handling for budget
        if attr_name == "budget":
            return self._apply_budget_filter(session, current_product_ids, attr_value)

        # Check if it's a product column filter
        if self._is_product_column(session, attr_name):
            return self._apply_product_column_filter(
                session, current_product_ids, attr_name, attr_value
            )

        # Otherwise, it's a custom attribute filter
        return self._apply_custom_attribute_filter(
            session, current_product_ids, attr_name, attr_value
        )

    def _is_product_column(self, session, attr_name: str) -> bool:
        """Check if an attribute name corresponds to a product table column."""
        try:
            from sqlalchemy import inspect

            inspector = inspect(session.bind)
            prod_cols = {c["name"] for c in inspector.get_columns("products")}
            return attr_name in prod_cols
        except Exception:
            return False

    def _apply_product_column_filter(
        self, session, current_product_ids: set, attr_name: str, attr_value: Any
    ) -> set:
        """Apply filter for product table column."""
        try:
            if isinstance(attr_value, str):
                query = f"SELECT id FROM products WHERE LOWER({attr_name}) = :val"
                params = {"val": attr_value.lower()}
            else:
                query = f"SELECT id FROM products WHERE {attr_name} = :val"
                params = {"val": attr_value}

            # Add current product ID constraints
            if current_product_ids:
                ids_list = list(current_product_ids)
                placeholders = ", ".join([f":id_{i}" for i in range(len(ids_list))])
                query += f" AND id IN ({placeholders})"
                for i, pid in enumerate(ids_list):
                    params[f"id_{i}"] = pid

            result = session.execute(text(query), params)
            matching_ids = {row[0] for row in result.fetchall()}
            return current_product_ids.intersection(matching_ids)

        except Exception:
            logger.warning(f"Failed to apply product-column filter for {attr_name}")
            return current_product_ids

    def _apply_custom_attribute_filter(
        self, session, current_product_ids: set, attr_name: str, attr_value: Any
    ) -> set:
        """Apply filter for custom product attributes."""
        try:
            attr_def_repo = get_dynamic_repository(session, "attribute_definitions")
            attr_val_repo = get_dynamic_repository(session, "product_attribute_values")

            # Find attribute definition
            attr_defs = attr_def_repo.filter_by_attributes({"name": attr_name})
            if not attr_defs:
                logger.warning(f"Attribute definition not found for: {attr_name}")
                return current_product_ids

            attr_def = attr_defs[0]
            attr_def_id = attr_def["id"]

            # Find matching attribute values
            matching_attr_vals = attr_val_repo.filter_by_attributes(
                {"attribute_definition_id": attr_def_id, "value": str(attr_value)}
            )

            matching_product_ids = {val["product_id"] for val in matching_attr_vals}
            return current_product_ids.intersection(matching_product_ids)

        except Exception as e:
            logger.error(f"Error applying custom attribute filter for {attr_name}: {e}")
            return current_product_ids

    def _apply_budget_filter(
        self, session, current_product_ids: set, budget_value: str
    ) -> set:
        """Apply budget filtering directly on products table."""
        try:
            logger.info(f"Parsing budget value: {budget_value}")

            budget_lower = budget_value.lower().strip()
            max_price_euros = None

            if "minder dan" in budget_lower:
                parts = budget_lower.split("minder dan")
                if len(parts) > 1:
                    amount_str = parts[1].strip().replace("€", "").replace(" ", "")
                    try:
                        max_price_euros = float(amount_str)
                    except ValueError:
                        pass

            elif any(currency in budget_lower for currency in ["euro", "€"]):
                import re

                numbers = re.findall(r"\d+(?:\.\d+)?", budget_lower)
                if numbers:
                    try:
                        max_price_euros = float(numbers[0])
                    except ValueError:
                        pass

            else:
                try:
                    max_price_euros = float(budget_lower)
                except ValueError:
                    pass

            if max_price_euros is not None:
                logger.info(f"Parsed budget as: €{max_price_euros}")

                query = "SELECT id FROM products WHERE price_cents <= :max_price_cents"
                if current_product_ids:
                    ids_list = list(current_product_ids)
                    placeholders = ", ".join([f":id_{i}" for i in range(len(ids_list))])
                    query += f" AND id IN ({placeholders})"

                    params = {"max_price_cents": int(max_price_euros * 100)}
                    for i, product_id in enumerate(ids_list):
                        params[f"id_{i}"] = product_id
                else:
                    params = {"max_price_cents": int(max_price_euros * 100)}

                result = session.execute(text(query), params)
                price_matching_ids = {row[0] for row in result.fetchall()}

                logger.info(f"Budget filter matched {len(price_matching_ids)} products")
                return price_matching_ids
            else:
                logger.warning(f"Could not parse budget amount from: {budget_value}")
                return current_product_ids

        except Exception as e:
            logger.error(f"Error applying budget filter: {e}")
            return current_product_ids

    def _map_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Map a product dictionary to the expected format."""
        return {
            "id": str(product.get("id", "")),
            "external_id": product.get("external_id"),
            "name": product.get("name"),
            "description": product.get("description"),
            "brand": product.get("brand"),
            "model": product.get("model"),
            "price": product.get("price_cents", 0) / 100.0,
            "product_type": product.get("category"),
            "created_at": product.get("created_at"),
        }


def create_search_engine():
    """Create and return a SearchEngine instance."""
    return SearchEngine()


__all__ = ["SearchEngine", "create_search_engine"]
