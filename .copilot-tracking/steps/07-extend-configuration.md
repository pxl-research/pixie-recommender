# Step 7: Configuration Uitbreiding voor Multi-Category

## Objective
Update de configuration om meerdere data files te ondersteunen en category-specific instellingen mogelijk te maken.

## Prerequisites
- Stap 1 voltooid: Nieuwe product data files
- Stap 3 voltooid: Multi-category search engine
- Kennis van huidige Config implementatie

## Actions
1. Analyseer huidige config.py structure
2. Update SearchConfig om meerdere data files te ondersteunen:
   - Change van single data_file naar data_files dictionary
   - Map category names naar file paths
3. Update environment variable handling:
   - Ondersteuning voor custom data file paths per category
   - Backward compatibility met bestaande PIXIE_DATA_FILE env var
4. Update config loading in main.py en test files
5. Test configuration loading met alle categorieën
6. Zorg dat default configuration werkt zonder extra env vars

## Success Criteria
- Config ondersteunt meerdere data files per categorie
- Environment variables werken voor custom file paths
- Backward compatibility met bestaande configuration
- Default config laadt alle 4 categorieën correct
- Configuration is toegankelijk voor SearchEngine
- Config loading werkt in zowel productie als test environment

## Next Step
Continue to: `08-extend-tests.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
