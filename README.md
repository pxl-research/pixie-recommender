# pixie-core

Simplified, API-first rebuild of Pixie with a mock-first approach

## Features

### v0.2 Ask-User Flow with Unified API

The system intelligently handles questions through a single `/ask` endpoint that:

- **Auto-detects Request Type**: New question vs. reply to pending question based on request structure
- **FakeRAGAdapter**: Quick semantic retrieval
- **FakeTabularRAG**: Structured data analysis  
- **Confidence Scoring**: Smart decision-making when to ask users for clarification
- **Seamless UX**: No endpoint complexity for clients - one endpoint for all interactions

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

#### Unified /ask Endpoint

The system uses a single, intelligent `/ask` endpoint that automatically detects whether you're asking a new question or replying to a pending question.

**New Question:**

```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the capital of France?"}'
```

**Reply to Pending Question:**

```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "pending_id": "123e4567-e89b-12d3-a456-426614174000",
       "message": "I meant the historical significance"
     }'
```

**Response Examples:**

Confident answer:

```json
{
  "type": "answer",
  "text": "The capital of France is Paris."
}
```

Needs clarification:

```json
{
  "type": "ask_user",
  "prompt": "Could you clarify your question about complex topics?",
  "pending_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

After clarification:

```json
{
  "type": "answer", 
  "text": "Based on your clarification: The historical significance includes..."
}
```

## Architecture

### Core Components

- **`apps/api/main.py`**: FastAPI application with unified `/ask` endpoint for both new questions and replies
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
