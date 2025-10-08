# Query API Gebruikshandleiding

## Endpoint
```
POST /collections/{collection_name}/products/{product_name}/query
```

## Headers
```
X-API-Key: <your-api-key>
```

## URL Parameters
- `collection_name`: Naam van de collectie
- `product_name`: Naam van het product binnen de collectie

## Request Body

### Basis structuur
```json
{
  "filters": [],
  "limit": 100,
  "offset": 0
}
```

### Parameters
- **filters**: Array van filter objecten (zie hieronder)
- **limit**: Aantal resultaten per pagina (1-1000, standaard 100)
- **offset**: Aantal resultaten om over te slaan (standaard 0)

---

## Filter Types

### 1. Exact Filter
Voor exacte waarde matching (tekst, nummers, booleans)

```json
{
  "name": "attribute_naam",
  "type": "exact",
  "value": "waarde"
}
```

**Voorbeelden:**
```json
// Tekst filter
{
  "name": "color",
  "type": "exact",
  "value": "blue"
}

// Numeriek filter
{
  "name": "price",
  "type": "exact",
  "value": 29.99
}

// Boolean filter
{
  "name": "in_stock",
  "type": "exact",
  "value": true
}
```

### 2. Range Filter
Voor numerieke bereik filtering (alleen voor NUMERIC attributes)

```json
{
  "name": "attribute_naam",
  "type": "range",
  "min_value": 10.0,
  "max_value": 100.0
}
```

**Opties:**
- Alleen `min_value`: >= waarde
- Alleen `max_value`: <= waarde
- Beide: tussen min en max (inclusief)

**Voorbeelden:**
```json
// Prijs tussen 10 en 50
{
  "name": "price",
  "type": "range",
  "min_value": 10.0,
  "max_value": 50.0
}

// Minimaal 100 stuks
{
  "name": "quantity",
  "type": "range",
  "min_value": 100
}

// Maximaal 25 jaar oud
{
  "name": "age",
  "type": "range",
  "max_value": 25
}
```

---

## Complete Request Voorbeelden

### Voorbeeld 1: Geen filters (alles ophalen)
```bash
curl -X POST "http://localhost:8000/collections/printers/products/HP_LaserJet/query" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": [],
    "limit": 50,
    "offset": 0
  }'
```

### Voorbeeld 2: Exact filter
```bash
curl -X POST "http://localhost:8000/collections/printers/products/Canon_Pixma/query" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": [
      {
        "name": "color",
        "type": "exact",
        "value": "black"
      }
    ],
    "limit": 100,
    "offset": 0
  }'
```

### Voorbeeld 3: Range filter
```bash
curl -X POST "http://localhost:8000/collections/products/products/Electronics/query" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": [
      {
        "name": "price",
        "type": "range",
        "min_value": 100.0,
        "max_value": 500.0
      }
    ],
    "limit": 100,
    "offset": 0
  }'
```

### Voorbeeld 4: Meerdere filters combineren
```bash
curl -X POST "http://localhost:8000/collections/inventory/products/Laptops/query" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": [
      {
        "name": "brand",
        "type": "exact",
        "value": "Dell"
      },
      {
        "name": "price",
        "type": "range",
        "min_value": 500.0,
        "max_value": 1500.0
      },
      {
        "name": "in_stock",
        "type": "exact",
        "value": true
      }
    ],
    "limit": 50,
    "offset": 0
  }'
```

### Voorbeeld 5: Paginatie
```bash
# Pagina 1 (eerste 20 resultaten)
curl -X POST "http://localhost:8000/collections/printers/products/HP_LaserJet/query" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": [],
    "limit": 20,
    "offset": 0
  }'

# Pagina 2 (resultaten 21-40)
curl -X POST "http://localhost:8000/collections/printers/products/HP_LaserJet/query" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": [],
    "limit": 20,
    "offset": 20
  }'
```

---

