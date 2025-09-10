# PiXie Agent - Copilot Instructions

## CONTAINER-FIRST ONTWIKKELING — Nooit lokaal testen

**BELANGRIJK:** Deze repository werkt uitsluitend container-first. Alle ontwikkel-activiteiten (testen, linting, formattering) gebeuren binnen de dev-container.

### Waarom container-first?
- **Geen lokale Python-problemen:** Voorkomt "bad interpreter", shebang-fouten, en dependency-conflicts
- **Identieke omgeving:** Iedereen gebruikt exact dezelfde Python-versie, venv, en tooling als CI
- **Eenvoudige onboarding:** Geen lokale setup vereist, direct productief

### Wat NIET te doen:
- ❌ `pytest` lokaal uitvoeren
- ❌ `ruff` of `black` lokaal installeren/draaien  
- ❌ Python packages lokaal installeren
- ❌ Lokale venv aanmaken

### Wat WEL te doen:
- ✅ Alle commands via `docker compose -f docker-compose.dev.yml`
- ✅ Tests uitvoeren in de `api` service
- ✅ Helper scripts gebruiken (`./scripts/dev_test.sh`)

---
````instructions
## Tests
## Run & test (CONTAINER-FIRST — nooit lokaal)
BELANGRIJK: werk altijd container-first. Deze repository ondersteunt expliciet een hermetische dev-container die de juiste Python-versie, dependencies en tooling bevat. Draai tests en debug-commands alleen binnen de `api` dev-service. Lokale runs (bijv. `pytest` op uw machine) zijn niet ondersteund en leiden vaak tot shebang/interpreter mismatches of ontbrekende dev-deps.

Waarom container-first?
- Voorkomt "bad interpreter" / shebang fouten wanneer contributors verschillende Python-installaties hebben.
- Zorgt dat iedereen exact dezelfde venv, PATH en dev-extras gebruikt (mirror CI).
- Vereenvoudigt onboarding en troubleshooting: één, betrouwbare manier om tests te draaien.

Als je dit document leest: stop vóórdat je `pytest` lokaal uitvoert — volg de container-commando's hieronder.

## Run & test (Docker-first)
Deze repo wordt ontwikkeld en getest in een ontwikkelcontainer. Gebruik altijd de dev Dockerfile / compose flow
om de applicatie te proberen en om pytest binnen de container te draaien — dat voorkomt lokale interpreter- of dependency-mismatch.
## App snel uitproberen

1. **Build en start de dev container:**
```bash
docker compose -f docker-compose.dev.yml up --build -d
```

2. **Controleer de health endpoint:**
```bash
curl -fsS http://localhost:8000/health
```

3. **Stuur een voorbeeldvraag:**
```bash
curl -s -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Ik zoek een nieuwe printer"}' | jq
```

4. **Stop en ruim op:**
```bash
docker compose -f docker-compose.dev.yml down -v
```

## Tests uitvoeren (container-only)

### Alle tests uitvoeren
```bash
docker compose -f docker-compose.dev.yml up --build -d
docker compose -f docker-compose.dev.yml exec api /bin/bash -lc "uv run python -m pytest -q"
docker compose -f docker-compose.dev.yml down -v
```

### Specifieke test uitvoeren
```bash
docker compose -f docker-compose.dev.yml up --build -d
docker compose -f docker-compose.dev.yml exec api /bin/bash -lc "uv run python -m pytest tests/test_logging.py::test_some_case -v"
docker compose -f docker-compose.dev.yml down -v
```

### Helper scripts gebruiken (aanbevolen)
```bash
# Pytest via helper script
./scripts/dev_test.sh pytest

# Of via Makefile
make dev-test
```
## Code quality & linting (container-only)

### Formatteren met Black
```bash
docker compose -f docker-compose.dev.yml exec api /bin/bash -lc "uv run black ."
```

### Linting met Ruff  
```bash
docker compose -f docker-compose.dev.yml exec api /bin/bash -lc "uv run ruff check ."
```

### All-in-one quality check
```bash
docker compose -f docker-compose.dev.yml exec api /bin/bash -lc "uv run ruff check . && uv run black --check ."
```

## Troubleshooting

### Pytest ontbreekt in container
Als `pytest` niet beschikbaar is:

```bash
# Controleer dev dependencies
docker compose -f docker-compose.dev.yml exec api /bin/bash -lc "python -m pip list | grep pytest"

# Forceer rebuild met dev dependencies
docker compose -f docker-compose.dev.yml build --no-cache api
```

### Container issues
```bash
# Volledige cleanup en rebuild
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up --build -d
```

## Helper scripts

Het project bevat helper scripts voor veelgebruikte workflows:

```bash
# Pytest uitvoeren  
./scripts/dev_test.sh pytest

# Makefile shortcuts
make dev-test        # pytest
make up              # start containers
make down            # stop en cleanup
```
---

# PiXie Agent - Project Overview

## Over het project

PiXie is een AI-gestuurde conversational shopping assistant die klanten helpt producten te vinden via natuurlijke taalinteractie. Het systeem gebruikt intern toegankelijke bedrijfsinformatie om complexe productvragen te begrijpen, analyseren en relevante aanbevelingen te genereren.

