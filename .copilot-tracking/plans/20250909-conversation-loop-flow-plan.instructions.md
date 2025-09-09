---
applyTo: '.copilot-tracking/changes/20250909-conversation-loop-flow-changes.md'
---
<!-- markdownlint-disable-file -->
# Task Checklist: Conversation Loop Flow

## Overview

Herzien planning voor de conversation-loop mock-implementatie die LLM-beslissingen simuleert voor printer-gerelateerde zoekvragen.

## Objectives

- Respecteer de bestaande abstracte `LLM` in `pixie/core/abstractclasses/llm.py`. **NIET** wijzigen.
- Plan de implementatie van `MockLLM`, `ConversationLoopManager` en `MockSearchEngine` in kleine, controleerbare stappen met goedkeuringspoorten.

## Research Summary

### Project Files
- `pixie/core/pixie.py` - Route en flowbeheer
- `pixie/core/pending_store.py` - In-memory pending store
- `apps/api/main.py` - Bestaande `/ask` endpoint

### External References
- #file:../research/20250908-conversation-loop-flow-research.md - Uitgebreid onderzoek en specificaties voor de 6-stappen flow

## Implementation Checklist

### [ ] Phase 1: Core Infrastructure (planning-only)

- [ ] Task 1.1: Valideer bestaande `LLM` abstract class (geen wijzigingen)
  - Details: .copilot-tracking/details/20250909-conversation-loop-flow-details.md (Lines 10-24)
  - Approval gate: STOP — wacht op jouw schriftelijke goedkeuring voordat code-implementatie start.

- [ ] Task 1.2: Plan implementatie van `MockLLM` (concrete specificatie)
  - Details: .copilot-tracking/details/20250909-conversation-loop-flow-details.md (Lines 26-40)
  - Approval gate: STOP — na planreview en jouw akkoord mag implementatie uitgevoerd worden.

- [ ] Task 1.3: Plan implementatie van `MockSearchEngine` (concrete specificatie)
  - Details: .copilot-tracking/details/20250909-conversation-loop-flow-details.md (Lines 42-55)
  - Approval gate: STOP — wacht op akkoord voor uitvoering.

### [ ] Phase 2: Conversation Loop Manager

- [ ] Task 2.1: Plan `ConversationLoopManager` design en interaction contract
  - Details: .copilot-tracking/details/20250909-conversation-loop-flow-details.md (Lines 57-74)
  - Approval gate: STOP — ontwerpreview en akkoord vereist.

- [ ] Task 2.2: Plan integratie met `Pixie` (routing /reply /answer) zonder codewijzigingen aan abstract classes
  - Details: .copilot-tracking/details/20250909-conversation-loop-flow-details.md (Lines 75-88)
  - Approval gate: STOP — wacht op jouw schriftelijke goedkeuring voor implementatie.

### [ ] Phase 3: Testing & Edge Cases

- [ ] Task 3.1: Plan testcases (geen uitvoering zonder akkoord)
  - Details: .copilot-tracking/details/20250909-conversation-loop-flow-details.md (Lines 91-108)
  - Approval gate: STOP — testplan review en akkoord vereist.

- [ ] Task 3.2: Plan edge-case validaties (max_iterations, TTL, fallbacks)
  - Details: .copilot-tracking/details/20250909-conversation-loop-flow-details.md (Lines 109-119)
  - Approval gate: STOP — wacht op akkoord voor uitvoering.

## Dependencies

- Python project (pyproject.toml), pytest available
- Geen externe LLM of DB benodigd voor deze iteratie

## Success Criteria

- MockLLM en MockSearchEngine aanwezig en getest
- ConversationLoopManager geïmplementeerd en geïntegreerd in `Pixie`
- Bestaande tests blijven slagen; nieuwe tests toegevoegd