## Response Format

```json
{
  "product_name": "HP_LaserJet",
  "results": [
    {
      "attribute1": "waarde1",
      "attribute2": "waarde2",
      "price": 299.99
    },
    {
      "attribute1": "waarde3",
      "attribute2": "waarde4",
      "price": 349.99
    }
  ],
  "count": 2,
  "total": 45,
  "limit": 100,
  "offset": 0
}
```

**Response velden:**
- `product_name`: Naam van het opgevraagde product
- `results`: Array van rij objecten (elke rij is een object met alle attributes)
- `count`: Aantal resultaten in deze response
- `total`: Totaal aantal resultaten dat aan de filters voldoet
- `limit`: Gebruikte limit
- `offset`: Gebruikte offset

---

## Belangrijke Opmerkingen

1. **Filter types per datatype:**
   - TEXT: alleen `exact` filters
   - NUMERIC: `exact` en `range` filters
   - BOOLEAN: alleen `exact` filters

2. **Range filters** werken alleen op numerieke attributes. Als je een range filter probeert op een tekst veld krijg je een 400 error.

3. **Alle filters worden gecombineerd met AND** - een rij moet aan alle filters voldoen om in de resultaten te komen.

4. **Attribute namen** moeten exact overeenkomen met de kolom namen in je document.

5. **Paginatie:** gebruik `limit` en `offset` om door grote resultatensets te bladeren. Gebruik het `total` veld om te bepalen hoeveel pagina's er zijn.

---

## Error Responses

### 400 Bad Request
- Lege attribute naam
- Onbekende attribute voor het document
- Range filter op niet-numeriek veld
- Ongeldige numerieke of boolean waarde

### 404 Not Found
- Collectie niet gevonden
- Product niet gevonden in collectie

### 401 Unauthorized
- Ontbrekende of ongeldige API key

---

## Python Voorbeeld

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key"

def query_products(collection: str, product: str, filters: list, limit: int = 100, offset: int = 0):
    url = f"{API_URL}/collections/{collection}/products/{product}/query"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "filters": filters,
        "limit": limit,
        "offset": offset
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

# Voorbeeld: prijs range en exact filter
filters = [
    {
        "name": "price",
        "type": "range",
        "min_value": 100.0,
        "max_value": 500.0
    },
    {
        "name": "brand",
        "type": "exact",
        "value": "Dell"
    }
]

result = query_products("inventory", "Laptops", filters, limit=50)
print(f"Gevonden {result['total']} resultaten")
for item in result['results']:
    print(item)
```

---

## JavaScript/TypeScript Voorbeeld

```typescript
interface QueryFilter {
  name: string;
  type: 'exact' | 'range';
  value?: string | number | boolean;
  min_value?: number;
  max_value?: number;
}

interface QueryRequest {
  filters: QueryFilter[];
  limit?: number;
  offset?: number;
}

interface QueryResponse {
  product_name: string;
  results: Record<string, any>[];
  count: number;
  total: number;
  limit: number;
  offset: number;
}

const API_URL = "http://localhost:8000";
const API_KEY = "your-api-key";

async function queryProducts(
  collection: string,
  product: string,
  request: QueryRequest
): Promise<QueryResponse> {
  const url = `${API_URL}/collections/${collection}/products/${product}/query`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });
  
  if (!response.ok) {
    throw new Error(`Query failed: ${response.statusText}`);
  }
  
  return response.json();
}

// Voorbeeld gebruik
const filters: QueryFilter[] = [
  {
    name: "price",
    type: "range",
    min_value: 100.0,
    max_value: 500.0
  },
  {
    name: "in_stock",
    type: "exact",
    value: true
  }
];

const result = await queryProducts("inventory", "Laptops", {
  filters,
  limit: 50,
  offset: 0
});

console.log(`Gevonden ${result.total} resultaten`);
result.results.forEach(item => console.log(item));
```
