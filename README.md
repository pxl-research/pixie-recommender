# pixie-core

Simplified, API-first rebuild of Pixie with a mock-first approach

## Features

### v0.2 Ask-User Flow with Orchestrator

The system intelligently handles questions through an orchestrator that combines:

- **FakeRAGAdapter**: Quick semantic retrieval
- **FakeTabularRAG**: Structured data analysis
- **Confidence Scoring**: Smart decision-making when to ask users for clarification

## Quick Start

### Development Setup

```bash
# Install dependencies
uv install

# Run development server
uv run uvicorn apps.api.main:app --reload

# Run tests
uv run python -m pytest tests/ -v
```

### API Usage

#### 1. Ask a Question (v0.2 Flow)

```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the capital of France?"}'
```

Response when confident:

```json
{
  "answer": "The capital of France is Paris.",
  "confidence": 0.95,
  "sources": ["mock_source_1"],
  "pending_id": null
}
```

Response when needs clarification:

```json
{
  "answer": "I need more information. Could you clarify your question about complex topics?",
  "confidence": 0.3,
  "sources": ["mock_source_1"],
  "pending_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### 2. Reply to Clarification Request

```bash
curl -X POST "http://localhost:8000/reply" \
     -H "Content-Type: application/json" \
     -d '{
       "pending_id": "123e4567-e89b-12d3-a456-426614174000",
       "user_response": "I meant the historical significance"
     }'
```

Response:

```json
{
  "answer": "Based on your clarification: The historical significance includes...",
  "confidence": 0.85,
  "sources": ["mock_source_1", "mock_source_2"]
}
```

## Architecture

### Core Components

- **`apps/api/main.py`**: FastAPI application with `/ask` and `/reply` endpoints
- **`pixie/core/pixie.py`**: Orchestrator combining RAG adapters with confidence scoring
- **`pixie/core/pending_store.py`**: UUID-based state management for multi-turn conversations
- **`pixie/core/contracts.py`**: Pydantic models for request/response validation

### Testing

Comprehensive test suite with 17+ test cases covering:

- E2E ask→ask_user→reply→answer flows
- Orchestrator decision scenarios
- Error handling and validation
- API metadata and structure

```bash
uv run python -m pytest tests/ -v
```
