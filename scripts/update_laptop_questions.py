#!/usr/bin/env python3
"""
Script to update laptop questions using the corrected LLM approach.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def update_laptop_questions():
    """Update laptop attributes with corrected LLM-generated questions."""
    print("🤖 Generating questions for laptop attributes using corrected LLM...")

    try:
        from pixie.core.database.connection import get_db_session
        from pixie.core.database.repositories.flexible_repositories import (
            get_dynamic_repository,
        )
        from pixie.core.utils.database_attributes import DatabaseAttributeManager

        with get_db_session() as session:
            # Get repositories
            product_types_repo = get_dynamic_repository(session, "product_types")
            attr_repo = get_dynamic_repository(session, "attribute_definitions")

            # Find laptop product type
            laptop_types = product_types_repo.find_by_column("name", "laptop")
            if not laptop_types:
                print("❌ No laptop product type found")
                return False

            laptop_type_id = laptop_types[0]["id"]

            # Get all laptop attributes without questions
            laptop_attrs = attr_repo.filter_by_attributes(
                {"product_type_id": laptop_type_id}
            )

            print(f"📋 Found {len(laptop_attrs)} laptop attributes")

            # Create database attribute manager
            db_mgr = DatabaseAttributeManager(session)

            # Update each attribute with a generated question
            updated_count = 0
            for attr in laptop_attrs:
                attr_name = attr["name"]
                existing_question = attr.get("question")

                if existing_question:
                    print(f"✅ {attr_name}: Already has question - {existing_question}")
                    continue

                print(f"🔄 Generating question for {attr_name}...")

                # Generate question using the corrected LLM
                question = db_mgr._generate_llm_question(
                    attr_name,
                    attr.get("display_name", attr_name),
                    attr.get("data_type", "string"),
                    attr.get("description", ""),
                    attr.get("options"),
                )

                print(f"   Generated: {question}")

                # Update the attribute in database
                try:
                    # Use SQLAlchemy text for raw SQL
                    from sqlalchemy import text

                    session.execute(
                        text(
                            "UPDATE attribute_definitions SET question = :question WHERE id = :id"
                        ),
                        {"question": question, "id": attr["id"]},
                    )
                    session.commit()
                    print(f"✅ Updated {attr_name} with question")
                    updated_count += 1

                except Exception as e:
                    print(f"❌ Failed to update {attr_name}: {e}")
                    session.rollback()
                    return False

            print(
                f"\n🎉 Successfully updated {updated_count} laptop attribute questions!"
            )
            return True

    except Exception as e:
        print(f"❌ Error updating questions: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🤖 LLM Question Generation for Laptop Attributes")
    print("=" * 60)

    success = update_laptop_questions()

    if success:
        print("\n🎉 All done! Laptop attributes now have LLM-generated questions!")
    else:
        print("\n❌ Failed to update questions!")
        sys.exit(1)
