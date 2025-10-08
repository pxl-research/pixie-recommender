# Conversation Loop Task Backlog

Deze takenlijst vat de kleine, beheersbare tickets samen om de conversation flow te verbeteren met behoud van een LLM-first aanpak.

## Tickets

1. **Define lightweight `ConversationState` model**  
   - Voeg een minimale dataclass toe met velden voor `conversation_id`, turns, actieve filters, gevraagde attributen, status en timestamps.
   - Schrijf korte unit-test(s) die defaultconstructie en lijstinitialisatie controleren.
   - Geen andere componenten aanpassen.

2. **Implement in-memory `ConversationRepository`**  
   - Bouw een eenvoudige repository met `create`, `get`, `update`, `expire_stale` op basis van een dictionary + TTL.
   - Voorzie unit-tests die CRUD en verstrijken van TTL aantonen.
   - Nog geen externe opslag integreren.

3. **Wire repository into `Pixie` bootstrap**  
   - Instantieer het repository-object binnen `Pixie.__init__` en geef het door aan actieve conversatiemanagers.
   - Voeg loggingcontext toe (`conversation_id`, turn-index) zonder bestaand gedrag te breken.
   - Zorg dat bestaande scripts/tests blijven werken.

4. **Introduce `ConversationAction` enum + manager skeleton**  
   - Maak een enum met `ASK_ATTRIBUTE`, `REFINE_RESULTS`, `SHOW_RESULTS`, `END`.
   - Introduceer `ConversationLoopManager` met methodes `handle_new_question` en `handle_reply` die voorlopig `NotImplementedError` werpen.
   - Geen gebruik in productiecode totdat vervolgtickets klaar zijn.

5. **Port direct-flow logica naar loop manager (minimal viable)**  
   - Verplaats/refactor logica uit `DirectConversationManager` zodat state wordt opgeslagen via het repository.
   - Activeer via featureflag (bijvoorbeeld `PIXIE_ACTIVE_FLOW=loop`), behoud de oude manager als fallback.
   - Schrijf unit-tests voor happy path en scenario “te veel resultaten → vraag → antwoord”.

6. **Update FastAPI `/ask` endpoint voor `conversation_id`**  
   - Breid `AskPayload` uit met optionele `conversation_id` en stuur dit door naar `Pixie`.
   - Laat responses altijd het actieve conversation ID bevatten.
   - Verifieer achterwaartse compatibiliteit met bestaande clients.

7. **Refresh refinement & result prompts (LLM driven)**  
   - Herwerk prompts zodat ze eerdere antwoorden erkennen en uitleggen waarom er een vraag wordt gesteld.
   - Voer enkel wijzigingen door die via de LLM verlopen; geen hardcoded alternatief gedrag.
   - Documenteer voorbeeldinvoer/-uitvoer en controleer maximale lengte (≤120 tekens).

8. **Documenteer conversatiescenario’s**  
   - Maak `docs/conversation-scenarios.md` met transcriptvoorbeelden (happy path, onzeker antwoord, geen resultaten).
   - Benoem welke prompts/responses verwacht worden zodat QA kan valideren.
   - Link naar dit document vanuit README of developer guide.

---

Vink elke taak af na voltooiing en houd scopes klein om de proof-of-concept wendbaar te houden.
