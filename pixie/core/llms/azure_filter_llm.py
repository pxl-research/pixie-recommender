"""LLM for converting natural language replies to structured filters."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

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
                        filters = self._normalise_filters(filters, attribute)
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

        return []

    def derive_filters_from_question(
        self, question: str, attributes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Ask the LLM to extract filters directly from the user's question."""
        question_text = (question or "").strip()
        if not question_text or not attributes or not self.model:
            return []

        prompt = self._build_initial_filter_prompt(question_text, attributes)
        try:
            response = self.model.invoke(prompt)
            if not hasattr(response, "content"):
                return []
            content = (response.content or "").strip()
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                logger.warning(
                    "initial_filter_invalid_json",
                    extra={"question": question_text, "content": content},
                )
                return []

            if isinstance(parsed, dict):
                parsed = [parsed]
            if not isinstance(parsed, list):
                return []

            attr_lookup = {
                str(attr.get("name")): attr
                for attr in attributes
                if isinstance(attr, dict) and attr.get("name")
            }
            filters: List[Dict[str, Any]] = []
            for entry in parsed:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("name")
                meta = attr_lookup.get(name)
                if not meta:
                    continue
                normalised = self._normalise_filters([entry], meta)
                if normalised:
                    filters.extend(normalised)
            if filters:
                logger.info(
                    "initial_filter_llm_success",
                    extra={"question": question_text, "filters": filters},
                )
            return filters
        except Exception as exc:  # defensive
            logger.warning(
                "initial_filter_llm_failed",
                extra={"question": question_text, "error": str(exc)},
            )
            return []

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

    def _build_initial_filter_prompt(
        self, question: str, attributes: List[Dict[str, Any]]
    ) -> str:
        limited: List[Dict[str, Any]] = []
        for attr in attributes:
            if not isinstance(attr, dict):
                continue
            name = attr.get("name")
            if not name:
                continue
            entry: Dict[str, Any] = {"name": name}
            attr_type = attr.get("type")
            if attr_type:
                entry["type"] = attr_type
            description = attr.get("description")
            if description:
                entry["description"] = description
            values = attr.get("values")
            if isinstance(values, list) and values:
                entry["values"] = values[:10]
            q1 = attr.get("q1")
            q3 = attr.get("q3")
            if isinstance(q1, (int, float)):
                entry["q1"] = q1
            if isinstance(q3, (int, float)):
                entry["q3"] = q3
            limited.append(entry)
            if len(limited) >= 20:
                break

        attributes_json = json.dumps(limited, ensure_ascii=False)

        prompt = (
            "Je bent een expert in het extraheren van gestructureerde filters uit gebruikersvragen.\n\n"
            "Je krijgt een vraag van een gebruiker en de lijst met mogelijke attributen."
            " Bepaal welke attributen expliciet of impliciet in de vraag voorkomen en geef passende filterwaarden terug.\n\n"
            f"VRAAG: \"{question}\"\n\n"
            "BESCHIKBARE ATTRIBUTEN (JSON):\n"
            f"{attributes_json}\n\n"
            "INSTRUCTIES:\n"
            "- Gebruik uitsluitend de attribuutnamen uit de lijst (exacte string in het veld 'name').\n"
            "- Voor categorische en boolean attributen gebruik een EXACT filter met een waarde uit de lijst 'values' (of de dichtstbijzijnde semantische match als het bijna gelijk is).\n"
            "- Voor numerieke attributen gebruik RANGE filters met 'min_value' en/of 'max_value'.\n"
            "- Als er meerdere voorkeuren in de vraag staan, geef meerdere filterobjecten terug.\n"
            "- Als een attribuut niet duidelijk aanwezig is, neem het niet op in het resultaat.\n"
            "- Retourneer enkel een JSON-array met filterobjecten.\n"
            "- Gebruik strikte JSON (dubbele aanhalingstekens, geen extra tekst).\n"
            "\nVOORBEELD:\n"
            "Vraag: 'Ik zoek een blauwe Ford Fiesta auto'\n"
            "Mogelijke uitvoer: [{\"name\": \"kleur\", \"type\": \"exact\", \"value\": \"blauw\"},"
            " {\"name\": \"merk\", \"type\": \"exact\", \"value\": \"Ford\"},"
            " {\"name\": \"model\", \"type\": \"exact\", \"value\": \"Fiesta\"}]\n"
            "(alleen als deze attributen in de lijst voorkomen).\n"
        )
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

    def _normalise_filters(
        self, filters: List[Dict[str, Any]], attribute: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        normalised: List[Dict[str, Any]] = []
        for filter_obj in filters:
            cleaned = self._normalise_filter(filter_obj, attribute)
            if cleaned:
                normalised.append(cleaned)
        return normalised

    def _normalise_filter(
        self, filter_obj: Dict[str, Any], attribute: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(filter_obj, dict):
            return None
        filter_type = filter_obj.get("type")
        if filter_type not in {"exact", "range"}:
            return None
        cleaned = dict(filter_obj)
        attr_kind = (attribute.get("type") or "").lower()
        values = attribute.get("values")
        is_numeric_categorical = (
            attr_kind == "categorical"
            and isinstance(values, list)
            and values
            and all(isinstance(v, (int, float)) for v in values if v is not None)
        )
        is_numeric = attr_kind in {"numeric", "continuous"} or is_numeric_categorical

        if filter_type == "range":
            has_value = False
            for key in ("min_value", "max_value"):
                if key in cleaned:
                    coerced = self._coerce_numeric(cleaned[key])
                    if coerced is None:
                        cleaned.pop(key, None)
                    else:
                        cleaned[key] = coerced
                        has_value = True
            if not has_value:
                return None
        else:  # exact
            value = cleaned.get("value")
            if is_numeric:
                coerced = self._coerce_numeric(value)
                if coerced is None:
                    return None
                cleaned["value"] = coerced
            elif attr_kind == "boolean":
                coerced_bool = self._coerce_boolean(value)
                if coerced_bool is None:
                    return None
                cleaned["value"] = coerced_bool
            else:
                if value is None:
                    return None
                cleaned["value"] = value if isinstance(value, str) else str(value)

        return cleaned

    @staticmethod
    def _coerce_numeric(value: Any) -> Optional[float]:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.strip().lower()
            cleaned = cleaned.replace("€", " ")
            cleaned = cleaned.replace("eur", " ")
            cleaned = cleaned.replace("euro", " ")
            match = re.search(r"-?\d+[\d.,]*", cleaned)
            if not match:
                return None
            number_text = match.group(0)
            if "," in number_text and "." in number_text:
                number_text = number_text.replace(".", "")
                number_text = number_text.replace(",", ".")
            else:
                number_text = number_text.replace(",", ".")
            try:
                return float(number_text)
            except ValueError:
                return None
        return None

    @staticmethod
    def _coerce_boolean(value: Any) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            text = value.strip().lower()
            if text in {"true", "ja", "yes", "y", "1"}:
                return True
            if text in {"false", "nee", "no", "n", "0"}:
                return False
        if isinstance(value, (int, float)):
            if value == 1:
                return True
            if value == 0:
                return False
        return None
