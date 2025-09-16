# Step 3: Search Engine Aanpassing voor Multi-Category

## Objective
Pas de search engine aan om meerdere product databases te ondersteunen en dynamisch de juiste database te kiezen op basis van categorie.

## Prerequisites
- Stap 1 voltooid: Nieuwe product data files beschikbaar
- Stap 2 voltooid: Categorie detectie functionaliteit
- Kennis van huidige SearchEngine implementatie

## Actions
1. Analyseer huidige search_engine.py implementatie
2. Update SearchEngine constructor om meerdere data files te laden:
   - Laad alle category JSON files in dictionary: {"printers": data, "laptops": data, ...}
   - Bewaar metadata per categorie (attribute priorities, descriptions)
3. Voeg category parameter toe aan search methods
4. Update filtering logic om category-specifieke attributen te ondersteunen
5. Zorg dat bestaande printer searches exact hetzelfde blijven werken
6. Test search functionaliteit per categorie

## Success Criteria
- SearchEngine kan alle 4 categorieën laden en zoeken
- Category-specifieke filtering werkt correct
- Metadata (attribute priorities) zijn toegankelijk per categorie
- Backward compatibility: bestaande printer searches werken ongewijzigd
- Search methods accepteren category parameter
- Default behavior (zonder category) valt terug op printers voor compatibility

## Next Step
Continue to: `04-extend-conversation-context.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
