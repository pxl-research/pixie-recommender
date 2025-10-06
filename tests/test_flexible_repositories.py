import uuid

from pixie.core.database.connection import get_db_session
from pixie.core.database.repositories.flexible_repositories import (
    get_dynamic_repository,
)


def test_create_generates_uuid_for_string_primary_key(ensure_minimal_catalog):
    unique_name = "test_product_type_uuid_generation"

    with get_db_session() as session:
        repo = get_dynamic_repository(session, "product_types")

        created = repo.create(
            {
                "name": unique_name,
                "display_name": "UUID Gen",
                "description": "Ensures UUIDs are generated when missing.",
                "is_active": True,
            }
        )

        assert created["id"], "Repository should populate the primary key"

        generated_id = str(created["id"])
        # Validate the generated value parses as a UUID (hex form without hyphens is accepted)
        uuid.UUID(generated_id)

        fetched = repo.get_by_id(generated_id)
        assert fetched is not None
        assert str(fetched["id"]) == generated_id
