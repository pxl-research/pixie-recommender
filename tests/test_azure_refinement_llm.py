"""
Tests for AzureRefinementLLM without hardcoded fallbacks.
"""

from unittest.mock import Mock, patch

from pixie.core.llms.azure_refinement_llm import AzureRefinementLLM
from pixie.core.llms.azure_sql_llm import AzureSQLLLM


class TestAzureRefinementLLM:
    """Test suite for Azure refinement LLM functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.llm = AzureRefinementLLM(
            api_version="2023-12-01-preview",
            api_endpoint="https://test.openai.azure.com/",
            api_key="test-key",
            model_version="gpt-4",
        )

    def test_generate_refinement_question_uses_database_attributes(self):
        """Test refinement question generation using database attributes."""
        context = {"category": "printers", "collected_attributes": []}

        patch_path = (
            "pixie.core.llms.azure_refinement_llm." "get_database_attribute_manager"
        )

        with patch(patch_path) as mock_manager:
            mock_attr_manager = Mock()
            mock_manager.return_value = mock_attr_manager

            mock_next_attr = {
                "name": "budget",
                "question": "Wat is je budget voor de printer?",
                "type": "number",
                "required": True,
            }

            mock_attr_manager.get_next_missing_attribute.return_value = mock_next_attr
            expected_q = "Wat is je budget voor de printer?"
            mock_attr_manager.get_attribute_question.return_value = expected_q

            # Use predefined question when no LLM model
            self.llm.model = None
            question = self.llm.generate_refinement_question(context)

            assert question == expected_q


class TestAzureSQLLLMSimple:
    """Test suite for simple Azure SQL LLM enhancements."""

    def setup_method(self):
        """Setup test environment."""
        self.sql_llm = AzureSQLLLM(
            api_version="2023-12-01-preview",
            api_endpoint="https://test.openai.azure.com/",
            api_key="test-key",
            model_version="gpt-4",
        )

    def test_collect_attribute(self):
        """Test simple attribute collection."""
        self.sql_llm.collect_attribute("budget", "€200")

        assert "attributes" in self.sql_llm.context
        assert self.sql_llm.context["attributes"]["budget"] == "€200"

    def test_set_category(self):
        """Test category setting from relevance LLM."""
        self.sql_llm.set_category("printers")

        assert self.sql_llm.context["category"] == "printers"

    def test_generate_sql_with_context(self):
        """Test SQL generation with context."""
        # Set up context
        self.sql_llm.set_category("printers")
        self.sql_llm.collect_attribute("budget", "€200")

        # Mock the schema manager
        with patch("pixie.core.llms.azure_sql_llm.get_schema_manager") as mock_schema:
            mock_schema_manager = Mock()
            mock_schema.return_value = mock_schema_manager
            mock_schema_manager.generate_table_description.return_value = "Mock schema"

            # Test without LLM model (fallback)
            self.sql_llm.model = None
            sql = self.sql_llm.generate_sql("Ik zoek een printer")

            assert "SELECT p.* FROM products p" in sql
            assert "printers" in sql

    def test_reset_context(self):
        """Test context reset."""
        self.sql_llm.set_category("printers")
        self.sql_llm.collect_attribute("budget", "€200")

        self.sql_llm.reset_context()

        assert len(self.sql_llm.context) == 0

