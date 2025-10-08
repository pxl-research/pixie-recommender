"""LLM for converting natural language replies to structured filters."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from .azure_openai_llm import AzureOpenAILLM

logger = logging.getLogger(__name__)


class AzureFilterLLM(AzureOpenAILLM):
    """Converts user replies to structured filter objects using an LLM."""

    def __init__(
        self,
        api_version: str,
        api_endpoint: str,
        api_key: str,
        model_version: str,
        temperature: float = 0.0,
        model_name: str = "azure-filter-llm",
    ) -> None:
        super().__init__(api_version, api_endpoint, api_key, model_version, temperature)
        self.model_name = model_name

    def build_filters(
        self, reply: str, attribute: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Convert a natural language reply into structured filters.

        Args:
            reply: User's natural language reply
            attribute: Attribute metadata (name, type, q1, q3, values, etc.)

        Returns:
            List of filter objects conforming to AttributeExactFilter or
            AttributeRangeFilter schema
        """
        if not reply or not reply.strip():
            return []

        attr_name = attribute.get("name")
        if not attr_name:
            return []

        attr_type = (attribute.get("type") or "").lower()
        q1 = attribute.get("q1")
        q3 = attribute.get("q3")
        values = attribute.get("values")
        description = attribute.get("description") or ""

        # Build the prompt
        prompt = self._build_prompt(
            reply, attr_name, attr_type, description, q1, q3, values
        )

        # Try to get structured output from LLM
        if self.model:
            try:
                response = self.model.invoke(prompt)
                if hasattr(response, "content"):
                    content = response.content.strip()
                    filters = self._parse_llm_response(content, attr_name)
                    if filters:
                        logger.info(
                            "filter_llm_success",
                            extra={"reply": reply, "filters": filters},
                        )
                        return filters
            except Exception as exc:
                logger.warning(
                    "filter_llm_failed",
                    extra={"reply": reply, "attribute": attr_name, "error": str(exc)},
                )

        # Fallback to simple rule-based logic
        fallback_filters = self._fallback_filter_building(reply, attribute)
        if fallback_filters:
            logger.info(
                "filter_fallback_used",
                extra={"reply": reply, "filters": fallback_filters},
            )
        return fallback_filters

    def _build_prompt(
        self,
        reply: str,
        attr_name: str,
        attr_type: str,
        description: str,
        q1: Any,
        q3: Any,
        values: Any,
    ) -> str:
        """Build the LLM prompt for filter generation."""
        # Determine if this is actually a numeric attribute
        is_numeric_categorical = (
            attr_type == "categorical"
            and isinstance(values, list)
            and values
            and all(isinstance(v, (int, float)) for v in values if v is not None)
        )

        prompt = (
            "Je bent een expert in het omzetten van natuurlijke taal naar "
            "gestructureerde database filters.\n\n"
        )
        prompt += f'GEBRUIKERSANTWOORD: "{reply}"\n\n'
        prompt += "ATTRIBUUT INFORMATIE:\n"
        prompt += f"- Naam: {attr_name}\n"
        prompt += f"- Type: {attr_type}\n"
        prompt += f"- Omschrijving: {description}\n"

        if attr_type in {"numeric", "continuous"} or is_numeric_categorical:
            prompt += f"""
Voor NUMERIEKE attributen zijn er twee filter types:

1. RANGE FILTER (voor bereiken):
{{"name": "{attr_name}", "type": "range", "min_value": X, "max_value": Y}}
- Gebruik min_value voor "meer dan", "vanaf", "minimaal"
- Gebruik max_value voor "minder dan", "tot", "maximaal"
- Gebruik beide voor "tussen X en Y"
"""
            if isinstance(q1, (int, float)) and isinstance(q3, (int, float)):
                prompt += f"- Typische waarden: laag={q1}, hoog={q3}\n"
            elif is_numeric_categorical and isinstance(values, list):
                sorted_vals = sorted([v for v in values if isinstance(v, (int, float))])
                if sorted_vals:
                    prompt += f"- Mogelijke waarden: {', '.join(str(v) for v in sorted_vals)}\n"

            prompt += """
VOORBEELDEN:
- "ongeveer 250 euro" → {{"name": "prijs", "type": "range", "min_value": 200, "max_value": 300}}
- "minder dan 1000" → {{"name": "prijs", "type": "range", "max_value": 1000}}
- "meer dan 500" → {{"name": "prijs", "type": "range", "min_value": 500}}
- "tussen 200 en 400" → {{"name": "prijs", "type": "range", "min_value": 200, "max_value": 400}}
"""

        elif attr_type == "boolean":
            prompt += f"""
Voor BOOLEAN attributen gebruik EXACT FILTER:
{{"name": "{attr_name}", "type": "exact", "value": true/false}}

VOORBEELDEN:
- "ja" → {{"name": "{attr_name}", "type": "exact", "value": true}}
- "nee" → {{"name": "{attr_name}", "type": "exact", "value": false}}
- "graag" → {{"name": "{attr_name}", "type": "exact", "value": true}}
- "niet nodig" → {{"name": "{attr_name}", "type": "exact", "value": false}}
"""

        elif attr_type == "categorical":
            prompt += f"""
Voor CATEGORISCHE attributen gebruik EXACT FILTER:
{{"name": "{attr_name}", "type": "exact", "value": "waarde"}}
"""
            if isinstance(values, list) and values:
                prompt += (
                    f"\nMogelijke waarden: {', '.join(str(v) for v in values[:10])}\n"
                )

            prompt += """
VOORBEELDEN:
- "Dell" → {{"name": "merk", "type": "exact", "value": "Dell"}}
- "Ik geef voorkeur aan HP" → {{"name": "merk", "type": "exact", "value": "HP"}}
"""

        else:
            # Generic/unknown type
            prompt += f"""
Voor dit attribuut gebruik EXACT FILTER:
{{"name": "{attr_name}", "type": "exact", "value": "waarde"}}
"""

        prompt += """
BELANGRIJKE REGELS:
1. Als het antwoord "weet ik niet", "geen voorkeur", etc. is → return []
2. Return ALLEEN valide JSON, geen uitleg
3. Return een array van filter objecten: [{{...}}] of []
4. Gebruik Nederlandse taal interpretatie
5. Wees conservatief: bij twijfel, return []

OUTPUT FORMAAT (alleen JSON, geen markdown):
[{{"name": "...", "type": "...", ...}}]
"""

        return prompt

    def _parse_llm_response(self, content: str, attr_name: str) -> List[Dict[str, Any]]:
        """Parse the LLM response into filter objects."""
        # Try to extract JSON from the response
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            )

        # Try to parse as JSON
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                # Validate each filter
                valid_filters = []
                for f in parsed:
                    if self._validate_filter(f, attr_name):
                        valid_filters.append(f)
                return valid_filters
            elif isinstance(parsed, dict) and self._validate_filter(parsed, attr_name):
                return [parsed]
        except json.JSONDecodeError:
            logger.warning("filter_llm_invalid_json", extra={"content": content})

        return []

    def _validate_filter(self, filter_obj: Dict[str, Any], attr_name: str) -> bool:
        """Validate a filter object matches the expected schema."""
        if not isinstance(filter_obj, dict):
            return False

        # Check required fields
        if filter_obj.get("name") != attr_name:
            return False

        filter_type = filter_obj.get("type")
        if filter_type not in {"exact", "range"}:
            return False

        # Validate based on type
        if filter_type == "exact":
            return "value" in filter_obj
        elif filter_type == "range":
            # Must have at least min_value or max_value
            return "min_value" in filter_obj or "max_value" in filter_obj

        return False

    def _fallback_filter_building(
        self, reply: str, attribute: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Simple rule-based fallback when LLM fails."""
        reply_lower = reply.strip().lower()
        attr_name = attribute.get("name")

        # Check for "don't know" type responses
        if any(
            phrase in reply_lower
            for phrase in [
                "weet niet",
                "geen voorkeur",
                "maakt niet uit",
                "doet er niet toe",
            ]
        ):
            return []

        attr_type = (attribute.get("type") or "").lower()
        values = attribute.get("values")

        # Check if this is actually a numeric attribute even if marked categorical
        is_numeric_categorical = (
            attr_type == "categorical"
            and isinstance(values, list)
            and values
            and all(isinstance(v, (int, float)) for v in values if v is not None)
        )

        # Simple numeric extraction for numeric/continuous attributes OR numeric categoricals
        if attr_type in {"numeric", "continuous"} or is_numeric_categorical:
            # Try to extract a number
            import re

            match = re.search(r"(\d+(?:[.,]\d+)?)", reply_lower)
            if match:
                try:
                    value = float(match.group(1).replace(",", "."))
                    # Create a range with 20% tolerance
                    span = max(value * 0.2, 10)
                    return [
                        {
                            "name": attr_name,
                            "type": "range",
                            "min_value": max(0, value - span),
                            "max_value": value + span,
                        }
                    ]
                except ValueError:
                    pass

        # Simple boolean detection
        if attr_type == "boolean":
            if any(word in reply_lower for word in ["ja", "wel", "graag", "true"]):
                return [{"name": attr_name, "type": "exact", "value": True}]
            elif any(word in reply_lower for word in ["nee", "niet", "geen", "false"]):
                return [{"name": attr_name, "type": "exact", "value": False}]

        # For categorical (non-numeric), try to find a match in known values
        if attr_type == "categorical" and not is_numeric_categorical:
            # Try to find a match in known values
            if isinstance(values, list):
                for val in values:
                    if str(val).lower() in reply_lower:
                        return [{"name": attr_name, "type": "exact", "value": str(val)}]
            # Fallback: use the reply directly
            if reply.strip():
                return [{"name": attr_name, "type": "exact", "value": reply.strip()}]

        return []
