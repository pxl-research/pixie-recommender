# Pixie-Core Architecture Research Report

**Date:** September 16, 2025  
**Project:** pixie-core  
**Current Branch:** v0.6_multiple_sources  
**Purpose:** Complete architectural analysis for conversation loop flow implementation planning  

## Executive Summary

This research provides a comprehensive analysis of the current pixie-core architecture to support implementing sophisticated conversation loop flows. The system has successfully evolved from mock to Azure OpenAI LLMs and implements 4 distinct product flows with a conversational interface. The current implementation shows a solid foundation for conversation management but uses linear stage progression that could be enhanced with more sophisticated flow control patterns.

## Current Project Analysis

### 1. Architecture Overview

**Core Components:**
- **FastAPI Application** (`apps/api/main.py`): Single `/ask` endpoint handling both new questions and replies
- **Pixie Main Class** (`pixie/core/conversation/pixie.py`): Simple delegator to ConversationLoopManager
- **ConversationLoopManager** (`pixie/core/conversation/conversation_loop.py`): Core conversation orchestrator (300+ lines)
- **LLM Set** (Azure + Mock): Three specialized LLMs (relevance, SQL, refinement)
- **Search Engine** (`pixie/core/search/search_engine.py`): JSON-based product search with multi-category support
- **Pending Store** (`pixie/core/storage/pending_store.py`): In-memory conversation state management with TTL

**Dependencies:**
```toml
dependencies = [
  "fastapi>=0.110,<1.0",
  "uvicorn[standard]>=0.29,<1.0", 
  "pydantic>=2.5,<3.0",
  "langchain-openai>=0.1,<1.0"
]
```

### 2. Current Flow Implementation Analysis

#### Existing 4 Flows (as documented in README.md):

1. **Product Discovery Flow**
   - **Trigger:** `"Ik zoek een nieuwe printer"`
   - **Behavior:** Starts conversational refinement (budget → brand → technology)
   - **Implementation:** ConversationLoopManager with hardcoded stages

2. **Specific Product Search**
   - **Trigger:** `"Ik wil een Brother laserprinter onder de €150"`
   - **Behavior:** Direct SQL generation and search
   - **Implementation:** Bypasses conversation flow when specific attributes provided

3. **Not Relevant Flow**
   - **Trigger:** `"Waar kan ik mijn moeder vinden?"`
   - **Behavior:** Returns `{"type": "not_relevant"}`
   - **Implementation:** AzureRelevanceLLM classifies as non-product-related

4. **No Results Flow**
   - **Trigger:** Overly restrictive criteria
   - **Behavior:** Returns `{"type": "no_results"}` after max iterations
   - **Implementation:** Search returns empty after filtering, triggers result view choice

#### Multi-Category Support (4 Categories):
- **Printers:** budget → brand → technology (inkjet/laser)
- **Laptops:** budget → brand → screen_size
- **Computers:** budget → brand → processor  
- **Smartphones:** budget → brand → screen_size

### 3. Current API Structure

**Request/Response Format:**
```json
// New question
POST /ask
{"question": "Ik zoek een nieuwe printer"}

// Reply to pending question  
POST /ask
{"pending_id": "pending-xxxx", "message": "Minder dan 150 euro"}

// Response types
{
  "type": "ask_user|answer|not_relevant|no_results|error",
  "text": "response text",
  "prompt": "follow-up question", 
  "pending_id": "pending-xxxx",
  "reason": "error reason"
}
```

**Key Insight:** The API structure is simple and stable, supporting both new questions and conversation replies through a single endpoint.

### 4. Conversation State Management

**Current Implementation:**
- **Storage:** `InMemoryPendingStore` with TTL (300 seconds default)
- **Context Structure:**
```json
{
  "flow": "product",
  "category": "printers|laptops|computers|smartphones",
  "stage": "ask_budget|ask_brand|ask_tech|choose_result_view", 
  "iterations": 0,
  "question": "original question",
  "collected_attributes": ["budget", "brand"],
  "budget": "user response",
  "brand": "user response", 
  "technology": "user response",
  "view": "user preference"
}
```

**Limitations:**
- Linear stage progression managed by hardcoded `_get_next_stage()` method
- No branching logic or conditional flows
- Limited to 4-5 conversation stages per category
- No complex decision trees or dynamic state transitions

## ConversationLoopManager Deep Analysis

### Current Flow Logic (line-by-line analysis)

**File:** `pixie/core/conversation/conversation_loop.py`

#### handle_new_question() Method:
```python
# Lines 39-79: Initial question processing
1. Relevance check via AzureRelevanceLLM.is_relevant()
2. If not relevant → return not_relevant response
3. Category detection via AzureRelevanceLLM.detect_category()
4. Create pending_id and initialize context with category
5. Load attribute manager and determine first stage
6. Try refinement question generation first
7. Fallback to immediate SQL search if refinement fails
8. Return ask_user with prompt or immediate answer
```

