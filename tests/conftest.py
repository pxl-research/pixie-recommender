import os

import pytest

from pixie.core.llms import azure_llm_set
from pixie.core.utils.attributes import get_attribute_manager


class MockRelevance:
    def is_relevant(self, text: str) -> bool:
        return True


class MockSQL:
    def generate_sql(self, question: str, attributes: dict | None = None) -> str:
        """Generate SQL query with proper budget filtering."""
        base_query = "SELECT * FROM printers"
        conditions = []

        # Define vague responses that should be ignored
        vague_responses = [
            "weet ik niet",
            "geen idee",
            "maakt niet uit",
            "doet er niet toe",
            "geen voorkeur",
            "weet niet",
            "onbekend",
            "nvt",
            "n.v.t.",
        ]

        if attributes:
            # Handle budget filtering
            if "budget" in attributes:
                budget_str = attributes["budget"].lower().strip()

                # Skip vague responses
                if budget_str not in vague_responses:
                    # Parse budget values (supporting different formats)
                    if "-" in budget_str and any(char.isdigit() for char in budget_str):
                        # Range format like "100-200" or "100-200 euro"
                        import re

                        numbers = re.findall(r"\d+", budget_str)
                        if len(numbers) >= 2:
                            min_price = int(numbers[0])
                            max_price = int(numbers[1])
                            conditions.append(
                                f"price >= {min_price} AND price <= {max_price}"
                            )
                        elif len(numbers) == 1:
                            max_price = int(numbers[0])
                            conditions.append(f"price <= {max_price}")
                    elif "maximaal" in budget_str or "max" in budget_str:
                        # Extract maximum value
                        import re

                        numbers = re.findall(r"\d+", budget_str)
                        if numbers:
                            max_price = int(numbers[-1])
                            conditions.append(f"price <= {max_price}")
                    elif any(char.isdigit() for char in budget_str):
                        # Extract any numeric value and treat as maximum
                        import re

                        numbers = re.findall(r"\d+", budget_str)
                        if numbers:
                            max_price = int(numbers[-1])
                            conditions.append(f"price <= {max_price}")

            # Handle brand filtering
            if "brand" in attributes and attributes["brand"]:
                brand = attributes["brand"].strip()
                if brand.lower() not in vague_responses:
                    conditions.append(f"brand = '{brand}'")

            # Handle technology filtering
            if "technology" in attributes and attributes["technology"]:
                tech = attributes["technology"].strip().lower()
                if tech not in vague_responses:
                    conditions.append(f"LOWER(technology) = '{tech}'")

            # Handle color requirement
            if "has_color" in attributes:
                if attributes["has_color"]:
                    conditions.append("has_color = true")
                else:
                    conditions.append("has_color = false")

            # Handle multifunction requirement
            if "is_multifunction" in attributes:
                if attributes["is_multifunction"]:
                    conditions.append("is_multifunction = true")
                else:
                    conditions.append("is_multifunction = false")

        # Combine base query with conditions
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            return base_query + where_clause + ";"

        return base_query + ";"


class MockRefinement:
    def __init__(self):
        self.attr_manager = get_attribute_manager()

    def generate_refinement_question(self, context: dict) -> "str | None":
        # Use the structured attribute system for consistent behavior
        next_attr = self.attr_manager.get_next_missing_attribute("printer", context)
        if next_attr:
            return self.attr_manager.get_attribute_question(next_attr)
        return None


@pytest.fixture
def mock_llm_set():
    # Use Azure LLMs if environment variables are set, otherwise fall back to mocks
    if (
        os.getenv("AZURE_OPENAI_ENDPOINT") != "https://example.openai.azure.com/"
        and os.getenv("AZURE_OPENAI_KEY") != "dummy-key-for-development"
        and os.getenv("AZURE_OPENAI_API_VERSION")
        and os.getenv("AZURE_OPENAI_MODEL")
    ):
        return azure_llm_set.create_azure_llm_set()
    else:
        return MockRelevance(), MockSQL(), MockRefinement()
