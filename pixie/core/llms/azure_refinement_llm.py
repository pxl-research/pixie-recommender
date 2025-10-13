from __future__ import annotations

from typing import Optional

from .azure_openai_llm import AzureOpenAILLM


class AzureRefinementLLM(AzureOpenAILLM):
    """Generates friendly follow-up questions to refine the product search."""

    def __init__(
        self,
        api_version: str,
        api_endpoint: str,
        api_key: str,
        model_version: str,
        temperature: float = 0.01,
        model_name: str = "azure-refinement-llm",
    ) -> None:
        super().__init__(api_version, api_endpoint, api_key, model_version, temperature)
        self.model_name = model_name

    def generate_question(self, context: Optional[dict] = None) -> Optional[str]:
        ctx = context or {}
        category = ctx.get("category") or "het product"
        attribute = ctx.get("attribute") or {}
        applied_filters = ctx.get("applied_filters") or []
        asked_attributes = ctx.get("asked_attributes") or []
        reason = ctx.get("reason") or ""
        attribute_name = attribute.get("name")
        description = attribute.get("description") or ""
        attr_type = attribute.get("type")
        q1 = attribute.get("q1")
        q3 = attribute.get("q3")
        values = attribute.get("values")

        if not attribute_name:
            return None

        label = attribute_name.replace("_", " ")

        if not self.model:
            return None

        options = attribute.get("options") or []
        examples = attribute.get("examples") or []

        prompt_parts = [
            "Je bent een vriendelijke Nederlandse productadviseur.",
            "Formuleer een behulpzame vervolgvraag die uitlegt waarom dit attribuut relevant is en die de gebruiker richting geeft.",
            "Je mag één of twee zinnen gebruiken; eindig met een vraagteken en geef alleen de vraag terug.",
            f"Categorie: {category}",
            f"Attribuut: {label}",
            f"Beschrijving: {description}",
        ]
        if attr_type:
            prompt_parts.append(f"Attribuut-type: {attr_type}")
        if isinstance(q1, (int, float)) and isinstance(q3, (int, float)):
            prompt_parts.append(f"Typische waarden (q1/q3): {q1} / {q3}")
        if isinstance(values, list) and values:
            prompt_parts.append(f"Mogelijke ruwe waarden: {values[:5]}")
        if options:
            prompt_parts.append(f"Suggesties die je mag noemen: {options[:5]}")
        if examples:
            prompt_parts.append(f"Voorbeelden voor je vraag: {examples[:5]}")
        if applied_filters:
            prompt_parts.append(f"Al gekozen voorkeuren: {applied_filters}")
        if asked_attributes:
            prompt_parts.append(f"Eerder besproken attributen: {asked_attributes}")
        if reason:
            prompt_parts.append(f"Reden voor vervolg: {reason}")
        prompt_parts.append(
            "Richtlijnen per type:\n"
            "- Numeriek: bied één of twee voorbeeldbereiken of vraag naar een doelwaarde.\n"
            "- Categorisch: noem een paar relevante opties en vraag naar voorkeur.\n"
            "- Boolean: maak duidelijk dat het om een ja/nee keuze gaat."
        )
        prompt_parts.append("Zorg dat de toon vriendelijk en concreet is.")

        prompt = "\n".join(str(part) for part in prompt_parts if part)

        try:
            response = self.model.invoke(prompt)
            if hasattr(response, "content"):
                answer = response.content.strip().strip("\"'")
                if not answer.endswith("?"):
                    answer += "?"
                if len(answer) >= 5:
                    return answer
        except Exception:
            pass
        return None
