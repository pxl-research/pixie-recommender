# Step 1: Nieuwe Product Data Files Aanmaken

## Objective
Maak nieuwe JSON data files aan voor laptops, computers en smartphones met logische attributen en priority lists voor conversatie flow.

## Prerequisites
- Huidige printers.json structure als referentie
- Kennis van categorie-specifieke attributen per product type

## Actions
1. Analyseer huidige printers.json structuur en velden
2. Definieer attributen per categorie:
   - Laptops: price, brand, screen_size, processor, ram, storage, battery_life, usage_type
   - Computers: price, brand, processor, ram, storage, graphics_card, form_factor, usage_type  
   - Smartphones: price, brand, screen_size, storage, operating_system, camera_megapixels, battery_capacity
3. Maak laptops.json aan met ~15-20 laptop records
4. Maak computers.json aan met ~15-20 computer records  
5. Maak smartphones.json aan met ~15-20 smartphone records
6. Voeg per bestand een "_metadata" object toe met:
   - category name
   - attribute_priority lijst (volgorde van belangrijkheid voor vragen)
   - attribute_descriptions (korte beschrijving per attribuut)

## Success Criteria
- 3 nieuwe JSON files in pixie/core/data/ directory
- Elk file heeft consistente structure met printers.json
- Elke categorie heeft verschillende, logische attributen
- Metadata object bevat priority en descriptions
- Files kunnen geladen worden zonder JSON syntax errors

## Next Step
Continue to: `02-extend-relevance-llm.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
