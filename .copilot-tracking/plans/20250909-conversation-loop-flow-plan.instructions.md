---
applyTo: '.copilot-tracking/changes/20250909-conversation-loop-flow-changes.md'
---
<!-- markdownlint-disable-file -->
# Todo: Conversation Loop — remaining work

Dit bestand bevat alleen de concrete, nog openstaande taken zodat een nieuwe agent direct kan beginnen.

Doel: zorg dat de conversation-loop feature volledig getest en deterministisch is door
- een concrete MockSearchEngine toe te voegen
- ontbrekende tests voor edge-cases toe te voegen

Checklist (uit te voeren)

- [ ] Implementatie: `pixie/core/mock_search.py`
  - Maak een `MockSearchEngine` met de API: `search(sql: str, attributes: dict | None) -> list[dict]`.
  - Gedrag (deterministisch):
    - Als `attributes` bevat `budget` gelijk aan "minder dan 50€" (case-insensitive) → retourneer []
    - Als `attributes` is None of leeg → retourneer een lijst met >5 mock items (bijv. 152 items)
    - Als `attributes` gedeeltelijk aanwezig zijn (bijv. budget of brand of technology) → retourneer 1–5 mock items
  - Plaats het bestand op `pixie/core/mock_search.py` en exporteer een eenvoudige factory of klasse.

- [ ] Tests: uitbreidingen voor conversation-loop
  - `tests/test_conversation_loop.py` uitbreiden met:
    - [ ] `test_max_iterations_reached` — simuleer dat search steeds [] teruggeeft en controleer dat bij overschrijding van `max_iterations` de manager `no_results` of de verwachte eindstatus teruggeeft.
    - [ ] `test_choose_result_view_large_results` — gebruik `MockSearchEngine` die `attributes` None -> 152 resultaten retourneert; controleer dat manager het `choose_result_view` pad volgt en dat de `choose_result_view` prompts leiden naar verwachte `answer`-responses wanneer gebruiker kiest `gesorteerd op prijs` of `willekeurig`.
    - [ ] `test_ttl_integration` — valideer dat een pending entry met korte TTL vervalt en dat replies na verval een `error` of `invalid_pending_id` teruggeven (integreer `InMemoryPendingStore`).

- [ ] Wiring / usage notes for agent
  - Gebruik de bestaande `ConversationLoopManager` constructor signature (`relevance_model, sql_model, refinement_model, search_fn, pending_store=None, max_iterations=3`). Injecteer `MockSearchEngine().search` als `search_fn` in tests.
  - Houd implementaties klein en deterministic; prefer gebruik van plain Python lists/dicts, geen netwerk of externe dependencies.

Acceptatiecriteria

- `pixie/core/mock_search.py` aanwezig en importeerbaar
- Nieuwe tests toegevoegd en lokaal uitvoerbaar met `pytest` (fast, geen externe services)
- Bestaande tests blijven slagen

Notes

- Alle overige taken uit de originele planning zijn al geïmplementeerd (mock LLMs, `ConversationLoopManager`, Pixie integratie). Dit bestand bevat alleen wat nog openstaat.
- Als je wilt dat ik deze taken direct uitvoer, geef kort akkoord en ik implementeer `mock_search.py` + tests en run `pytest`.
