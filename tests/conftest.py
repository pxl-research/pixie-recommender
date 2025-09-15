import os
import pytest

from pixie.core.llms import azure_llm_set


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
    def generate_refinement_question(self, context: dict) -> "str | None":
        stage = context.get("stage", "")
        # Check if this is the first question (ask_budget stage or no user attributes)
        system_keys = ["flow", "stage", "iterations", "question"]
        user_attrs = [k for k in context.keys() if k not in system_keys]
        if stage == "ask_budget" or not context or len(user_attrs) == 0:
            return "Wat is je budget?"
        if "budget" in context and "brand" not in context:
            return "Heb je een voorkeur voor een merk?"
        if "budget" in context and "brand" in context and "technology" not in context:
            return "Welke technologie heeft je voorkeur (inkjet/laser)?"
        return None


@pytest.fixture
def mock_llm_set():
    """LLM fixture that uses real Azure LLMs when available, falls back to mocks.

    This allows v0.5 real LLM testing while maintaining fast/reliable mock fallback.
    Set PIXIE_FORCE_MOCKS=1 to always use mocks even when Azure is configured.
    """
    # Check if we should force mock usage
    force_mocks = os.getenv("PIXIE_FORCE_MOCKS", "0") == "1"

    if not force_mocks:
        # Try to use real Azure LLMs if properly configured
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        azure_key = os.getenv("AZURE_OPENAI_KEY", "")

        # Check if Azure is properly configured (not default dev values)
        if (
            azure_endpoint
            and azure_endpoint != "https://example.openai.azure.com/"
            and azure_key
            and azure_key != "dummy-key-for-development"
        ):
            try:
                # Attempt to create real Azure LLMs
                real_llms = azure_llm_set.create_azure_llm_set()
                print(
                    f"✅ Using REAL Azure LLMs for testing (endpoint: {azure_endpoint})"
                )
                return real_llms
            except Exception as e:
                # If Azure LLMs fail, fall back to mocks with warning
                print(f"⚠️  Azure LLMs failed ({e}), falling back to mocks")

    # Default: Use mock LLMs for fast, predictable tests
    print("🔧 Using MOCK LLMs for testing")
    return MockRelevance(), MockSQL(), MockRefinement()
