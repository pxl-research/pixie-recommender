# Conversation Loop Flow Implementation - Onderzoeksrapport

**Datum**: 2025-09-08  
**Project**: pixie-core  
**Taak**: Implementeer conversation loop flow volgens Nederlandse conversatie-eisen  

---

## Executive Summary

Dit onderzoek analyseert de huidige pixie-core architectuur en geeft uitgebreide guidance voor het implementeren van een conversation loop flow. Het doel is een eenvoudige, onderhoudbare mock implementatie die bestaande functionaliteit behoudt en intelligente conversatiemogelijkheden toevoegt.

---

## 1. Huidige Project Analyse

### 1.1 Architectuur Overzicht

Het pixie-core project implementeert een minimale mock van een productontdekkingssysteem met de volgende hoofdcomponenten:

**Kern Classes:**
- `Pixie`: Hoofdorchestrator klasse (`/pixie/core/pixie.py`, 248 regels)
- `AskResponse`: Response contract (`/pixie/core/contracts.py`, 24 regels) 
- `InMemoryPendingStore`: Conversatie state management (`/pixie/core/pending_store.py`, 58 regels)

**API Layer:**
- FastAPI applicatie (`/apps/api/main.py`, 89 regels)
- Enkele `/ask` endpoint die zowel nieuwe vragen als replies afhandelt

**Huidige Response Types:**
- `"answer"`: Eindresultaat met productinformatie
- `"ask_user"`: Verzoek om meer informatie (met `pending_id`)
- `"not_relevant"`: Out-of-scope query
- `"no_results"`: Geen matchende producten gevonden
- `"error"`: Systeemfouten

### 1.2 Bestaande Flow Architectuur

**Huidig Implementatie Patroon:**
```python
# Stage-gebaseerde conversatie flow
context = {
    "flow": "product",           # Flow identifier  
    "stage": "ask_budget"        # Huidige conversatie stage
}

# Lineaire progressie: ask_budget -> ask_brand -> ask_tech -> results
```

**Ondersteunde Flows:**
1. **Product Discovery**: `"Ik zoek een nieuwe printer"` → Multi-turn conversatie
2. **No Results**: `"Brother laserprinter onder €50"` → Direct no_results
3. **Not Relevant**: `"Ik zoek mijn mama"` → Direct not_relevant  
4. **Too Many Results**: `"weet ik niet"` responses → Verfijningsverzoek

### 1.3 Huidige State Management

**PendingEntry Structuur:**
```python
@dataclass
class PendingEntry:
    pending_id: str                              # Unieke conversatie ID
    question: str                                # Originele vraag
    created_at: datetime                         # Sessie timestamp
    ttl_seconds: int = 300                      # 5-minuten expiratie
    conversation_context: Optional[Dict[str, Any]] # Flow state
```

**Context Data:**
- Eenvoudige dictionary-gebaseerde state tracking
- Flow en stage identifiers
- TTL-gebaseerde cleanup (5 minuten)
- In-memory storage (geen persistentie)

### 1.4 Decision Logic Patterns

**Huidige Decision Making:**
- **Literal String Matching**: Exacte Nederlandse zinnen triggeren specifieke flows
- **Stage-Based Routing**: Context bepaalt volgende stap in conversatie
- **Fallback Logic**: Onbekende input → not_relevant response

**Voorbeeld Decision Points:**
```python
# Exacte match triggers
if key == "ik zoek een nieuwe printer":
    # Start product discovery flow
    
if key == "ik zoek mijn mama":
    # Return not_relevant onmiddellijk
    
# Stage-gebaseerde beslissingen  
if stage == "ask_budget" and key == "minder dan 50€":
    # Return no_results (te restrictief)
```

---

## 2. Nederlandse Conversatie Flow Vereisten Analyse

### 2.1 Vereisten uit User Request

Gebaseerd op de user requirements moeten we de volgende 6 stappen implementeren:

**Stap 1: Vraag Analyse**
- Controleer of vraag het woord "printer" of "printers" bevat
- Zo niet → standaardantwoord dat onderwerp niet relevant is
- Moet in toekomst een LLM-afgeleide klasse worden

