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


class TestAzureSQLLLMEnhanced:
    """Test suite for enhanced Azure SQL LLM functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.sql_llm = AzureSQLLLM(
            api_version="2023-12-01-preview",
            api_endpoint="https://test.openai.azure.com/",
            api_key="test-key",
            model_version="gpt-4",
        )

    def test_build_entity_context(self):
        """Test progressive entity context building."""
        question = "Ik zoek een HP laser printer onder €200"
        detected_category = "printers"

        # Mock the database attribute manager
        with patch(
            "pixie.core.llms.azure_sql_llm.get_database_attribute_manager"
        ) as mock_manager:
            mock_attr_manager = Mock()
            mock_manager.return_value = mock_attr_manager
            mock_attr_manager.get_attributes_for_category.return_value = [
                {"name": "budget"},
                {"name": "brand"},
                {"name": "technology"},
            ]

            context = self.sql_llm.build_entity_context(question, detected_category)

            assert context["category"] == "printers"
            assert context["category_confidence"] == 0.9
            assert "hints" in context
            assert "brand_hint" in context["hints"]
            assert context["hints"]["brand_hint"] == "Hp"
            assert context["hints"]["technology_hint"] == "laser"
            assert "available_attributes" in context

    def test_determine_next_attributes(self):
        """Test attribute prioritization logic."""
        question = "Ik wil een printer met een budget van €150"
        context = {"category": "printers", "collected_attributes": ["budget"]}

        with patch(
            "pixie.core.llms.azure_sql_llm.get_database_attribute_manager"
        ) as mock_manager:
            mock_attr_manager = Mock()
            mock_manager.return_value = mock_attr_manager
            mock_attr_manager.get_attributes_for_category.return_value = [
                {"name": "budget", "required": True},
                {"name": "brand", "required": False},
                {"name": "technology", "required": False},
                {"name": "color", "required": False},
            ]

            # Set up entity context with budget hint
            self.sql_llm.entity_context = {"hints": {"budget_hint": "150"}}

            next_attrs = self.sql_llm.determine_next_attributes(question, context)

            # Should prioritize brand and technology over color
            assert len(next_attrs) >= 2
            attr_names = [attr["name"] for attr in next_attrs]
            assert "brand" in attr_names
            assert "technology" in attr_names

    def test_collect_attribute_value(self):
        """Test attribute collection with normalization."""
        # Test budget normalization
        success = self.sql_llm.collect_attribute_value("budget", "150", 0.9)
        assert success
        assert self.sql_llm.collected_attributes["budget"] == "€150"
        assert self.sql_llm.confidence_scores["budget"] == 0.9

        # Test brand normalization
        self.sql_llm.collect_attribute_value("brand", "hp", 0.8)
        assert self.sql_llm.collected_attributes["brand"] == "Hp"

        # Test technology normalization
        self.sql_llm.collect_attribute_value("technology", "laser printer", 1.0)
        assert self.sql_llm.collected_attributes["technology"] == "laser"

    def test_should_collect_more_attributes(self):
        """Test decision logic for continuing attribute collection."""
        question = "Ik zoek een goede printer"

        # Empty collection should continue
        assert self.sql_llm.should_collect_more_attributes(question)

        # With only non-critical attribute should continue
        self.sql_llm.collect_attribute_value("color", "zwart", 1.0)
        assert self.sql_llm.should_collect_more_attributes(question)

        # With budget should be more selective
        self.sql_llm.collect_attribute_value("budget", "€200", 1.0)
        self.sql_llm.collect_attribute_value("brand", "HP", 1.0)
        # With 3 attributes should not continue (fallback logic)
        self.sql_llm.collect_attribute_value("technology", "laser", 1.0)
        assert not self.sql_llm.should_collect_more_attributes(question)

    def test_enhanced_generate_sql(self):
        """Test SQL generation with progressive context."""
        question = "Ik zoek een HP laser printer"
        context = {
            "category": "printers",
            "attributes": {"budget": "€200", "brand": "HP", "technology": "laser"},
        }

        # Mock schema manager
        with patch("pixie.core.llms.azure_sql_llm.get_schema_manager") as mock_schema:
            mock_schema_manager = Mock()
            mock_schema.return_value = mock_schema_manager
            mock_schema_manager.generate_table_description.return_value = "Mock schema"

            # Mock attribute manager
            with patch(
                "pixie.core.llms.azure_sql_llm.get_database_attribute_manager"
            ) as mock_attr:
                mock_attr_manager = Mock()
                mock_attr.return_value = mock_attr_manager
                mock_attr_manager.get_attributes_for_category.return_value = []

                # Test without LLM model (fallback)
                self.sql_llm.model = None
                sql = self.sql_llm.generate_sql(question, context=context)

                assert "SELECT p.* FROM products p" in sql
                assert "JOIN product_types pt" in sql
                assert "pt.name = 'printers'" in sql

    def test_extract_entity_hints(self):
        """Test entity hint extraction from questions."""
        # Test budget extraction
        question1 = "Ik zoek een printer voor €150"
        hints1 = self.sql_llm._extract_entity_hints(question1)
        assert "budget_hint" in hints1
        assert hints1["budget_hint"] == "150"

        # Test brand extraction
        question2 = "Welke HP printers zijn er?"
        hints2 = self.sql_llm._extract_entity_hints(question2)
        assert "brand_hint" in hints2
        assert hints2["brand_hint"] == "Hp"

        # Test technology extraction
        question3 = "Ik wil een laser printer"
        hints3 = self.sql_llm._extract_entity_hints(question3)
        assert "technology_hint" in hints3
        assert hints3["technology_hint"] == "laser"

    def test_get_collection_summary(self):
        """Test collection summary generation."""
        # Set up some collected data
        self.sql_llm.entity_context = {"category": "printers"}
        self.sql_llm.collect_attribute_value("budget", "€200", 0.9)
        self.sql_llm.collect_attribute_value("brand", "HP", 0.8)

        summary = self.sql_llm.get_collection_summary()

        assert summary["entity_context"]["category"] == "printers"
        assert summary["total_collected"] == 2
        assert summary["avg_confidence"] == 0.85
        assert "budget" in summary["collected_attributes"]
        assert "brand" in summary["collected_attributes"]

    def test_reset_state(self):
        """Test state reset functionality."""
        # Set up some state
        self.sql_llm.entity_context = {"category": "printers"}
        self.sql_llm.collect_attribute_value("budget", "€200", 0.9)

        # Reset and verify
        self.sql_llm.reset_state()

        assert len(self.sql_llm.entity_context) == 0
        assert len(self.sql_llm.collected_attributes) == 0
        assert len(self.sql_llm.confidence_scores) == 0

    def test_integration_with_conversation_flow(self):
        """Test integration with the full conversation flow."""
        # Simulate a complete conversation flow
        question = "Ik zoek een goede printer voor thuis"

        # 1. Build entity context
        context = self.sql_llm.build_entity_context(question, "printers")
        assert context["category"] == "printers"

        # 2. Collect some attributes
        self.sql_llm.collect_attribute_value("budget", "€200", 0.9)
        self.sql_llm.collect_attribute_value("brand", "HP", 0.8)

        # 3. Check if we should collect more
        should_continue = self.sql_llm.should_collect_more_attributes(question)
        assert isinstance(should_continue, bool)

        # 4. Generate SQL with collected context
        with patch("pixie.core.llms.azure_sql_llm.get_schema_manager") as mock_schema:
            mock_schema_manager = Mock()
            mock_schema.return_value = mock_schema_manager
            mock_schema_manager.generate_table_description.return_value = "Mock schema"

            with patch(
                "pixie.core.llms.azure_sql_llm.get_database_attribute_manager"
            ) as mock_attr:
                mock_attr_manager = Mock()
                mock_attr.return_value = mock_attr_manager
                mock_attr_manager.get_attributes_for_category.return_value = []

                # Generate SQL
                sql = self.sql_llm.generate_sql(
                    question,
                    context={
                        "category": "printers",
                        "attributes": self.sql_llm.collected_attributes,
                    },
                )

                assert isinstance(sql, str)
                assert len(sql) > 0
        assert question is None