#### handle_reply() Method - Stage Progression:
```python
# Lines 160-300: Hardcoded stage transitions
stage="ask_budget" → add budget → stage="ask_brand" → ask brand question
stage="ask_brand" → add brand → stage="ask_tech" → ask tech question  
stage="ask_tech" → add tech → generate SQL → search
  - If results: return answer
  - If no results + iterations < max: stage="choose_result_view" 
  - If no results + max iterations: return no_results
stage="choose_result_view" → add view → search again → return answer or no_results
```

**Critical Limitations:**
- **No flow branching:** Only one conversation path per category (budget→brand→tech)
- **No conditional logic:** Cannot skip stages based on user input
- **Hardcoded stages:** Cannot dynamically determine next question based on context
- **Limited decision points:** Only max_iterations counter prevents infinite loops

### Mock vs Azure LLM Patterns

**Mock LLM Implementation** (`pixie/core/llms/mock_llm_set.py`):
- **MockRelevance:** Simple keyword matching for product relevance + category detection
- **MockSQL:** Returns hardcoded "SELECT * FROM {category};"
- **MockRefinement:** Linear question progression based on missing context keys

**Azure LLM Implementation:**
- **AzureRelevanceLLM:** AI-powered relevance classification and category detection
- **AzureSQLLLM:** Dynamic SQL generation based on conversation context and category
- **AzureRefinementLLM:** AI-generated refinement questions with fallback to static progression

**Key Insight:** The system architecture supports both mock and real LLMs seamlessly, enabling robust testing and gradual migration.

## Flow Control Requirements Analysis

### Missing Conversation Loop Capabilities

Based on the need for more sophisticated conversation loops, the following capabilities appear to be missing:

1. **Dynamic Flow Routing**
   - Conditional branching based on user responses
   - Multiple conversation paths from a single starting point
   - Context-aware flow selection

2. **Complex Decision Trees**
   - Multi-level conditional logic
   - Parallel information gathering paths
   - Dynamic question ordering based on priorities

3. **Advanced State Management**
   - Flow state tracking beyond simple stage progression
   - Support for backtracking and flow restarts
   - Context preservation across flow transitions

4. **Conversation Strategy Pattern**
   - Pluggable conversation strategies
   - Flow-specific refinement logic
   - Configurable conversation templates

### Integration Requirements

**Backward Compatibility:**
- Current 4 flows must continue to work unchanged
- Existing API structure should be preserved  
- Mock implementation should remain functional

**Extension Points:**
- ConversationLoopManager should support flow strategies
- Pending store should support richer conversation context
- LLM interfaces should support flow-aware prompting

## Technical Implementation Recommendations

### 1. Flow Strategy Pattern Implementation

**Proposed Structure:**
```python
# New flow strategy interface
class ConversationFlowStrategy:
    def get_next_stage(self, context: dict, user_response: str) -> Optional[str]
    def should_generate_sql(self, context: dict) -> bool
    def get_refinement_prompt(self, context: dict) -> Optional[str]

# Existing linear flow (maintains compatibility)
class LinearProductFlowStrategy(ConversationFlowStrategy):
    # Implements current hardcoded stage progression
    
# New sophisticated flow
class DynamicProductFlowStrategy(ConversationFlowStrategy):
    # Implements flowchart-based conversation logic
```

### 2. Enhanced Conversation Context

**Proposed Context Structure:**
```python
@dataclass
class ConversationContext:
    flow_type: str  # "product", "support", etc.
    flow_strategy: str  # "linear", "dynamic", "guided"
    current_stage: str
    completed_stages: Set[str]
    collected_attributes: Dict[str, Any]
    conversation_history: List[Dict[str, str]]
    flow_metadata: Dict[str, Any]  # Strategy-specific data
    priority_queue: List[str]  # Next questions to ask
```

### 3. ConversationLoopManager Refactoring

**Minimal Changes Required:**
```python
class ConversationLoopManager:
    def __init__(self, search_fn, flow_strategy=None, **kwargs):
        self.flow_strategy = flow_strategy or LinearProductFlowStrategy()
        # ... existing initialization
    
    def handle_reply(self, pending_id: str, reply: str) -> AskResponse:
        # Replace hardcoded stage logic with strategy pattern
        next_stage = self.flow_strategy.get_next_stage(context, reply)
        # ... implement strategy-driven flow control
```

### 4. Testing Strategy

**Test Coverage Requirements:**
- Existing tests must continue to pass (backward compatibility)
- New flow strategies should have comprehensive test coverage
- Integration tests for complex conversation paths
- Mock implementations for reliable CI/CD

**Test Implementation:**
```python
# Existing test structure should be preserved
def test_basic_success_path(mock_llm_set):
    # Current test - should continue to work

# New tests for advanced flows  
def test_dynamic_flow_branching(mock_llm_set):
    # Test conditional conversation paths
    
def test_flow_strategy_switching(mock_llm_set):
    # Test runtime flow strategy changes
```

