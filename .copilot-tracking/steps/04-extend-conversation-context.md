# Step 4: Conversation Context Uitbreiding

## Objective
Breidt de conversation context uit om category tracking en category-specifieke attributen te ondersteunen.

## Prerequisites
- Stap 2 voltooid: Categorie detectie functionaliteit
- Stap 3 voltooid: Multi-category search engine
- Kennis van huidige conversation context structure

## Actions
1. Analyseer huidige context structure in conversation_loop.py
2. Update context dictionary om category te bewaren:
   - Voeg "category" veld toe voor detected category
   - Maak attributes dynamisch (niet hardcoded budget/brand/technology)
   - Bewaar attribute_priority list per category
3. Update ConversationLoopManager.handle_new_question():
   - Call relevance LLM voor category detection
   - Set category in context
   - Load category-specific attribute priorities
4. Update stage progression om dynamische attributen te gebruiken:
   - Vervang hardcoded stages door priority-based progression
   - Support voor verschillende attributen per category
5. Zorg voor backward compatibility met bestaande printer flows

## Success Criteria
- Context bevat category information
- Dynamische attribute handling per category
- Conversation flow gebruikt category-specific priorities
- Bestaande printer conversations werken ongewijzigd
- Context kan verschillende attributen per categorie bewaren
- Stage progression is gebaseerd op attribute priorities

## Next Step
Continue to: `05-adapt-sql-llm.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
