"""Database-driven search engine for Pixie Core."""

import logging
from typing import Any, Dict, Optional

from ..database.connection import get_db_session
from ..database.repositories.flexible_repositories import (
    get_dynamic_repository,
    get_table_discovery,
)

logger = logging.getLogger(__name__)


class SearchEngine:
    """Database-driven search engine for Pixie Core.

    This engine provides unified search functionality across all product categories
    using PostgreSQL database with optimized queries and indexing.

    Methods:
      search(sql: str, attributes: Optional[Dict[str, Any]],
             category: Optional[str] = None) -> Dict[str, Any]
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
        """Search products using database queries."""
        logger.info(
            f"Search called with sql='{sql}', "
            f"attributes={attributes}, category='{category}'"
        )

        # If we have a meaningful SQL query, execute it
        if sql and sql.strip() and sql.strip().lower() != "select":
            try:
                return self._execute_sql_query(sql)
            except Exception as e:
                logger.warning(f"Failed to execute SQL query: {e}")
                # Fall back to attribute-based search

        # If attributes is None or empty, return default results
        if attributes is None or (
            isinstance(attributes, dict) and len(attributes) == 0
        ):
            return self._get_default_results(category)

        # Use attributes to filter results
        return self._filter_results_by_attributes(attributes, category)

    def _execute_sql_query(self, sql: str) -> list:
        """Execute a SQL query and return results."""
        logger.info(f"Executing SQL query: {sql}")

        with get_db_session() as session:
            try:
                # Attempt to detect naive queries like "SELECT * FROM mixer;"
                # and rewrite them into a dynamic, safe query against the
                # normalized `products` table if the referenced name is a
                # product type in the database. This avoids errors when
                # the LLM generates SQL that references category-named tables.
                import re

                # find first FROM <identifier>
                m = re.search(r"from\s+([a-zA-Z_][\w]*)", sql, re.IGNORECASE)
                if m:
                    referenced = m.group(1).lower()

                    try:
                        # get discovered tables via TableDiscovery API
                        discovery = get_table_discovery(session)
                        if hasattr(discovery, "get_all_tables"):
                            discovered_iter = discovery.get_all_tables()
                        elif hasattr(discovery, "get_product_tables"):
                            discovered_iter = discovery.get_product_tables()
                        elif isinstance(discovery, (list, tuple, set)):
                            discovered_iter = discovery
                        else:
                            discovered_iter = []

                        discovered_names = set(str(t).lower() for t in discovered_iter)
                    except Exception:
                        discovered_names = set()

                    # if the referenced name is not a real table but is a
                    # product_type name, rewrite the query to select from
                    # products joined with product_types
                    if referenced not in discovered_names:
                        try:
                            type_repo = get_dynamic_repository(session, "product_types")
                            product_types = type_repo.filter_by_attributes(
                                {"name": referenced}
                            )
                            if product_types:
                                logger.info(
                                    "Rewriting SQL: referenced table '%s' is a product_type; "
                                    "using products join instead",
                                    referenced,
                                )
                                # safe rewrite
                                sql = (
                                    "SELECT p.* FROM products p "
                                    "JOIN product_types pt ON p.product_type_id = pt.id "
                                    f"WHERE pt.name = '{referenced}'"
                                )
                        except Exception:
                            # ignore and fall back to executing original SQL
                            pass
                from sqlalchemy import text

                result = session.execute(text(sql))
                rows = result.fetchall()

                # Convert rows to dictionaries
                if rows:
                    # Get column names from the result
                    columns = result.keys()
                    results = []
                    for row in rows:
                        row_dict = {}
                        for i, col_name in enumerate(columns):
                            row_dict[col_name] = row[i]
                        results.append(self._map_product(row_dict))

                    logger.info(f"SQL query returned {len(results)} results")
                    return results
                else:
                    logger.info("SQL query returned no results")
                    return []

            except Exception as e:
                logger.error(f"Error executing SQL query: {e}")
                raise

    def _get_default_results(self, category: Optional[str]) -> list:
        """Get default results when no attributes are provided."""
        logger.info(f"Getting default results for category: {category}")

        with get_db_session() as session:
            try:
                # Use dynamic repository for products table
                product_repo = get_dynamic_repository(session, "products")

                if category:
                    # Find product_type by name first
                    type_repo = get_dynamic_repository(session, "product_types")
                    product_types = type_repo.filter_by_attributes({"name": category})

                    if product_types:
                        type_id = product_types[0]["id"]
                        # Filter products by product_type_id
                        products = product_repo.filter_by_attributes(
                            {"product_type_id": type_id}
                        )
                    else:
                        logger.warning(f"Product type '{category}' not found")
                        products = []
                else:
                    # Get all products if no category specified
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

        # Extract only the relevant attributes for filtering
        filter_attributes = self._extract_filter_attributes(attributes)

        with get_db_session() as session:
            try:
                product_repo = get_dynamic_repository(session, "products")

                # Start with all products in the category
                if category:
                    # Find product_type by name first
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

                # Apply attribute filters using product_attribute_values
                filtered_products = self._apply_attribute_filters(
                    session, base_products, filter_attributes
                )

                # Convert to dictionary format
                results = [self._map_product(p) for p in filtered_products]
                logger.info(f"Filtered to {len(results)} products")

                return results

            except Exception as e:
                logger.error(f"Error filtering results by attributes: {e}")
                return []

    def _extract_filter_attributes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only the relevant attributes for filtering from context."""
        # Define which context keys are actual product attributes
        attribute_keys = {
            "budget",
            "brand",
            "screen_size",
            "processor",
            "ram",
            "storage",
            "camera",
            "wireless",
            "noise_cancelling",
            "resolution",
            "refresh_rate",
            "cellular",
            "price",
            "merk",
            "schermgrootte",
            "processor_type",
            "geheugen",
        }

        filter_attributes = {}
        for key, value in context.items():
            if key in attribute_keys and value is not None:
                filter_attributes[key] = value

        logger.info(f"Extracted filter attributes: {filter_attributes}")
        return filter_attributes

    def _apply_attribute_filters(
        self, session, base_products: list, filter_attributes: Dict[str, Any]
    ) -> list:
        """Apply attribute filters using the normalized database structure."""
        if not filter_attributes:
            return base_products

        logger.info(f"Applying attribute filters: {filter_attributes}")

        try:
            # Get repositories for attribute tables
            attr_def_repo = get_dynamic_repository(session, "attribute_definitions")
            attr_val_repo = get_dynamic_repository(session, "product_attribute_values")

            # Get product IDs from base products
            base_product_ids = [p["id"] for p in base_products]
            if not base_product_ids:
                return []

            # Start with all base product IDs
            filtered_product_ids = set(base_product_ids)

            # Apply each filter
            for attr_name, attr_value in filter_attributes.items():
                if attr_value is None:
                    continue

                # Handle special cases like budget filtering
                if attr_name == "budget":
                    filtered_product_ids = self._apply_budget_filter(
                        session, filtered_product_ids, attr_value
                    )
                    if not filtered_product_ids:
                        return []
                    continue

                # Find attribute definition
                attr_defs = attr_def_repo.filter_by_attributes({"name": attr_name})
                if not attr_defs:
                    logger.warning(f"Attribute definition not found for: {attr_name}")
                    continue

                attr_def = attr_defs[0]
                attr_def_id = attr_def["id"]

                # Find products that match this attribute value
                matching_attr_vals = attr_val_repo.filter_by_attributes(
                    {"attribute_definition_id": attr_def_id, "value": str(attr_value)}
                )

                # Get product IDs that have this attribute value
                matching_product_ids = {val["product_id"] for val in matching_attr_vals}

                # Intersect with current filtered set
                filtered_product_ids = filtered_product_ids.intersection(
                    matching_product_ids
                )

                if not filtered_product_ids:
                    # No products match all filters, return empty
                    return []

            # Filter base products to only include those that match all criteria
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
            # Return base products if filtering fails
            return base_products

    def _apply_budget_filter(
        self, session, current_product_ids: set, budget_value: str
    ) -> set:
        """Apply budget filtering directly on products table."""
        try:
            logger.info(f"Parsing budget value: {budget_value}")

            # Parse budget value - handle multiple formats
            budget_lower = budget_value.lower().strip()
            max_price_euros = None

            # Format: "minder dan 50€"
            if "minder dan" in budget_lower:
                parts = budget_lower.split("minder dan")
                if len(parts) > 1:
                    amount_str = parts[1].strip().replace("€", "").replace(" ", "")
                    try:
                        max_price_euros = float(amount_str)
                    except ValueError:
                        pass

            # Format: "500 euro", "€500", "500€"
            elif any(currency in budget_lower for currency in ["euro", "€"]):
                import re

                # Extract numbers from the string
                numbers = re.findall(r"\d+(?:\.\d+)?", budget_lower)
                if numbers:
                    try:
                        max_price_euros = float(numbers[0])
                    except ValueError:
                        pass

            # Format: just a number "500"
            else:
                try:
                    max_price_euros = float(budget_lower)
                except ValueError:
                    pass

            if max_price_euros is not None:
                logger.info(f"Parsed budget as: €{max_price_euros}")

                # Use raw SQL to filter by price with less than operator
                from sqlalchemy import text

                # Build query to get products with price <= max_price_cents
                query = """
                    SELECT id FROM products
                    WHERE price_cents <= :max_price_cents
                """
                if current_product_ids:
                    # Only include products that are already in our filtered set
                    ids_list = list(current_product_ids)
                    placeholders = ", ".join([f":id_{i}" for i in range(len(ids_list))])
                    query += f" AND id IN ({placeholders})"

                    # Add ID parameters
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

            logger.warning(f"Unsupported budget format: {budget_value}")
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
            "price": product.get("price_cents", 0) / 100.0,  # Convert cents to euros
            "product_type": product.get("category"),
            "created_at": product.get("created_at"),
        }


def create_search_engine():
    """Create and return a SearchEngine instance."""
    return SearchEngine()


__all__ = ["SearchEngine", "create_search_engine"]
