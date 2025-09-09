---
applyTo: '.copilot-tracking/changes/20250908-conversation-loop-flow-changes.md'
---
<!-- markdownlint-disable-file -->
# Task Checklist: Conversation Loop Flow Implementation

## Overview

Implementeer een 6-stappen conversation loop flow die vraagrelevantie analyseert, SQL queries mockt, zoekresultaten simuleert en stapsgewijze verfijning uitvoert via gebruikersdialoog.

## Objectives

- Implementeer abstracte LLM base class en MockLLM afgeleide voor toekomstige uitbreidbaarheid
- Creëer ConversationLoopManager die 6-stappen flow orkestreert volgens Nederlandse voorbeeldgesprekken
- Integreer conversation loop met bestaande Pixie class zonder bestaande flows te breken
- Werk stap-voor-stap met kleine implementaties die telkens gecontroleerd worden

## Research Summary

### Project Files
- pixie/core/pixie.py - Huidige orchestrator met 4 literal triggers (248 regels)
- pixie/core/contracts.py - AskResponse structuur (24 regels)
- pixie/core/pending_store.py - In-memory conversatie state (58 regels)

### External References
- #file:../research/20250908-conversation-loop-flow-research.md - Uitgebreide analyse van huidige architectuur en implementatiestrategie
- Nederlandse voorbeeldgesprekken - Specificatie voor exacte mock responses en flows

### Standards References
- Bestaande code patterns - Eenvoudige, onderhoudbare mock implementations
- Huidige testing approach - Behoud alle bestaande test compatibility

## Implementation Checklist

### [ ] Fase 1: Foundation Components (kleine stappen, telkens review)

- [ ] Stap 1.1: Creëer abstracte LLM base class
  - Bestand: pixie/core/abstractclasses/llm.py
  - Eenvoudige ABC met model_name parameter
  - **REVIEW PUNT**: Controleer abstracte interface voor toekomstige uitbreiding

- [ ] Stap 1.2: Implementeer MockLLM afgeleide klasse  
  - Bestand: pixie/core/mock_llm.py
  - Implementeer is_relevant() method (stap 1 flow)
  - **REVIEW PUNT**: Test relevantie detectie voor "printer"/"printers"

- [ ] Stap 1.3: Voeg SQL generatie toe aan MockLLM
  - Uitbreid MockLLM met generate_sql() method (stap 2 flow)
  - Return altijd "SELECT * FROM printers;" voor mock
  - **REVIEW PUNT**: Valideer SQL mock implementatie

### [ ] Fase 2: Search Engine Mock (kleine stappen, telkens review)

- [ ] Stap 2.1: Creëer MockSearchEngine class
  - Bestand: pixie/core/conversation_loop.py
  - Configureerbare result counts: 0, 1-5, >5 scenarios
  - **REVIEW PUNT**: Test verschillende result count scenarios

- [ ] Stap 2.2: Implementeer mock product data
  - Hardcoded Brother printers volgens voorbeeldgesprekken
  - Configureerbare responses voor testing
  - **REVIEW PUNT**: Valideer mock data structuur

### [ ] Fase 3: Conversation Manager Core (kleine stappen, telkens review)

- [ ] Stap 3.1: Creëer ConversationLoopManager klasse
  - Basis orchestratie structuur in conversation_loop.py
  - Max iterations configuratie (default 3)
  - **REVIEW PUNT**: Controleer manager interface en configuratie

- [ ] Stap 3.2: Implementeer stappen 1-3 van flow
  - Relevantie check (stap 1)
  - SQL generatie en mock search (stap 2)  
  - Result count analysis (stap 3)
  - **REVIEW PUNT**: Test basis flow tot result count beslissing

- [ ] Stap 3.3: Implementeer stappen 4-6 van flow
  - Max iterations check (stap 4)
  - Attribute selection en vraag generatie (stap 5)
  - Answer relevantie validatie (stap 6)
  - **REVIEW PUNT**: Test complete conversation loop cyclus

### [ ] Fase 4: Pixie Integration (voorzichtige integratie, telkens review)

- [ ] Stap 4.1: Voeg conversation loop routing toe aan Pixie.answer()
  - Behoud alle bestaande literal triggers onveranderd
  - Route niet-literal vragen naar conversation loop
  - **REVIEW PUNT**: Zorg dat bestaande tests blijven slagen

- [ ] Stap 4.2: Implementeer conversation loop reply handling
  - Uitbreid Pixie.reply() voor "conversation_loop" flow
  - Handle attribute antwoorden en "Weet ik niet" responses
  - **REVIEW PUNT**: Test reply flow met mock responses

### [ ] Fase 5: Testing & Validatie (grondige testing, telkens review)

- [ ] Stap 5.1: Creëer conversation loop unit tests
  - Test alle 6 stappen van de flow afzonderlijk
  - Test edge cases zoals max iterations
  - **REVIEW PUNT**: Valideer test coverage en scenario's

- [ ] Stap 5.2: Valideer backward compatibility
  - Alle bestaande tests moeten blijven slagen
  - Geen performance impact op bestaande flows
  - **REVIEW PUNT**: Bevestig geen regressies geïntroduceerd

- [ ] Stap 5.3: Integratie testing voorbeeldgesprekken
  - Test alle Nederlandse voorbeeldgesprekken end-to-end
  - Valideer exacte responses volgens specificatie
  - **REVIEW PUNT**: Bevestig gesprekken werken zoals verwacht

## Dependencies

- Python 3.12 runtime (huidige project setup)
- Bestaande InMemoryPendingStore voor state management  
- FastAPI framework voor API compatibility

## Success Criteria

- Abstracte LLM klasse en MockLLM implementatie gereed voor toekomstige uitbreiding
- 6-stappen conversation loop werkt volgens Nederlandse voorbeeldgesprekken
- Alle bestaande literal triggers blijven onveranderd functioneren
- Alle bestaande tests slagen zonder wijzigingen
- Nieuwe conversation loop is volledig getest met edge cases
- Code is eenvoudig, onderhoudbaar en goed gedocumenteerd

## Review Process

**KRITIEK BELANGRIJK**: Na elke stap in de checklist:
1. Implementeer alleen die specifieke stap
2. Test de implementatie lokaal
3. Vraag om review en goedkeuring voordat verder te gaan
4. Wacht op expliciete goedkeuring voordat volgende stap wordt gestart
5. Geen commits zonder review goedkeuring

Dit zorgt voor:
- Controleerbare voortgang
- Vroege detectie van problemen  
- Mogelijkheid om richting bij te stellen
- Kwaliteitsborging bij elke stap
