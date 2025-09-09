<!-- markdownlint-disable-file -->
# Task Details: Conversation Loop Flow Implementation

## Research Reference

**Source Research**: #file:../research/20250908-conversation-loop-flow-research.md

## Fase 1: Foundation Components

### Stap 1.1: Creëer abstracte LLM base class

Implementeer de basis abstracte klasse die de user specificeerde in de requirements. Deze klasse vormt de basis voor toekomstige echte LLM implementaties.

- **Bestanden**:
  - pixie/core/abstractclasses/llm.py - Nieuwe abstracte base class
- **Success Criteria**:
  - Abstracte LLM klasse met model_name parameter in constructor
  - Geen concrete methods geïmplementeerd in base class
  - Import en instantiatie werkt correct
- **Research References**:
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 195-210) - MockLLM implementatie specificatie
- **Dependencies**:
  - Python ABC module voor abstracte base class definitie

### Stap 1.2: Implementeer MockLLM afgeleide klasse

Creëer concrete implementatie van LLM die eerste stap van conversation flow implementeert: relevantie analyse.

- **Bestanden**:
  - pixie/core/mock_llm.py - MockLLM implementatie
- **Success Criteria**:
  - MockLLM erft van abstracte LLM klasse
  - is_relevant() method detecteert "printer"/"printers" in input
  - Return True voor relevante vragen, False voor irrelevante
  - Eenvoudige string matching implementatie
- **Research References**:
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 377-385) - Relevance Rules specificatie
- **Dependencies**:
  - Stap 1.1 voltooid (abstracte LLM base class)

### Stap 1.3: Voeg SQL generatie toe aan MockLLM

Implementeer tweede stap van conversation flow: herformulering naar SQL query (gemockt).

- **Bestanden**:
  - pixie/core/mock_llm.py - Uitbreiding van bestaande MockLLM
- **Success Criteria**:
  - generate_sql() method toegevoegd aan MockLLM
  - Return altijd "SELECT * FROM printers;" voor mock implementatie
  - Method accepteert question en context parameters voor toekomstige uitbreiding
- **Research References**:
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 109-113) - SQL Query Generatie specificatie
- **Dependencies**:
  - Stap 1.2 voltooid (MockLLM basis implementatie)

## Fase 2: Search Engine Mock

### Stap 2.1: Creëer MockSearchEngine class

Implementeer mock search engine die configureerbare aantallen resultaten kan teruggeven voor testing van verschillende scenario's.

- **Bestanden**:
  - pixie/core/conversation_loop.py - Nieuwe MockSearchEngine klasse
- **Success Criteria**:
  - search() method accepteert SQL string en geeft list resultaten terug
  - Configureerbare scenarios: 0 resultaten, 1-5 resultaten, >5 resultaten
  - Eenvoudige regel-gebaseerde logica voor verschillende test cases
- **Research References**:
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 260-275) - MockSearchEngine specificatie
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 324-340) - Search Logic Rules
- **Dependencies**:
  - Basis Python data structures voor mock resultaten

### Stap 2.2: Implementeer mock product data

Voeg realistische mock product data toe die overeenkomt met de Nederlandse voorbeeldgesprekken.

- **Bestanden**:
  - pixie/core/conversation_loop.py - Mock data in MockSearchEngine
- **Success Criteria**:
  - Brother XC 2570 en Brother XT 3560 zoals in voorbeeldgesprekken
  - Brother ZX 1570, HP inkjet 234, Kyocera T70, HP inkjet 1234 voor "Weet ik niet" scenario
  - Configureerbare result sets voor verschillende test scenarios
  - Prijzen en beschrijvingen zoals gespecificeerd in voorbeelden
- **Research References**:
  - Nederlandse voorbeeldgesprekken - Exacte product namen en prijzen
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 307-323) - Mock Product Database structuur
- **Dependencies**:
  - Stap 2.1 voltooid (MockSearchEngine basis structuur)

## Fase 3: Conversation Manager Core

### Stap 3.1: Creëer ConversationLoopManager klasse

Implementeer de hoofdorchestrator die de 6-stappen conversation flow beheert.

- **Bestanden**:
  - pixie/core/conversation_loop.py - ConversationLoopManager klasse
- **Success Criteria**:
  - Constructor met configureerbare max_iterations (default 3)
  - handle_conversation_loop() method die AskResponse terugggeeft
  - Integratie met MockLLM en MockSearchEngine
  - Basis conversation state tracking
- **Research References**:
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 217-230) - ConversationLoopManager specificatie
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 275-290) - Enhanced Context Structure
- **Dependencies**:
  - Fase 1 voltooid (MockLLM implementatie)
  - Fase 2 voltooid (MockSearchEngine implementatie)

### Stap 3.2: Implementeer stappen 1-3 van flow

Implementeer eerste helft van conversation flow: relevantie, SQL generatie, en result count analyse.

- **Bestanden**:
  - pixie/core/conversation_loop.py - Uitbreiding ConversationLoopManager
- **Success Criteria**:
  - Stap 1: Relevantie check via MockLLM.is_relevant()
  - Stap 2: SQL generatie via MockLLM.generate_sql() en MockSearchEngine.search()
  - Stap 3: Result count beslissing (0/1-5/>5)
  - Correcte AskResponse types: not_relevant, no_results, answer