## Core concept

Het systeem werkt als een digitale verkoopmedewerker die:

- **Klantvragen begrijpt** in natuurlijke taal, ongeacht hoe complex of vaag ze geformuleerd zijn
- **Intelligente vervolgvragen stelt** om productspecificaties te verfijnen  
- **Productcatalogi doorzoekt** met zowel gestructureerde data als ongestructureerde documentatie
- **Gepersonaliseerde aanbevelingen geeft** met uitleg en bronverwijzingen

## Technische architectuur

Het systeem faciliteert **natuurlijke productontdekking** door klanten te begeleiden van vage intenties naar specifieke productmatches. Het beheert **complexe gesprekken** die zich ontwikkelen over meerdere interacties, waarbij context en voorkeuren behouden blijven.

De architectuur ondersteunt **multi-source informatie-ophaling**, waardoor zowel gestructureerde productdata als ongestructureerde documentatie doorzoekbaar worden voor nauwkeurige en volledige antwoorden.

## Bedrijfswaarde

PiXie automatiseert het productadviesproces door menselijke gesprekken te voeren terwijl het tegelijkertijd toegang heeft tot complete productcatalogi en documentatie. Dit resulteert in betere klantervaring en verhoogde conversie zonder de overhead van menselijke klantenservice.

## Core flows

Pixie ondersteunt verschillende gesprekspatronen. Hieronder enkele voorbeeldflows:

### 1. Product gevonden
Een vage productaanvraag wordt geleidelijk verfijnd door vervolgvragen totdat een concrete productlijst kan worden geretourneerd.

**Voorbeeld:**
- **V:** Ik zoek een nieuwe printer  
- **A:** Wat is uw budget? Minder dan €150, tussen €150-€300, meer dan €300, of maakt niet uit?  
- **V:** Maximaal €200  
- **A:** Welk merk heeft uw voorkeur? Brother, BenQ, HP, Kyocera, … of maakt niet uit?  
- **V:** Brother  
- **A:** Welke printtechnologie? Inkjet, laser, thermal inkjet, of maakt niet uit?  
- **V:** Laser  
- **A:** Hier zijn matchende printers:  
  1. Brother XC 2570 – €199 – korte beschrijving  
  2. Brother XT 3560 – €159 – korte beschrijving  

### 2. Niet relevant
Wanneer de vraag buiten ondersteunde domeinen valt, geeft Pixie een duidelijke vroege exit.

**Voorbeeld:**
- **V:** Ik zoek mijn mama  
- **A:** Sorry, daar kan ik niet bij helpen. Ik heb alleen informatie over printers, laptops, smartphones, …

### 3. Geen resultaten
Geldige filters worden toegepast maar de query levert nul matches op. Pixie reageert netjes en stelt alternatieven voor.

**Voorbeeld:**
- **V:** Ik wil een Brother laserprinter onder €50  
- **A:** Helaas geen printers die voldoen aan uw criteria. Probeer opnieuw met ruimere criteria of neem contact op voor hulp.

### 4. Te veel resultaten
Wanneer de query meer dan N resultaten oplevert, biedt Pixie verfijningsstrategieën of een hanteerbare subset.

**Voorbeeld:**
- **V:** Ik zoek een nieuwe printer  
- **A:** Wat is uw budget?  
- **V:** Maakt niet uit  
- **A:** Welk merk?  
- **V:** Maakt niet uit  
- **A:** Welke printtechnologie?  
- **V:** Maakt niet uit  
- **A:** Ik vond 152 printers. Wilt u de top 5 op prijs, of een willekeurige selectie van 5?  
- **V:** Op prijs gesorteerd  
- **A:** Hier zijn de top 5 printers:  
  1. Brother ZX 1570 – €69 – korte beschrijving  
  2. HP Inkjet 234 – €79 – korte beschrijving  
  3. Kyocera T70 – €99 – korte beschrijving  
  4. Brother XT 3560 – €99 – korte beschrijving  
  5. HP Inkjet 1234 – €109 – korte beschrijving

## Visie en lange termijn doelen

Pixie is ontworpen om te evolueren naar een modulair en uitbreidbaar systeem dat kan integreren met verschillende databronnen en reasoning engines. In de huidige versie zijn adapters gemockt, maar het lange termijn doel is om ze te verbinden als onafhankelijke services via het Model Context Protocol (MCP).

De assistent moet uiteindelijk kunnen:
- Naadloos informatie combineren van meerdere adapters zoals RAG, TabularRAG, en toekomstige gespecialiseerde modules
- Betrouwbaar beslissen wanneer meer informatie nodig is en natuurlijke vervolgvragen formuleren
- Transparante antwoorden geven met traceerbare oorsprong
- Functioneren als plug-and-play component dat in verschillende user interfaces kan worden ingebed

## Ontwikkelingsbenadering

Pixie wordt bewust gebouwd in incrementele mijlpalen.  
We starten met een volledig gemockt prototype om flows en contracten te valideren, en vervangen geleidelijk gemockte componenten door echte adapters en services.  
Deze stap-voor-stap benadering zorgt ervoor dat het systeem testbaar, begrijpelijk en stabiel blijft terwijl functionaliteit en realisme gestaag toenemen.
