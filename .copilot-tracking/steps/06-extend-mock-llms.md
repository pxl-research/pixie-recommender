# Step 6: Mock LLM Uitbreiding voor Testing

## Objective
Breidt alle Mock LLM implementaties uit om multi-category ondersteuning te testen zonder Azure dependencies.

## Prerequisites
- Stap 2 voltooid: Relevance LLM categorie detectie
- Stap 5 voltooid: SQL LLM category ondersteuning
- Kennis van huidige Mock LLM implementaties

## Actions
1. Update MockRelevance in mock_llm_set.py:
   - Implement detect_category method met keyword matching
   - Keywords per categorie: laptop, computer, smartphone, printer
2. Update MockSQL voor category support:
   - Template SQL queries per categorie
   - Category-specific SELECT statements
3. Update MockRefinement voor category-aware questions:
   - Different question templates per category
   - Use category-specific attribute priorities
4. Test mock implementations met alle categorieën
5. Zorg dat mock behavior consistent is met Azure LLMs
6. Update existing tests die mock LLMs gebruiken

## Success Criteria
- MockRelevance kan alle 4 categorieën detecteren
- MockSQL genereert juiste queries per categorie
- MockRefinement stelt category-appropriate vragen
- Mock behavior is consistent met Azure LLM interfaces
- Bestaande tests blijven werken met mock LLMs
- Nieuwe categorieën zijn testbaar zonder Azure dependencies

## Next Step
Continue to: `07-extend-configuration.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
