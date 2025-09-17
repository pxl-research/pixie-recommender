#!/usr/bin/env python3
"""
Test script to verify the new DatabaseAttributeManager works correctly.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_database_attribute_manager():
    """Test the new database attribute manager with mixer data."""
    print("🧪 Testing DatabaseAttributeManager...")

    try:
        from pixie.core.utils.database_attributes import get_database_attribute_manager

        manager = get_database_attribute_manager()

        # Test mixer attributes
        print("\n📋 Testing mixer attributes...")
        mixer_attrs = manager.get_attributes_for_category("mixer")

        if mixer_attrs:
            print(f"✅ Found {len(mixer_attrs)} mixer attributes:")
            for attr in mixer_attrs:
                print(f"  - {attr['name']}: {attr['question']}")
        else:
            print("❌ No mixer attributes found")
            return False

        # Test next missing attribute
        print("\n🔍 Testing next missing attribute logic...")
        context = {}
        next_attr = manager.get_next_missing_attribute("mixer", context)

        if next_attr:
            print(f"✅ Next attribute: {next_attr['name']} - {next_attr['question']}")
        else:
            print("❌ No next attribute found")
            return False

        # Test with some collected attributes
        context = {"budget": "400", "type": "planetmixer"}
        next_attr = manager.get_next_missing_attribute("mixer", context)

        if next_attr:
            print(
                f"✅ Next attribute after budget+type: {next_attr['name']} - "
                f"{next_attr['question']}"
            )
        else:
            print("❌ Should still have more attributes to collect")
            return False

        # Test printer attributes (should work with existing data)
        print("\n🖨️ Testing printer attributes...")
        printer_attrs = manager.get_attributes_for_category("printers")

        if printer_attrs:
            print(f"✅ Found {len(printer_attrs)} printer attributes")
        else:
            print("⚠️ No printer attributes found (this is expected if not seeded)")

        return True

    except Exception as e:
        print(f"❌ Error testing DatabaseAttributeManager: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_fallback_attribute_manager():
    """Test the updated AttributeManager with database fallback."""
    print("\n🔄 Testing AttributeManager with database fallback...")

    try:
        from pixie.core.utils.attributes import get_attribute_manager

        manager = get_attribute_manager()

        # Test mixer attributes (should come from database)
        mixer_attrs = manager.get_attributes_for_category("mixer")

        if mixer_attrs:
            print(
                f"✅ AttributeManager found {len(mixer_attrs)} mixer attributes via database"
            )

            # Test next missing attribute
            context = {}
            next_attr = manager.get_next_missing_attribute("mixer", context)

            if next_attr:
                question = manager.get_attribute_question(next_attr)
                print(f"✅ Next question: {question}")
            else:
                print("❌ No next attribute found")
                return False
        else:
            print("❌ AttributeManager didn't find mixer attributes")
            return False

        return True

    except Exception as e:
        print(f"❌ Error testing AttributeManager: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Testing Database-Based Attribute System")
    print("=" * 50)

    success1 = test_database_attribute_manager()
    success2 = test_fallback_attribute_manager()

    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 All tests passed!")
        print("✨ Database attribute system is working correctly!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
