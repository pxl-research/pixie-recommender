# Step 5: SQL LLM Aanpassing voor Universele Ondersteuning

## Objective
Pas de SQL LLM aan om universele SQL generatie te ondersteunen voor alle product categorieën met dynamische table names en attributen.

## Prerequisites
- Stap 3 voltooid: Multi-category search engine
- Stap 4 voltooid: Category-aware conversation context
- Kennis van huidige SQL LLM implementatie

## Actions
1. Analyseer huidige AzureSQLLLM implementatie in azure_sql_llm.py
2. Update SQL generation prompt om category en table name te accepteren:
   - Pass category information naar SQL LLM
   - Include available attributes per category in prompt
   - Generate SQL voor juiste table (printers, laptops, computers, smartphones)
3. Update Mock SQL LLM voor testing:
   - Category-aware SQL generation
   - Simple template-based SQL per category
4. Update LLM interface om category parameter te ondersteunen
5. Test SQL generation voor alle categorieën
6. Zorg dat generated SQL werkt met search engine filtering

## Success Criteria
- SQL LLM accepteert category parameter
- Generated SQL gebruikt correcte table names per category
- SQL queries bevatten juiste attributen per category
- Mock en Azure implementaties zijn consistent
- Generated SQL is compatible met search engine filtering
- Backward compatibility: printer SQL generation werkt ongewijzigd

## Next Step
Continue to: `06-extend-mock-llms.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
