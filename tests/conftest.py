import os
from typing import Any, Dict, List, Tuple

import pytest

from pixie.core.database.connection import reset_engine
from pixie.core.llms import azure_llm_set
from pixie.core.utils.config import reset_config

DEFAULT_TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")


def _configure_test_database() -> None:
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = DEFAULT_TEST_DB_URL

    reset_engine()
    reset_config()


_configure_test_database()


def _ensure_product_type_data(session) -> None:
    """Insert minimal product types and attribute definitions for tests."""

    from pixie.core.database.init import create_tables
    from pixie.core.database.repositories.flexible_repositories import (
        get_dynamic_repository,
    )

    create_tables()

    product_types_repo = get_dynamic_repository(session, "product_types")
    attribute_repo = get_dynamic_repository(session, "attribute_definitions")

    product_types: List[Dict[str, Any]] = [
        {
            "name": "printers",
            "display_name": "Printers",
            "description": "Printers including inkjet and laser",
            "is_active": True,
        },
        {
            "name": "laptop",
            "display_name": "Laptops",
            "description": "Portable computers",
            "is_active": True,
        },
        {
            "name": "smartphone",
            "display_name": "Smartphones",
            "description": "Mobile phones",
            "is_active": True,
        },
    ]

    attribute_definitions: Dict[str, List[Dict[str, Any]]] = {
        "printers": [
            {
                "name": "budget",
                "display_name": "Budget",
                "data_type": "number",
                "is_required": True,
                "display_order": 1,
                "canonical_name": "budget",
                "is_searchable": True,
                "is_filterable": True,
            },
            {
                "name": "brand",
                "display_name": "Brand",
                "data_type": "choice",
                "is_required": False,
                "display_order": 2,
                "options": ["HP", "Canon", "Brother"],
                "canonical_name": "brand",
                "is_searchable": True,
                "is_filterable": True,
            },
            {
                "name": "technology",
                "display_name": "Technology",
                "data_type": "choice",
                "is_required": False,
                "display_order": 3,
                "options": ["inkjet", "laser"],
                "canonical_name": "technology",
                "is_searchable": True,
                "is_filterable": True,
            },
        ],
        "laptop": [
            {
                "name": "budget",
                "display_name": "Budget",
                "data_type": "number",
                "is_required": True,
                "display_order": 1,
                "canonical_name": "budget",
                "is_searchable": True,
                "is_filterable": True,
            },
            {
                "name": "screen_size",
                "display_name": "Schermgrootte",
                "data_type": "number",
                "is_required": False,
                "display_order": 2,
                "canonical_name": "screen_size",
                "is_searchable": True,
                "is_filterable": True,
            },
        ],
        "smartphone": [
            {
                "name": "budget",
                "display_name": "Budget",
                "data_type": "number",
                "is_required": True,
                "display_order": 1,
                "canonical_name": "budget",
                "is_searchable": True,
                "is_filterable": True,
            },
            {
                "name": "storage",
                "display_name": "Opslag",
                "data_type": "choice",
                "is_required": False,
                "display_order": 2,
                "options": ["128GB", "256GB", "512GB"],
                "canonical_name": "storage",
                "is_searchable": True,
                "is_filterable": True,
            },
        ],
    }

    for pt in product_types:
        existing = product_types_repo.find_by_column("name", pt["name"])
        if existing:
            product_type = existing[0]
        else:
            product_type = product_types_repo.create(pt)

        product_type_id = product_type["id"]

        for attr in attribute_definitions[pt["name"]]:
            filters = {
                "name": attr["name"],
                "product_type_id": product_type_id,
            }
            existing_attr = attribute_repo.filter_by_attributes(filters)
            if existing_attr:
                continue

            payload = attr.copy()
            payload["product_type_id"] = product_type_id
            attribute_repo.create(payload)


@pytest.fixture(scope="session", autouse=True)
def ensure_minimal_catalog():
    """Ensure the flexible schema contains minimal attribute metadata for tests."""

    from pixie.core.database.connection import get_db_session

    with get_db_session() as session:
        _ensure_product_type_data(session)


@pytest.fixture(scope="session")
def azure_llm_set_fixture() -> Tuple[Any, Any, Any]:
    """
    Fixture that provides Azure LLM instances for testing.

    Requires proper Azure OpenAI configuration to run tests.
    """
    # Check if Azure is properly configured
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_key = os.getenv("AZURE_OPENAI_KEY", "")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "")
    azure_model = os.getenv("AZURE_OPENAI_MODEL", "")

    azure_configured = (
        azure_endpoint
        and azure_endpoint
        not in [
            "https://example.openai.azure.com/",
            "https://your-resource.openai.azure.com/",
        ]
        and azure_key
        and azure_key not in ["dummy-key-for-development", "your-api-key-here"]
        and azure_api_version
        and azure_model
    )

    if not azure_configured:
        pytest.skip(
            "Azure OpenAI configuration is required for tests. "
            "Please set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, "
            "AZURE_OPENAI_API_VERSION, and AZURE_OPENAI_MODEL environment variables."
        )

    try:
        # Create real Azure LLMs
        real_llms = azure_llm_set.create_azure_llm_set()
        print(f"✅ Using Azure LLMs for testing (endpoint: {azure_endpoint})")
        return real_llms
    except Exception as e:
        pytest.skip(f"Failed to create Azure LLMs: {e}")


# Legacy compatibility - can be removed once all tests are updated
@pytest.fixture(scope="session")
def llm_set(azure_llm_set_fixture):
    """Legacy fixture name for backward compatibility."""
    return azure_llm_set_fixture
