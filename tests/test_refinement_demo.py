"""
Demonstration of the refined azure_refinement_llm functionality.
Shows how it works without hardcoded fallbacks, using only database attributes.
"""

import pytest

from pixie.core.llms.azure_refinement_llm import AzureRefinementLLM
from pixie.core.utils.database_attributes import get_database_attribute_manager


def test_refinement_progression_demo():
    """Demonstrate how refinement questions progress through attributes."""

    # Create refinement LLM
    llm = AzureRefinementLLM(
        api_version="2023-12-01-preview",
        api_endpoint="https://test.openai.azure.com/",
        api_key="test-key",
        model_version="gpt-4",
    )

    # Force to use predefined questions for predictable demo
    llm.model = None

    print("\n🔧 Demonstrating dynamic attribute collection for printers:")

    # Start with empty context
    context = {
        "category": "printers",
        "collected_attributes": [],
        "skipped_attributes": [],
    }

    # Collect up to 5 questions to show progression
    for i in range(5):
        question = llm.generate_refinement_question(context)

        if question is None:
            print(f"✅ Step {i+1}: All attributes collected!")
            break

        print(f"❓ Step {i+1}: {question}")

        # Simulate collecting an attribute (get next attribute name)
        attr_manager = get_database_attribute_manager()
        next_attr = attr_manager.get_next_missing_attribute("printers", context)

        if next_attr:
            attr_name = next_attr["name"]
            context["collected_attributes"].append(attr_name)
            print(f"   ✅ Collected: {attr_name}")
        else:
            break

    print(f"\n📊 Final context: {context}")


def test_different_categories_demo():
    """Show how it works with different product categories."""

    llm = AzureRefinementLLM(
        api_version="2023-12-01-preview",
        api_endpoint="https://test.openai.azure.com/",
        api_key="test-key",
        model_version="gpt-4",
    )
    llm.model = None

    print("\n🛍️ Demonstrating different product categories:")

    categories = ["printers", "laptop", "smartphone"]

    for category in categories:
        print(f"\n📱 Category: {category}")

        context = {
            "category": category,
            "collected_attributes": [],
            "skipped_attributes": [],
        }

        # Get first 2 questions for each category
        for i in range(2):
            question = llm.generate_refinement_question(context)

            if question is None:
                print(f"   ⚠️  No more attributes for {category}")
                break

            print(f"   ❓ Question {i+1}: {question}")

            # Simulate collecting the attribute
            attr_manager = get_database_attribute_manager()
            next_attr = attr_manager.get_next_missing_attribute(category, context)

            if next_attr:
                attr_name = next_attr["name"]
                context["collected_attributes"].append(attr_name)


if __name__ == "__main__":
    # Run demos manually
    test_refinement_progression_demo()
    test_different_categories_demo()
    print("\n✨ All demos completed successfully!")
