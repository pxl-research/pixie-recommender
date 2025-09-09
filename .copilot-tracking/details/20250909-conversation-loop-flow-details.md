<!-- markdownlint-disable-file -->
# Task Details: Conversation Loop Flow

## Research Reference

**Source Research**: #file:../research/20250908-conversation-loop-flow-research.md

## Phase 1: Core Infrastructure

### Task 1.1: Validate existing `LLM` abstract class (NO CODE CHANGES)

De planner zal *niet* het bestand `pixie/core/abstractclasses/llm.py` wijzigen. De bestaande abstracte klasse moet ongewijzigd blijven en wordt als contract behandeld.

- **Action (planning-only)**: Review de huidige `llm.py` en bevestig dat de interface voldoet aan de implementatie-eisen (presence van constructor en documentatie). Noteer eventuele ontbrekende abstractmethoden als opmerkingen in dit details-bestand.
- **Files**:
  - `pixie/core/abstractclasses/llm.py` (do not modify)
- **Approval gate**: STOP — wacht op jouw akkoord voordat enige implementatiestap wordt uitgevoerd.

### Task 1.2: Plan `MockLLM` (concrete specificatie, NO IMPLEMENTATION)

Beschrijf exact wat `MockLLM` moet doen zonder code te schrijven:

- `is_relevant`: zoekt naar "printer" of "printers" (case-insensitive)
- `generate_sql`: retourneert `SELECT * FROM printers;`
- `generate_refinement_question`: geeft de volgende vraag terug op basis van context (budget → merk → technologie)

- **Files (planned)**:
  - `pixie/core/mock_llm.py` (do not create without approval)
- **Approval gate**: STOP — wacht op jouw schriftelijke goedkeuring van deze specificatie.

### Task 1.3: Plan `MockSearchEngine` (NO IMPLEMENTATION)

Beschrijf het zoekgedrag en test-scenarios zonder codewijzigingen:

- `search(sql: str, attributes: dict = None) -> list[dict]`
- Gedrag:
  - budget == "minder dan 50€" → []
  - attributes leeg → >5 resultaten (152 mock items)
  - attributes gedeeltelijk aanwezig → 1-5 resultaten

- **Files (planned)**:
  - `pixie/core/mock_search.py` (do not create without approval)
- **Approval gate**: STOP — wacht op jouw akkoord voor uitvoering.

## Phase 2: Conversation Loop Manager

### Task 2.1: Design `ConversationLoopManager` (NO IMPLEMENTATION)

Definieer het API-contract en state machine zonder codewijzigingen:

- Constructor: `ConversationLoopManager(max_iterations: int = 3)`
- Methoden (planned):
  - `handle_new_question(question: str) -> AskResponse`
  - `handle_reply(pending_id: str, reply: str) -> AskResponse`
- Gebruik `MockLLM` en `MockSearchEngine` (gekozen implementaties pas na jouw akkoord)

- **Files (planned)**:
  - `pixie/core/conversation_loop.py` (do not create without approval)
- **Approval gate**: STOP — ontwerp review en akkoord vereist.

### Task 2.2: Plan integratie met `Pixie` (NO IMPLEMENTATION)

Beschrijf precies hoe routing en integratie eruit zal zien zonder codewijzigingen:

- Import contract en waar wijzigingen plaatsvinden in `pixie/core/pixie.py`
- Routingregels: existing literal checks first; anders route naar conversation loop manager
- Reply handling: gebruik bestaande pending store en context schema

- **Files (planned)**:
  - `pixie/core/pixie.py` (do not modify without approval)
- **Approval gate**: STOP — wacht op akkoord.

## Phase 3: Testing & Edge Cases

### Task 3.1: Plan testcases (NO IMPLEMENTATION)

- Definieer testcases in detail:
  - `not_relevant` (input: "Ik zoek mijn mama") → expect `not_relevant`
  - `basic success path` (chain of replies) → expect final `answer` with list
  - `weet_ik_niet path` → expect iterative attribute skipping and final choose-option
  - `max_iterations reached` → expect subset response

- **Files (planned)**:
  - `tests/test_conversation_loop.py` (do not add without approval)
- **Approval gate**: STOP — testplan akkoord vereist before adding tests.

### Task 3.2: Edge cases

- Validate TTL behaviour via `InMemoryPendingStore`
- Test malformed pending_id

## Dependencies

- #file:../research/20250908-conversation-loop-flow-research.md (Lines 1-819)
- Existing project files: `pixie/core/pixie.py`, `pixie/core/pending_store.py`, `apps/api/main.py`

## Success Criteria (planning-only)

- Alle designs en specificaties gereviewd en goedgekeurd door jou
- Implementatie wordt pas uitgevoerd na jouw expliciete goedkeuring per stap
- Na uitvoering van elke stap: tests en integratie uitgevoerd en alleen bij jouw akkoord wordt verdergegaan
