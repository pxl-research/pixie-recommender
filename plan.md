# Plan van Aanpak v0.2: Ask-User Flow & Orchestrator

## 🎯 Doel v0.2
Implementeren van de kernflow waar Pixie kan terugvragen aan gebruikers voor verduidelijking en een orchestrator kan beslissen tussen verschillende strategieën.

## 📋 Requirements Analysis

### ✅ Al Aanwezig
- [x] Basis AskResponse contract (answer/ask_user/error types)
- [x] ReplyRequest contract
- [x] /ask endpoint die beide flows ondersteunt
- [x] Basis test setup
- [x] Logging infrastructure

### ❌ Nog Te Implementeren
- [ ] FakeTabularRAG component
- [ ] Orchestrator component met beslissingslogica
- [ ] Proper pending_id management met state persistence
- [ ] Error handling voor ongeldige pending_id's
- [ ] E2E test voor complete ask→ask_user→reply→answer flow
- [ ] /reply endpoint (momenteel via /ask gedaan)
- [ ] Updated README met flow voorbeelden

## 🗓️ Planning: 8 Stappen

### Stap 1: FakeTabularRAG Component
**Doel**: Toevoegen van tweede data bron voor orchestrator beslissingen
**Bestanden**: `pixie/core/pixie.py`
**Tijd**: 15 min

- Implementeer `FakeTabularRAG` klasse naast `FakeRAGAdapter`
- Geef verschillende mock responses voor tabular data
- Test basic functionaliteit

### Stap 2: Orchestrator Component
**Doel**: Centrale beslissingslogica die combineert RAG + TabularRAG
**Bestanden**: `pixie/core/pixie.py`
**Tijd**: 30 min

- Implementeer `Orchestrator` klasse
- Beslissingslogica: analyseer vraag → bepaal of genoeg info
- Gebruik beide RAG sources voor rijkere mock responses
- Integreer in `Pixie` klasse

### Stap 3: Pending ID Management
**Doel**: Proper state management voor ask_user flows
**Bestanden**: `pixie/core/pixie.py`, `pixie/core/pending_store.py`
**Tijd**: 20 min

- Integreer `InMemoryPendingStore` in `Pixie` klasse
- Genereer unieke pending_id's (UUID gebaseerd)
- Sla vraag context op bij ask_user response
- Valideer pending_id bij reply

### Stap 4: Error Handling
**Doel**: Proper error responses voor edge cases
**Bestanden**: `pixie/core/pixie.py`
**Tijd**: 15 min

- Error response voor ongeldige pending_id
- Error response voor missing/expired pending state
- Error response voor malformed requests
- Logging van error scenarios

### Stap 5: Dedicated /reply Endpoint
**Doel**: Scheiden van /ask en /reply voor duidelijkere API
**Bestanden**: `apps/api/main.py`
**Tijd**: 20 min

- Nieuwe `/reply` POST endpoint
- Verwijder reply logic uit `/ask` endpoint
- Update routing en validation
- Behoud backward compatibility tests

### Stap 6: Enhanced Testing
**Doel**: Complete E2E test coverage voor v0.2 flow
**Bestanden**: `tests/test_api_routes.py`
**Tijd**: 25 min

- E2E test: vage vraag → ask_user → reply → answer
- Test error scenarios (invalid pending_id)
- Test orchestrator decision making
- Test both RAG sources integration

### Stap 7: Documentation Update
**Doel**: Documenteer nieuwe v0.2 flows met voorbeelden
**Bestanden**: `README.md`
**Tijd**: 20 min

- Update README met v0.2 flow beschrijving
- Voeg curl voorbeelden toe voor beide flows
- Documenteer API endpoints (/ask, /reply)
- Beschrijf orchestrator werking

### Stap 8: Integration Test & Polish
**Doel**: End-to-end validatie en laatste refinements
**Bestanden**: Alle
**Tijd**: 25 min

- Manual testing van complete flows
- Performance check
- Code cleanup en final refactoring
- Git commit met v0.2 completion

## 🎯 Success Criteria (Definition of Done)

- [ ] /ask ondersteunt answer en ask_user responses
- [ ] /reply vervolledigt pending_id flow met vrije tekst → answer
- [ ] Ongeldige pending_id geeft error response
- [ ] E2E test: /ask (vague) → ask_user → /reply → answer
- [ ] README documenteert flows met voorbeelden
- [ ] Alle tests slagen (target: 12+ tests)
- [ ] Clean commit message volgens Conventional Commits

## 📊 Huidige Status
**Start**: Basis infrastructuur klaar, tests slagen (9/9)
**Voortgang**: 0/8 stappen voltooid
**Geschatte tijd**: ~2.5 uur totaal

---

## 🚀 Uitvoering
Deze planning dient als leidraad. Elke stap wordt individueel uitgevoerd met:
1. Implementatie
2. Lokale tests
3. Commit bij voltooiing stap
4. Update van deze planning

**Volgende actie**: Start met Stap 1 - FakeTabularRAG Component
