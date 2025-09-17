"""
Database-based attribute manager that replaces the JSON-based approach.
This enables the flexible repository system to work purely from database configuration.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..database.connection import get_db_session
from ..database.repositories.flexible_repositories import get_dynamic_repository


class DatabaseAttributeManager:
    """Manages product attributes directly from the database."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session
        self._attributes_cache: Dict[str, List[Dict[str, Any]]] = {}

    def _get_session(self) -> Session:
        """Get database session."""
        if self._session:
            return self._session
        return get_db_session().__enter__()

    def _load_attributes_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Load attributes for a category from database."""
        if category in self._attributes_cache:
            return self._attributes_cache[category]

        session = self._get_session()

        try:
            # Get product type repository
            product_types_repo = get_dynamic_repository(session, "product_types")

            # Find product type by name
            product_types = product_types_repo.find_by_column("name", category)
            if not product_types:
                self._attributes_cache[category] = []
                return []

            product_type_id = product_types[0]["id"]

            # Get attribute definitions repository
            attr_repo = get_dynamic_repository(session, "attribute_definitions")

            # Get all attributes for this product type, ordered by display_order
            attributes = attr_repo.filter_by_attributes(
                {"product_type_id": product_type_id}
            )

            # Sort by display_order
            attributes.sort(key=lambda x: x.get("display_order", 999))

            # Transform to expected format
            formatted_attributes = []
            for attr in attributes:
                formatted_attr = {
                    "name": attr["name"],
                    "display_name": attr["display_name"],
                    "question": self._generate_question_for_attribute(attr),
                    "type": self._map_data_type(attr["data_type"]),
                    "required": attr.get("is_required", False),
                    "options": attr.get("options"),
                    "description": attr.get("description"),
                }
                formatted_attributes.append(formatted_attr)

            self._attributes_cache[category] = formatted_attributes
            return formatted_attributes

        except Exception as e:
            print(f"Error loading attributes for {category}: {e}")
            self._attributes_cache[category] = []
            return []

    def _generate_question_for_attribute(self, attr: Dict[str, Any]) -> str:
        """Generate appropriate question for an attribute based on its properties."""
        attr_name = attr["name"]
        display_name = attr.get("display_name", attr_name)
        data_type = attr.get("data_type", "string")
        description = attr.get("description", "")
        options = attr.get("options")

        # If options are available, parse them
        if options and isinstance(options, str):
            import json

            try:
                options = json.loads(options)
            except Exception:
                options = None

        # Check if there's a pre-defined question in the database
        if "question" in attr and attr["question"]:
            return attr["question"]

        # Use LLM to generate contextual question
        return self._generate_llm_question(
            attr_name, display_name, data_type, description, options
        )

    def _generate_llm_question(
        self,
        attr_name: str,
        display_name: str,
        data_type: str,
        description: str,
        options: Optional[List[str]],
    ) -> str:
        """Use LLM to generate a natural Dutch question for the attribute."""
        try:
            from ..llms import create_azure_llm_set

            # Get LLM set (will fallback to mocks if Azure not available)
            relevance_llm, sql_llm, refinement_llm = create_azure_llm_set()

            # Create a proper prompt using the LLM's invoke method directly
            options_text = f", opties: {', '.join(options)}" if options else ""

            prompt = f"""
Genereer een korte, natuurlijke Nederlandse vraag voor dit product attribuut:

Attribuut: {display_name} ({attr_name})
Type: {data_type}{options_text}
Beschrijving: {description or 'Geen beschrijving'}

Richtlijnen:
- Houd het kort en duidelijk
- Begin met vraagwoorden zoals "Welke", "Hoeveel", "Wat"
- Voor keuzes: noem opties als er weinig zijn
- Voor getallen: vraag naar voorkeur/minimum waar relevant

Genereer alleen de vraag, geen extra tekst.
"""

            # Use the LLM's invoke method directly
            if hasattr(refinement_llm, "model") and refinement_llm.model:
                response = refinement_llm.model.invoke(prompt)

                if hasattr(response, "content") and response.content:
                    question = response.content.strip()
                    if question and len(question) > 0:
                        # Clean up the response
                        if not question.endswith("?"):
                            question += "?"
                        return question

        except Exception as e:
            print(f"Warning: Could not generate LLM question for {attr_name}: {e}")

        # Fallback to simple generic question
        return self._generate_fallback_question(display_name, data_type, options)

    def _generate_fallback_question(
        self, display_name: str, data_type: str, options: Optional[List[str]]
    ) -> str:
        """Generate a simple fallback question when LLM is unavailable."""
        display_name_lower = display_name.lower()

        if data_type == "choice" and options:
            if len(options) <= 5:
                options_str = ", ".join(options)
                return f"Welke {display_name_lower} heeft je voorkeur ({options_str})?"
            else:
                return f"Welke {display_name_lower} heeft je voorkeur?"
        elif data_type in ["number", "range"]:
            return f"Wat is je voorkeur voor {display_name_lower}?"
        elif data_type == "boolean":
            return f"Wil je {display_name_lower}?"
        else:
            return f"Wat zijn je voorkeuren voor {display_name_lower}?"

    def _map_data_type(self, db_data_type: str) -> str:
        """Map database data type to legacy format."""
        mapping = {
            "choice": "string",
            "range": "number",
            "text": "string",
            "number": "number",
            "boolean": "boolean",
        }
        return mapping.get(db_data_type, "string")

    def get_attributes_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all attributes for a specific category."""
        return self._load_attributes_for_category(category)

    def get_next_missing_attribute(
        self, category: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find the next attribute that hasn't been collected yet."""
        attributes = self.get_attributes_for_category(category)

        # Get list of attributes that are already collected or skipped
        collected_attributes = set(context.get("collected_attributes", []))
        skipped_attributes = set(context.get("skipped_attributes", []))
        processed_attributes = collected_attributes.union(skipped_attributes)

        for attr in attributes:
            attr_name = attr["name"]
            # Skip if attribute is already collected, skipped, or present in context
            if attr_name not in context and attr_name not in processed_attributes:
                return attr

        return None  # All attributes collected or skipped

    def get_attribute_question(self, attribute: Dict[str, Any]) -> str:
        """Get the question to ask for a specific attribute."""
        return attribute.get(
            "question", f"Wat zijn je voorkeuren voor {attribute['name']}?"
        )

    def clear_cache(self):
        """Clear the attributes cache."""
        self._attributes_cache.clear()


# Global instance
_database_attribute_manager: Optional[DatabaseAttributeManager] = None


def get_database_attribute_manager() -> DatabaseAttributeManager:
    """Get the global database attribute manager instance."""
    global _database_attribute_manager
    if _database_attribute_manager is None:
        _database_attribute_manager = DatabaseAttributeManager()
    return _database_attribute_manager
