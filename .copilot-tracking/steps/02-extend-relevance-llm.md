# Step 2: Relevance LLM Uitbreiding voor Categorie Detectie

## Objective
Breidt de relevance LLM uit om niet alleen product-relevantie te detecteren, maar ook de specifieke product categorie te bepalen.

## Prerequisites
- Stap 1 voltooid: Nieuwe product data files beschikbaar
- Kennis van huidige AzureRelevanceLLM en MockRelevance implementatie

## Actions
1. Analyseer huidige relevance LLM interface in azure_relevance_llm.py
2. Voeg nieuwe methode toe: `detect_category(question: str) -> Optional[str]`
3. Update Azure implementation:
   - Prompt engineering voor categorie detectie
   - Return values: "printers", "laptops", "computers", "smartphones", None
4. Update Mock implementation:
   - Keyword-based categorie detectie
   - Consistent met Azure LLM return values
5. Update LLM set interfaces om category detection te ondersteunen
6. Test beide implementaties met verschillende vraag voorbeelden

## Success Criteria
- Nieuwe detect_category methode in beide LLM implementations
- Azure LLM kan categorieën correct detecteren uit Nederlandse vragen
- Mock LLM heeft betrouwbare keyword-based detectie
- Interface is consistent tussen Mock en Azure implementaties
- Method retourneert None voor niet-product gerelateerde vragen

## Next Step
Continue to: `03-adapt-search-engine.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