- **Research References**:
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 104-118) - Stappen 1-3 specificatie
- **Dependencies**:
  - Stap 3.1 voltooid (ConversationLoopManager basis)

### Stap 3.3: Implementeer stappen 4-6 van flow

Implementeer tweede helft van conversation flow: max iterations, attribute selection, answer validation.

- **Bestanden**:
  - pixie/core/conversation_loop.py - Voltooiing ConversationLoopManager
  - pixie/core/mock_llm.py - Attribute related methods
- **Success Criteria**:
  - Stap 4: Max iterations check en subset return
  - Stap 5: Attribute selection (budget → merk → printtechnologie)
  - Stap 6: "Weet ik niet" detection en processing
  - Exacte Nederlandse vragen volgens voorbeeldgesprekken
- **Research References**:
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 119-132) - Stappen 4-6 specificatie
  - Nederlandse voorbeeldgesprekken - Exacte vraagformuleringen
- **Dependencies**:
  - Stap 3.2 voltooid (eerste helft conversation flow)

## Fase 4: Pixie Integration

### Stap 4.1: Voeg conversation loop routing toe aan Pixie.answer()

Integreer conversation loop met bestaande Pixie orchestrator zonder bestaande functionaliteit te breken.

- **Bestanden**:
  - pixie/core/pixie.py - Wijziging answer() method
- **Success Criteria**:
  - Behoud alle bestaande literal triggers exact hetzelfde
  - Route niet-herkende vragen naar conversation loop
  - Integratie met ConversationLoopManager
  - Alle bestaande tests blijven slagen
- **Research References**:
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 408-420) - Integration Approach
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 395-407) - Backward Compatibility Strategy
- **Dependencies**:
  - Fase 3 voltooid (volledige ConversationLoopManager)
  - Import van conversation loop componenten

### Stap 4.2: Implementeer conversation loop reply handling

Voeg "conversation_loop" flow handling toe aan Pixie.reply() voor multi-turn gesprekken.

- **Bestanden**:
  - pixie/core/pixie.py - Uitbreiding reply() method
- **Success Criteria**:
  - Herkenning van "conversation_loop" flow in pending context
  - Processing van attribute antwoorden via conversation manager
  - "Weet ik niet" handling en iteration tracking  
  - State persistence via bestaande pending store
- **Research References**:
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 421-435) - Enhanced Flow Coexistence
- **Dependencies**:
  - Stap 4.1 voltooid (conversation loop routing in answer())

## Fase 5: Testing & Validatie

### Stap 5.1: Creëer conversation loop unit tests

Implementeer uitgebreide unit tests voor alle conversation loop componenten.

- **Bestanden**:
  - tests/test_conversation_loop.py - Nieuwe test suite
- **Success Criteria**:
  - test_conversation_loop_basic() - Eenvoudig succesvol pad
  - test_conversation_loop_refinement() - Multi-turn verfijning
  - test_conversation_loop_max_iterations() - Iteration limit handling
  - test_conversation_loop_not_relevant() - Out-of-scope vragen
  - test_weet_ik_niet_handling() - "Weet ik niet" antwoorden
- **Research References**:
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 444-455) - Nieuwe Test Coverage
- **Dependencies**:
  - Fase 4 voltooid (volledige Pixie integratie)

### Stap 5.2: Valideer backward compatibility

Zorg ervoor dat alle bestaande functionaliteit ongewijzigd blijft werken.

- **Bestanden**:
  - Alle bestaande test bestanden - Moeten blijven slagen
- **Success Criteria**:
  - Alle bestaande tests in tests/test_api_routes.py slagen
  - Geen wijzigingen nodig aan bestaande tests
  - Geen performance regressie voor bestaande flows
  - Bestaande literal triggers werken identiek
- **Research References**:
  - #file:../research/20250908-conversation-loop-flow-research.md (Lijnen 437-443) - Bestaande Tests Behouden
- **Dependencies**:
  - Volledige implementatie afgerond

### Stap 5.3: Integratie testing voorbeeldgesprekken

Test alle Nederlandse voorbeeldgesprekken end-to-end om exacte compliance te waarborgen.

- **Bestanden**:
  - tests/test_conversation_examples.py - Voorbeeldgesprek tests
- **Success Criteria**:
  - Exact reproduce van alle 4 voorbeeldgesprekken
  - Correcte Nederlandse responses
  - Juiste flow routing en state management
  - End-to-end validatie via API endpoints
- **Research References**:
  - Nederlandse voorbeeldgesprekken - Complete gesprek scenarios
- **Dependencies**:
  - Stap 5.1 en 5.2 voltooid (unit tests en compatibility validatie)

## Dependencies

- Python ABC module voor abstracte base class
- Bestaande pixie-core architectuur (InMemoryPendingStore, AskResponse, etc.)
- FastAPI TestClient voor integratie tests

## Success Criteria

- Alle 6 stappen van conversation flow correct geïmplementeerd volgens specificatie
- Abstracte LLM basis voor toekomstige uitbreiding
- Volledige backward compatibility met bestaande functionaliteit
- Nederlandse voorbeeldgesprekken werken exact zoals gespecificeerd
- Uitgebreide test coverage voor alle nieuwe functionaliteit