## Data Model Analysis

### Current Product Data Structure

**File:** `pixie/core/data/printers.json` (and similar for other categories)
- **Schema:** 425 lines, ~40+ records per category
- **Fields:** id, name, brand, technology, price, description, features, availability
- **Search Attributes:** budget (price), brand, technology/screen_size/processor
- **Filtering Logic:** Handles vague responses ("weet ik niet") gracefully

### Attribute Configuration

**File:** `pixie/core/data/attributes.json`
- **Structure:** Category-specific attribute definitions
- **Questions:** Dutch language questions for each attribute
- **Types:** range, choice with predefined options
- **Extensible:** Easy to add new attributes or categories

### Search Engine Capabilities

**Current Features:**
- Budget range parsing ("maximaal 200 euro", "100-200 euro")  
- Brand exact matching with vague response filtering
- Technology/feature filtering per category
- Default page sizing for vague queries (prevents data dumps)
- Multi-category support with category-specific metadata

**Extension Points:**
- Additional attribute filters can be easily added
- Search logic is separate from conversation logic
- Supports both SQL-style queries and attribute filtering

## Configuration and Environment

### Environment Variables
```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_VERSION=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_KEY=
AZURE_OPENAI_MODEL=

# Pixie Configuration
PIXIE_FORCE_MOCKS=1  # Forces mock LLMs for testing
```

### Configuration Files
- **Search Configuration:** `pixie/core/utils/config.py`
- **Data File Paths:** Configurable via environment
- **LLM Fallback:** Automatic fallback to mocks when Azure unavailable

## External Dependencies Analysis

### Current Dependencies (`pyproject.toml`):
- **FastAPI + Uvicorn:** Web framework and ASGI server
- **LangChain OpenAI:** Azure OpenAI integration
- **Pydantic:** Data validation (minimal usage)
- **Dev Dependencies:** pytest, httpx, ruff for testing and linting

### Stability Assessment:
- **Minimal dependency footprint** reduces security and maintenance risks
- **Well-established libraries** ensure long-term stability
- **Mock implementations** provide independence from external services
- **Locked dependency versions** (`uv.lock`) ensure reproducible builds

## Implementation Complexity Assessment

### Low Risk Changes:
1. **Flow strategy interface** - Can be implemented as an optional parameter
2. **Enhanced context structure** - Backward compatible with current dict approach
3. **Additional conversation stages** - Can extend existing stage enumeration

### Medium Risk Changes:
1. **ConversationLoopManager refactoring** - Core logic changes but well-tested
2. **Complex flow branching logic** - New code paths require extensive testing
3. **Dynamic conversation routing** - Potential for infinite loops or dead ends

### High Risk Changes:
1. **API structure modifications** - Could break existing clients
2. **Fundamental conversation model changes** - Would require complete rewrite
3. **External service dependencies** - Could introduce reliability issues

## Success Criteria and Next Steps

### Immediate Implementation Goals:
1. **Preserve existing functionality** - All current flows must work unchanged
2. **Enable flow strategy pattern** - Support pluggable conversation strategies
3. **Implement basic branching** - Support conditional conversation paths
4. **Maintain test coverage** - All changes must be thoroughly tested

### Progressive Enhancement Path:
1. **Phase 1:** Implement strategy pattern with linear strategy (current behavior)
2. **Phase 2:** Add dynamic flow strategy with basic branching
3. **Phase 3:** Implement sophisticated conversation flow from diagram
4. **Phase 4:** Add advanced features (backtracking, parallel paths, etc.)

### Quality Assurance Requirements:
- **100% backward compatibility** with existing API
- **Comprehensive test coverage** for new functionality
- **Performance parity** with current implementation
- **Clear documentation** for new conversation patterns

## Conclusion

The current pixie-core implementation provides a solid foundation for implementing sophisticated conversation loop flows. The architecture is well-designed with clear separation of concerns, robust testing infrastructure, and support for both mock and real LLM implementations.

**Key Strengths:**
- Clean, maintainable codebase with good separation of concerns
- Robust testing infrastructure with mock and real LLM support
- Container-first development ensuring environment consistency
- Simple but effective conversation state management
- Multi-category support with attribute-driven questioning
- Flexible search engine with category-specific filtering

**Key Limitations:**
- Linear conversation flow with hardcoded stage progression
- No support for conditional branching or complex decision trees
- Limited conversation context structure
- Lack of pluggable flow strategies

**Recommended Approach:**
Implement a strategy pattern for conversation flows that maintains backward compatibility while enabling sophisticated conversation logic. This can be achieved with minimal disruption to the existing codebase and allows for progressive enhancement of conversation capabilities.

The system is well-positioned for implementing sophisticated conversation loop flows, with the strategy pattern providing the necessary foundation for complex flow control while preserving the simplicity and reliability of the current implementation.

---

**Research Completed:** September 16, 2025  
**Next Phase:** Technical planning and implementation design based on this analysis
