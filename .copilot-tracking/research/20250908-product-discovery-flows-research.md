<!-- markdownlint-disable-file -->
# Research: Product Discovery Flows Implementation

**Date**: 2025-09-08
**Task**: Implement mocked product discovery flows for Pixie Core

## Current Architecture Analysis

### Existing Components (Lines 1-195: pixie/core/pixie.py)

**Core Classes**:
- `FakeRAGAdapter` (Lines 8-13) - Mock text-based responses
- `FakeTabularRAG` (Lines 16-35) - Mock structured data responses  
- `Orchestrator` (Lines 38-100) - LLM decision simulation
- `Pixie` (Lines 103-195) - Main service orchestrator

**Current Flow Types**:
- `answer` - Direct text responses
- `ask_user` - Follow-up question flow with pending_id
- `answer_with_data` - Combined text + tabular data responses
- `error` - Error handling

### Response Contract Structure (Lines 1-50: pixie/core/contracts.py)

**AskResponse Model**:
- `type`: Discriminator field ("answer", "ask_user", "error")
- `text`: Response content (required for "answer")
- `prompt`: Follow-up question (required for "ask_user") 
- `pending_id`: Conversation continuation token (required for "ask_user")
- `needed_info`: Optional list of required information types
- `reason`: Error explanation (required for "error")

### API Implementation (Lines 1-122: apps/api/main.py)

**Endpoints**:
- `/health` - Health check
- `/ask` - Unified endpoint for questions and replies
  - New questions: `{"question": "..."}`
  - Reply flow: `{"pending_id": "...", "message": "..."}`

## Required Core Flows from Instructions

### Flow 1: Product Found (Lines 26-35: copilot-instructions.md)
**Pattern**: Vague request → Follow-up questions → Product list
**Example**: "I'm looking for a new printer" → Budget? → Brand? → Technology? → Results

**Requirements**:
- Progressive refinement through follow-up questions
- Product filtering by budget, brand, technology
- Final product list with prices and descriptions

### Flow 2: Not Relevant (Lines 37-42: copilot-instructions.md)  
**Pattern**: Out-of-scope question → Clear rejection with supported domains
**Example**: "I'm looking for my mom" → "Sorry, I only help with printers, laptops..."

**Requirements**:
- Domain validation
- Supported category enumeration
- Graceful rejection responses

### Flow 3: No Results (Lines 44-48: copilot-instructions.md)
**Pattern**: Valid filters → Zero matches → Alternative suggestions
**Example**: "Brother laser printer under €50" → "No matches, try broader budget"

**Requirements**:
- Empty result detection
- Alternative suggestion generation
- Contact support fallback

### Flow 4: Too Many Results (Lines 50-65: copilot-instructions.md)
**Pattern**: Broad query → Large result set → Refinement or sampling options
**Example**: "I want a printer" → 152 results → "Top 5 by price or random sample?"

**Requirements**:
- Result count thresholds
- Sorting options (price, rating, popularity)
- Result sampling strategies

## Mock Data Requirements

### Product Catalog Structure
Based on examples in instructions:

**Product Schema**:
```python
{
    "id": "brother-xc-2570",
    "name": "Brother XC 2570", 
    "price": 199,
    "brand": "Brother",
    "category": "printer",
    "technology": "laser",
    "description": "short description"
}
```

**Sample Products**:
- Brother XC 2570 – €199 – Laser printer
- Brother XT 3560 – €159 – Laser printer  
- Brother ZX 1570 – €69 – Budget laser printer
- HP Inkjet 234 – €79 – Inkjet printer
- HP Inkjet 1234 – €109 – Inkjet printer
- Kyocera T70 – €99 – Laser printer

### Filter Categories
**Budget Ranges**:
- "Less than €150"
- "Between €150–€300" 
- "More than €300"
- "No preference"

**Brands**: Brother, BenQ, HP, Kyocera, Canon, Epson

**Technologies**: Inkjet, Laser, Thermal inkjet

**Supported Categories**: Printers, Laptops, Smartphones, Tablets

## Implementation Strategy

### Phase 1: Enhanced Response Types
- Extend `AskResponse` with product list support
- Add product filtering result types
- Implement refinement question patterns

### Phase 2: Product Catalog Mock
- Create `FakeProductCatalog` class
- Implement filtering by budget, brand, technology
- Add result count management and sampling

### Phase 3: Enhanced Orchestrator  
- Add product discovery decision logic
- Implement progressive refinement patterns
- Add domain validation for supported categories

### Phase 4: Integration & Testing
- Update API endpoints for product responses
- Add comprehensive test coverage
- Validate all 4 core flows work end-to-end

## Technical Dependencies

**Current Stack**:
- FastAPI for REST API
- Pydantic for data validation
- Python 3.12+ with type hints
- pytest for testing

**No External Dependencies Required** - All mocking will be in-memory

## Success Criteria

1. All 4 core flows from instructions work with realistic mock data
2. Progressive product refinement through multiple ask/reply cycles
3. Proper result management (empty results, too many results)
4. Domain validation and rejection for unsupported queries
5. Comprehensive test coverage for all new flows
6. Backward compatibility with existing functionality

## Code Examples from Current Implementation

**Current Orchestrator Decision Logic** (Lines 65-98: pixie/core/pixie.py):
```python
def _simulate_llm_decision(self, question: str, tabular_result: dict) -> str:
    # Pattern 1: Very vague questions -> ask_user
    vague_patterns = ["algemeen", "meer info", "vertel eens", ...]
    
    # Pattern 2: Complex multi-part questions -> ask_user
    if "?" in question and len(question.split("?")) > 2:
        return "ask_user"
        
    # Pattern 3: Has specific data available -> answer_with_data
    if tabular_result.get("found_data"):
        return "answer_with_data"
        
    # Pattern 4: Specific, answerable questions -> answer_text_only
    specific_patterns = ["hoofdstad", "naam", "wanneer", ...]
```

**Current API Flow** (Lines 67-119: apps/api/main.py):
```python
# Auto-detect request type based on pending_id presence
pending_id = req.get("pending_id")

if pending_id:
    # Reply flow: responding to a pending question
    resp = pixie.reply(pending_id.strip(), message.strip())
else:
    # New question flow  
    resp = pixie.answer(question.strip())
```

This architecture provides an excellent foundation for implementing the product discovery flows through mock data and enhanced decision logic.
