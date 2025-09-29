# Flexible database repositories for dynamic product system

from .flexible_repositories import (
    DynamicRepository,
    TableDiscovery,
    discover_product_tables,
    get_dynamic_repository,
    get_table_discovery,
)

__all__ = [
    "DynamicRepository",
    "TableDiscovery",
    "discover_product_tables",
    "get_dynamic_repository",
    "get_table_discovery",
]