**Stap 2: SQL Query Generatie** 
- Als vraag relevant is → herformuleer naar SQL query
- "Ik zoek een nieuwe printer" wordt `SELECT * FROM printers;`
- Toekomstig: echte LLM, nu mock met >5 rijen default

**Stap 3: Resultaat Analyse**
- 0 rijen: standaardantwoord geen resultaten
- 1-5 rijen: ga naar antwoord formulatie (LLM3)
- >5 rijen: ga naar verfijningsstap

**Stap 4: Maximum Bijvragen Check**
- Configureerbaar maximum (voorlopig 3 bijvragen)
- Als bereikt: geef subset terug (hardcoded)
- Anders: ga naar attribuut selectie

**Stap 5: Attribuut Selectie**
- Volgorde: budget, merk, printtechnologie
- Stel specifieke vragen zoals voorgetoond in voorbeelden
- Mock implementatie met hardcoded vragen

**Stap 6: Antwoord Validatie**
- Controleer of antwoord "Weet ik niet" is
- Zo ja: niet toevoegen aan query, try volgende attribuut
- Anders: verwerk attribuut en herhaal vanaf stap 2

### 2.2 Conversatie Voorbeelden

**Voorbeeld 1: Succesvol Pad**
```
Q: Ik zoek een nieuwe printer
A: Wat is uw budget voor een printer? Minder dan 150€, tussen 150€ en 300€, meer dan 300€ of maakt het niet uit?
Q: Maximaal 200€
A: Welk merk van printer had u in gedachte? U kan kiezen uit Brother, Benq, HP, Kyocera, ... of weet u het nog niet?
Q: Brother
A: Welke printtechnologie had u in gedachte? U kan kiezen uit inkjet, laser, thermal inkjet of weet u het nog niet?
Q: laser
A: Ik heb volgende printers voor u gevonden
1. Brother XC 2570 - Prijs: 199€ - Beschrijving: ....
2. Brother XT 3560 - Prijs: 159€ - Beschrijving: ...
```

**Voorbeeld 2: "Weet ik niet" Pad**
```
Q: Ik zoek een nieuwe printer
A: Wat is uw budget voor een printer? [budget vraag]
Q: Weet ik niet
A: Welk merk van printer had u in gedachte? [merk vraag]  
Q: Weet ik niet
A: Welke printtechnologie had u in gedachte? [tech vraag]
Q: Weet ik niet
A: Ik heb 152 verschillende printers gevonden. Wilt u graag de top 5 zien gesorteerd op prijs of dat ik er 5 willekeurig selecteer?
```

---

## 3. Technische Implementatie Specificaties

### 3.1 Vereiste Nieuwe Classes

**MockLLM (afgeleide van abstracte LLM)**
```python
from abc import ABC, abstractmethod

class LLM(ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name

class MockLLM(LLM):
    def __init__(self):
        super().__init__("mock-llm-v1")
    
    def is_relevant(self, question: str) -> bool:
        return "printer" in question.lower() or "printers" in question.lower()
    
    def generate_sql(self, question: str, context: dict) -> str:
        # Basisimplementatie: altijd SELECT * FROM printers
        return "SELECT * FROM printers;"
    
    def generate_refinement_question(self, context: dict) -> str:
        # Gebaseerd op collected_attributes, return volgende vraag
        pass
```

**ConversationLoopManager**
```python
class ConversationLoopManager:
    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self.llm = MockLLM()
        
    def handle_conversation_loop(self, question: str, context: dict) -> AskResponse:
        # Implementeer 6-stappen flow
        pass
```

**MockSearchEngine**
```python
class MockSearchEngine:
    def search(self, sql: str) -> list:
        # Return configureerbare aantallen resultaten
        # Voor testing: 0, 1-5, >5 scenarios
        pass
```

### 3.2 Wijzigingen aan Pixie Class

**Nieuwe Methods in Pixie:**
```python
def _handle_conversation_loop(self, question: str) -> AskResponse:
    """Route nieuwe vragen naar conversation loop manager"""
    
def _handle_conversation_loop_reply(self, pending_id: str, reply: str) -> AskResponse:
    """Handle replies binnen conversation loop context"""
```

