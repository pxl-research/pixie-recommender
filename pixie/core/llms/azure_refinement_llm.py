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
        fallback = f"Kun je iets vertellen over {label}?"

        if not self.model:
            return fallback

        prompt = (
            "Je bent een vriendelijke Nederlandse productadviseur. "
            "Stel één korte vraag (max 120 tekens) om de gebruiker te helpen "
            "zijn zoekopdracht te verfijnen. Noem in dezelfde zin waarom je deze vraag stelt."
            f"\nCategorie: {category}"
            f"\nAttribuut: {label}"
            f"\nBeschrijving: {description}"
        )
        if attr_type:
            prompt += f"\nType attribuut: {attr_type}"
        if isinstance(q1, (int, float)) and isinstance(q3, (int, float)):
            prompt += f"\nTypische waarden: q1={q1}, q3={q3}"
        if isinstance(values, list) and values:
            prompt += f"\nMogelijke waardes: {values[:5]}"
        if applied_filters:
            prompt += f"\nReeds gekozen voorkeuren: {applied_filters}"
        if asked_attributes:
            prompt += f"\nEerder besproken attributen: {asked_attributes}"
        if reason:
            prompt += f"\nReden voor vervolg: {reason}"
        prompt += (
            "\nGebruik toegankelijke taal, sluit af met een vraagteken, "
            "verwijs kort naar de reden voor de vraag en geef uitsluitend de vraag terug."
        )

        try:
            response = self.model.invoke(prompt)
            if hasattr(response, "content"):
                answer = response.content.strip().strip("\"'")
                if not answer.endswith("?"):
                    answer += "?"
                if 5 <= len(answer) <= 120:
                    return answer
        except Exception:
            pass
        return fallback

    def generate_result_intro(self, context: Optional[dict] = None) -> Optional[str]:
        ctx = context or {}
        category = ctx.get("category") or "de geselecteerde producten"
        count = ctx.get("count")
        filters = ctx.get("applied_filters") or []
        reason = ctx.get("reason") or ""

        if not self.model:
            return None

        prompt = (
            "Je bent een vriendelijke Nederlandse productadviseur. "
            "Schrijf één korte zin in het Nederlands (max 120 tekens) die uitlegt "
            "waarom je deze resultaten toont. Verwijs naar opgegeven voorkeuren als ze er zijn."
            f"\nCategorie: {category}"
        )
        if isinstance(count, int):
            prompt += f"\nAantal resultaten: {count}"
        if filters:
            prompt += f"\nToegepaste filters: {filters}"
        if reason:
            prompt += f"\nReden: {reason}"
        prompt += "\nGebruik geen opsommingstekens en eindig met een punt."

        try:
            response = self.model.invoke(prompt)
            if hasattr(response, "content"):
                answer = response.content.strip().strip("\"'")
                if 5 <= len(answer) <= 120:
                    return answer
        except Exception:  # pragma: no cover - defensive
            return None
        return None
