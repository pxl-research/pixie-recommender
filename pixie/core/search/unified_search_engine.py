"""Database-driven search engine for Pixie Core."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from ..database.connection import get_db_session
from ..database.repositories.flexible_repositories import (
    get_product_repository,
    get_product_type_repository,
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
    ) -> Dict[str, Any]:
        """Search products using database queries."""
        logger.info(
            f"Search called with sql='{sql}', "
            f"attributes={attributes}, category='{category}'"
        )

        # If attributes is None or empty, return default results
        if attributes is None or (
            isinstance(attributes, dict) and len(attributes) == 0
        ):
            return self._get_default_results(category)

        # Use attributes to filter results
        return self._filter_results_by_attributes(attributes, category)

    def _get_default_results(self, category: Optional[str]) -> Dict[str, Any]:
        """Get default results when no attributes are provided."""
        logger.info(f"Getting default results for category: {category}")

        with get_db_session() as session:
            try:
                product_repo = get_product_repository(session)
                type_repo = get_product_type_repository(session)

                # Find product type by name
                if category:
                    product_type = type_repo.get_by_name(category)
                    if product_type:
                        # Convert to UUID if needed
                        type_id = UUID(str(product_type.id))
                        products = product_repo.get_by_product_type(type_id)
                        results = [self._map_product(p) for p in products]
                        logger.info(
                            f"Found {len(results)} products for category '{category}'"
                        )
                        return {"results": results, "total": len(results)}
                    else:
                        logger.warning(f"Product type '{category}' not found")
                else:
                    # Get all products if no category specified
                    products = product_repo.get_all()
                    results = [self._map_product(p) for p in products]
                    logger.info(f"Found {len(results)} products total")
                    return {"results": results, "total": len(results)}

                return {"results": [], "total": 0}

            except Exception as e:
                logger.error(f"Error getting default results: {e}")
                return {"results": [], "total": 0}

    def _filter_results_by_attributes(
        self, attributes: Dict[str, Any], category: Optional[str]
    ) -> Dict[str, Any]:
        """Filter products based on collected attributes."""
        logger.info(
            f"Filtering results by attributes: {attributes}, category: {category}"
        )

        # Extract only the relevant attributes for filtering
        filter_attributes = self._extract_filter_attributes(attributes)

        with get_db_session() as session:
            try:
                product_repo = get_product_repository(session)
                type_repo = get_product_type_repository(session)

                # Start with all products in the category
                if category:
                    product_type = type_repo.get_by_name(category)
                    if product_type:
                        type_id = UUID(str(product_type.id))
                        products = product_repo.get_by_product_type(type_id)
                    else:
                        logger.warning(f"Product type '{category}' not found")
                        return {"results": [], "total": 0}
                else:
                    products = product_repo.get_all()

                # Apply attribute filters
                filtered_products = self._apply_attribute_filters(
                    products, filter_attributes
                )

                # Convert to dictionary format
                results = [self._map_product(p) for p in filtered_products]
                logger.info(
                    f"Filtered to {len(results)} products from {len(products)} total"
                )

                return {"results": results, "total": len(results)}

            except Exception as e:
                logger.error(f"Error filtering results by attributes: {e}")
                return {"results": [], "total": 0}

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

    def _apply_attribute_filters(self, products, attributes: Dict[str, Any]):
        """Apply attribute-based filtering to products."""
        filtered_products = []

        for product in products:
            if self._matches_attributes(product, attributes):
                filtered_products.append(product)

        return filtered_products

    def _matches_attributes(self, product, attributes: Dict[str, Any]) -> bool:
        """Check if a product matches the given attributes."""
        # For now, implement basic filtering based on product fields
        # TODO: Implement more sophisticated filtering using product_attribute_values

        for attr_name, attr_value in attributes.items():
            if attr_name == "budget":
                # Parse budget value (remove euro signs, etc.)
                budget_str = (
                    str(attr_value).lower().replace("euro", "").replace("€", "").strip()
                )
                try:
                    budget_cents = int(float(budget_str) * 100)
                    if product.price_cents > budget_cents:
                        return False
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse budget value: {attr_value}")

            elif attr_name == "brand":
                brand_value = str(attr_value).lower().strip()
                product_brand = str(product.brand or "").lower().strip()
                if brand_value and product_brand and brand_value not in product_brand:
                    return False

            elif attr_name == "screen_size":
                # Basic screen size matching
                size_value = str(attr_value).lower().strip()
                product_name = str(product.name or "").lower()
                product_desc = str(product.description or "").lower()
                if (
                    size_value
                    and size_value not in product_name
                    and size_value not in product_desc
                ):
                    # Try to extract screen size from product name/description
                    pass  # For now, skip strict filtering

            # Add more attribute filters as needed

        return True

    def _map_product(self, product) -> Dict[str, Any]:
        """Map a Product object to dictionary format."""
        return {
            "id": str(product.id),
            "external_id": product.external_id,
            "name": product.name,
            "description": product.description,
            "brand": product.brand,
            "model": product.model,
            "price_cents": product.price_cents,
            "product_type": product.product_type.name if product.product_type else None,
            "created_at": (
                product.created_at.isoformat() if product.created_at else None
            ),
        }


def create_search_engine():
    """Create and return a SearchEngine instance."""
    return SearchEngine()