**Modified answer() method:**
```python
def answer(self, question: str) -> AskResponse:
    # Behoud bestaande literal triggers
    if key in EXISTING_LITERALS:
        return self._handle_existing_flow(key)
    
    # Route andere vragen naar conversation loop
    return self._handle_conversation_loop(question)
```

### 3.3 Enhanced Context Structure

**Uitgebreide Conversation Context:**
```python
conversation_context = {
    "flow": "conversation_loop",
    "original_question": str,
    "collected_attributes": {
        "budget": "maximaal 200€",
        "brand": "brother", 
        "technology": "laser"
    },
    "iteration_count": int,
    "last_result_count": int,
    "current_attribute": str  # budget/brand/technology
}
```

---

## 4. Mock Data Strategy

### 4.1 Mock Product Database

**Data Structure:**
```python
MOCK_PRODUCTS = [
    {
        "id": 1,
        "name": "Brother XC 2570",
        "brand": "Brother",
        "type": "laser", 
        "price": 199,
        "description": "Compacte laserprinter..."
    },
    {
        "id": 2,
        "name": "Brother XT 3560", 
        "brand": "Brother",
        "type": "laser",
        "price": 159,
        "description": "Efficiënte laserprinter..."
    },
    # Meer producten voor verschillende scenario's
]
```

**Search Logic Rules:**
- Budget "minder dan 50€" → return []
- Brand + budget combinaties → return 1-5 resultaten  
- Geen attributen → return >5 resultaten (152 items)
- Configureerbaar per test scenario

### 4.2 LLM Decision Rules

**Relevance Rules:**
```python
def is_relevant(question: str) -> bool:
    keywords = ["printer", "printers"]
    return any(kw in question.lower() for kw in keywords)
```

**Attribute Extraction:**
```python
def extract_attributes(reply: str) -> dict:
    reply_lower = reply.lower()
    attributes = {}
    
    # Budget detection
    if "maximaal" in reply_lower or "minder dan" in reply_lower:
        attributes["budget"] = reply
    
    # Brand detection  
    brands = ["brother", "hp", "canon", "kyocera", "benq"]
    for brand in brands:
        if brand in reply_lower:
            attributes["brand"] = brand
            break
    
    # Technology detection
    techs = ["laser", "inkjet", "thermal"]
    for tech in techs:
        if tech in reply_lower:
            attributes["technology"] = tech
            break
            
    return attributes
```

---

## 5. Implementatie Plan

### 5.1 Fase 1: Core Infrastructure

**Taken:**
1. Creëer abstracte LLM base class in `pixie/core/abstractclasses/llm.py`
2. Implementeer MockLLM class in `pixie/core/mock_llm.py`
3. Creëer ConversationLoopManager in `pixie/core/conversation_loop.py`
4. Implementeer MockSearchEngine met configureerbare resultaten

**Testing:**
- Unit tests voor elke nieuwe component
- Mock verschillende resultaat count scenarios  
- Valideer loop terminatie condities

### 5.2 Fase 2: Pixie Integration

**Taken:**
1. Wijzig `Pixie.answer()` om conversation loop te routen
2. Integreer conversation loop met bestaande pending store
3. Voeg conversation loop handling toe aan `Pixie.reply()`
4. Behoud alle bestaande literal triggers

**Testing:**
- Zorg dat bestaande tests blijven slagen (geen regressies)
- Voeg tests toe voor conversation loop scenarios
- Test gemengd gebruik (bestaande + nieuwe flows)

### 5.3 Fase 3: Edge Cases & Polish

**Taken:**  
1. Handle max iteratie limieten
2. Voeg uitgebreide error handling toe
3. Fine-tune mock response kwaliteit
4. Voeg logging toe voor conversation flow debugging

**Testing:**
- Integratie tests voor complete conversation loops
- Edge case testing (max iteraties, geen resultaten, etc.)
- Performance testing voor mock componenten

---

## 6. Backward Compatibility Strategy

### 6.1 Bestaande Functionaliteit Behouden

**Kritieke Vereiste:**
- Alle bestaande literal triggers moeten identiek blijven werken
- Bestaande tests mogen niet aangepast worden
- Geen performance regressie voor bestaande flows

