#!/usr/bin/env python3
"""
Script to generate and update questions for existing attributes using LLM.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def update_mixer_questions():
    """Update mixer attributes with LLM-generated questions."""
    print("🤖 Generating questions for mixer attributes using LLM...")

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

            # Find mixer product type
            mixer_types = product_types_repo.find_by_column("name", "mixer")
            if not mixer_types:
                print("❌ No mixer product type found")
                return False

            mixer_type_id = mixer_types[0]["id"]

            # Get all mixer attributes
            mixer_attrs = attr_repo.filter_by_attributes(
                {"product_type_id": mixer_type_id}
            )

            print(f"📋 Found {len(mixer_attrs)} mixer attributes")

            # Create database attribute manager
            db_mgr = DatabaseAttributeManager(session)

            # Update each attribute with a generated question
            for attr in mixer_attrs:
                attr_name = attr["name"]
                existing_question = attr.get("question")

                if existing_question:
                    print(f"✅ {attr_name}: Already has question - {existing_question}")
                    continue

                print(f"🔄 Generating question for {attr_name}...")

                # Generate question using the LLM
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

                except Exception as e:
                    print(f"❌ Failed to update {attr_name}: {e}")
                    session.rollback()
                    return False

            print("\n🎉 Successfully updated all mixer attribute questions!")
            return True

    except Exception as e:
        print(f"❌ Error updating questions: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_updated_questions():
    """Test that the updated questions work correctly."""
    print("\n🧪 Testing updated questions...")

    try:
        from pixie.core.utils.database_attributes import get_database_attribute_manager

        manager = get_database_attribute_manager()
        manager.clear_cache()  # Clear cache to get fresh data

        # Test mixer attributes
        mixer_attrs = manager.get_attributes_for_category("mixer")

        if mixer_attrs:
            print(f"✅ Found {len(mixer_attrs)} mixer attributes with questions:")
            for attr in mixer_attrs:
                print(f"  - {attr['name']}: {attr['question']}")
            return True
        else:
            print("❌ No mixer attributes found")
            return False

    except Exception as e:
        print(f"❌ Error testing questions: {e}")
        return False


if __name__ == "__main__":
    print("🤖 LLM Question Generation for Attributes")
    print("=" * 50)

    success1 = update_mixer_questions()
    if success1:
        success2 = test_updated_questions()

        if success1 and success2:
            print("\n🎉 All done! Attributes now have LLM-generated questions!")
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    else:
        print("\n❌ Failed to update questions!")
        sys.exit(1)