**Integration Approach:**
```python
def answer(self, question: str) -> AskResponse:
    # Check bestaande literal triggers eerst  
    if question.lower() in EXISTING_TRIGGERS:
        return self._handle_existing_flow(question)
    
    # Nieuw: Route naar conversation loop voor andere vragen
    return self._handle_conversation_loop(question)
```

### 6.2 Enhanced Flow Coexistence

**Flow Routing:**
1. **Exact Match Flows**: Bestaande literal triggers (onveranderd)
2. **Conversation Loop**: Nieuwe intelligente flow voor andere vragen
3. **Fallback**: not_relevant voor echt out-of-scope queries

---

## 7. Testing Strategy  

### 7.1 Bestaande Tests Behouden

**Kritieke Vereiste:**
- Alle bestaande test cases moeten slagen zonder wijziging
- Bestaande flows moeten identiek gedragen  
- Geen performance regressie

### 7.2 Nieuwe Test Coverage

**Conversation Loop Tests:**
```python
def test_conversation_loop_basic():
    # Test: Vraag → Query → Weinig resultaten → Eindantwoord
    
def test_conversation_loop_refinement():  
    # Test: Vraag → Query → Veel resultaten → Verfijn → Eindantwoord
    
def test_conversation_loop_max_iterations():
    # Test: Meerdere verfijningen → Max limiet → Return subset
    
def test_conversation_loop_not_relevant():
    # Test: Out-of-scope vraag → not_relevant response
    
def test_weet_ik_niet_handling():
    # Test: "Weet ik niet" antwoorden → skip attribuut, ga verder
```

---

## 8. Success Criteria

### 8.1 Functionele Vereisten

✅ **Behoud Bestaande Functionaliteit**: Alle 4 bestaande flows werken onveranderd  
✅ **Implementeer Conversation Loop**: Nieuwe intelligente conversatie flow  
✅ **Eenvoudige Implementatie**: Vermijd complexiteit van referentie voorbeelden  
✅ **Mock-Gebaseerd**: Geen externe dependencies, volledig mockbaar  
✅ **Onderhoudbare Code**: Duidelijke, eenvoudige, goed gedocumenteerde implementatie

### 8.2 Technische Vereisten  

✅ **Backward Compatibility**: Bestaande API onveranderd  
✅ **Test Coverage**: Alle bestaande tests slagen, nieuwe tests toegevoegd  
✅ **Performance**: Geen degradatie voor bestaande flows  
✅ **Memory Usage**: Efficiënt in-memory state management  
✅ **Error Handling**: Graceful handling van edge cases

---

## 9. Risico's en Mitigatie

### 9.1 Belangrijkste Risico's

**Regressie Risico:** Bestaande functionaliteit kapot maken
- **Mitigatie:** Uitgebreide testing van bestaande flows

**Complexiteit Risico:** Over-engineering van mock implementatie  
- **Mitigatie:** Houd implementatie eenvoudig, vermijd over-abstraction

**Performance Risico:** Langzamere response times
- **Mitigatie:** Profile mock componenten, optimaliseer indien nodig

**Integratie Risico:** Problemen met bestaande pending store  
- **Mitigatie:** Incrementele implementatie met continue testing

---

## Conclusie

Het pixie-core project heeft een solide basis voor het implementeren van de conversation loop flow. De bestaande architectuur ondersteunt de vereiste state management en flow control. De belangrijkste succesfactoren zijn:

1. **Behoud bestaande functionaliteit volledig**
2. **Houd de implementatie eenvoudig en onderhoudbaar**
3. **Gebruik effectieve mock strategieën om LLM beslissingen te simuleren**  
4. **Handhaaf backward compatibility terwijl nieuwe mogelijkheden worden toegevoegd**

De conversation loop kan worden geïmplementeerd als een verbetering die naast bestaande flows bestaat, wat een pad biedt voor geleidelijke migratie naar meer geavanceerde conversatie handling terwijl de betrouwbaarheid van het huidige systeem behouden blijft.

---

**Onderzoek Voltooid**: 2025-09-08  
**Volgende Stap**: Creëer implementatie plan gebaseerd op dit onderzoek  
**Geschatte Implementatie Tijd**: 2-3 dagen voor complete implementatie met testing
