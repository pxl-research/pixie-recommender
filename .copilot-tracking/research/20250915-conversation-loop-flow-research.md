# Conversation Loop Flow Implementation Research

**Date:** 2025-09-15  
**Researcher:** GitHub Copilot  
**Branch:** v0.5_real_llms  

## Executive Summary

This research analyzes the current pixie-core architecture and identifies requirements for implementing a conversation loop flow. The current system has been migrated from mock LLMs to Azure OpenAI LLMs, with a basic conversation loop already implemented. However, the existing flow is limited and needs enhancement to support more complex conversational patterns.

## Current Project Analysis

### Architecture Overview

The pixie-core system is structured as follows:

```bash
pixie-core/
├── apps/api/main.py              # FastAPI server with /ask endpoint
├── pixie/core/
│   ├── conversation/             # Main conversation logic
│   │   ├── pixie.py             # Pixie class delegating to ConversationLoopManager
│   │   └── conversation_loop.py # ConversationLoopManager implementation
│   ├── llms/                    # Azure OpenAI LLM implementations
│   ├── search/                  # RealSearchEngine for printer data
│   ├── storage/                 # InMemoryPendingStore for conversation state
│   └── utils/                   # Config, contracts, logging
└── tests/                       # Comprehensive test suite
```

### Existing Flows and Implementation Patterns

#### Current Conversation Flow

The existing `ConversationLoopManager` implements a simple linear conversation flow:

1. **New Question Handling:**
   - Check relevance using AzureRelevanceLLM
   - If not relevant: return "not_relevant"
   - If relevant: create pending entry with context `{"flow": "product", "stage": "ask_budget", "iterations": 0}`
   - Generate refinement question using AzureRefinementLLM
   - If no prompt: fallback to SQL search
   - Return "ask_user" with prompt and pending_id

2. **Reply Handling:**
   - Stages: `ask_budget` → `ask_brand` → `ask_tech` → `choose_result_view`
   - Each reply updates context and generates next refinement question
   - After `ask_tech`: generate SQL using AzureSQLLLM and search
   - If no results: either ask for view choice or return "no_results"
   - If results: return "answer"

#### API Structure

- Single `/ask` endpoint handling both new questions and replies
- Request format: `{"question": "..."}` or `{"pending_id": "...", "message": "..."}`
- Response: `AskResponse` with types: `answer`, `ask_user`, `not_relevant`, `error`, `no_results`

#### State Management

- `InMemoryPendingStore` with TTL (300s default)
- `PendingEntry` contains: `pending_id`, `question`, `created_at`, `conversation_context`
- Context tracks: `flow`, `stage`, `iterations`, `budget`, `brand`, `technology`, `view`

#### Mock Data Systems

- Printer data in `pixie/core/data/printers.json` (425 lines, ~100 printers)
- Schema defined in `schema.json`
- `RealSearchEngine` filters by budget, brand, technology
- Returns limited results for vague queries (default_page_size=10)

### Current Implementation Patterns

#### Code Organization

- Clean separation: LLMs, Search, Storage, Conversation logic
- Dependency injection pattern in ConversationLoopManager
- Factory pattern for LLM creation (`azure_llm_set.create_azure_llm_set()`)
- Centralized configuration via `config.py`

#### Error Handling

- Basic exception catching in API layer
- TTL-based cleanup of expired conversations
- Graceful fallback to empty datasets

#### Testing

- Comprehensive unit tests for ConversationLoopManager
- Integration tests with RealSearchEngine
- Mock LLM fixtures for testing

## Conversation Loop Flow Requirements

### Flowchart Analysis

**Note:** No flowchart diagram was found in the provided context. Analysis based on existing code and custom instructions.

Based on the existing `conversation_loop.py` and test patterns, the current flow appears to be:

```bash
New Question
├── Relevance Check
│   ├── Not Relevant → "not_relevant"
│   └── Relevant → Create Pending
│       ├── Try Refinement Question
│       │   ├── Has Prompt → "ask_user" (budget)
│       │   └── No Prompt → SQL Search
│       │       ├── Has Results → "answer"
│       │       └── No Results → "ask_user" (budget)
│
Reply (pending_id, message)
├── Validate Pending ID
│   └── Invalid → "error"
├── Stage: ask_budget
│   ├── Store budget → ask_brand
│   └── Generate refinement → "ask_user"
├── Stage: ask_brand  
│   ├── Store brand → ask_tech
│   └── Generate refinement → "ask_user"
├── Stage: ask_tech
│   ├── Store technology → Generate SQL
│   ├── Search with context
│   │   ├── Has Results → "answer"
│   │   └── No Results
│   │       ├── Iterations < max → choose_result_view
│   │       └── Iterations >= max → "no_results"
└── Stage: choose_result_view
    ├── Store view → Generate SQL with view
    ├── Search
    │   ├── Has Results → "answer"
    │   └── No Results → "no_results"
```

### Decision Points and Flow Logic

**Key Decision Points:**

1. **Relevance Check:** Binary - relevant/not relevant
2. **Initial Search Fallback:** If no refinement prompt, attempt immediate SQL search
3. **Result Availability:** Has results / no results after each search
4. **Iteration Limits:** Max iterations reached (default 3)
5. **View Selection:** When no results found, offer view choice

**Flow Logic Issues:**

- Hard-coded stages limit flexibility
- No branching logic beyond linear progression
- Limited error recovery
- No support for conversation restart or correction

### State Management Requirements

**Current State:**

- Simple dict-based context: `{"flow": "product", "stage": "...", "iterations": int, ...}`
- Stored in InMemoryPendingStore with TTL

**Enhancement Needs:**

- More flexible state machine
- Support for multiple flows
- Conversation history tracking
- Error state recovery
- User correction capabilities

## Implementation Patterns Analysis

### Existing conversation_loop.py Patterns

- **Strengths:** Simple, linear flow; clear stage progression; TTL management
- **Weaknesses:** Hard-coded stages; no flow branching; limited error handling; complex nested if-statements

### Recommended Patterns

- **State Machine Pattern:** Replace if-else chains with explicit state transitions
- **Strategy Pattern:** Different flow strategies for different conversation types
- **Command Pattern:** Encapsulate actions for each stage
- **Observer Pattern:** Notify components of state changes

### Mock Implementation Strategies

- Keep existing flow as "product_flow"
- Add flow registry for extensibility
- Maintain backward compatibility
- Use in-memory state for development

## Technical Specifications

### Required Changes to Core Logic

#### Pixie Class (`pixie/core/conversation/pixie.py`)

- Add flow selection logic
- Support multiple ConversationLoopManager instances
- Maintain API compatibility

#### ConversationLoopManager

- Refactor to use state machine pattern
- Support pluggable flow definitions
- Add flow validation and error recovery

#### New Components Needed

- `FlowRegistry`: Register and instantiate flows
- `StateMachine`: Manage conversation states and transitions  
- `FlowDefinition`: Define stages, transitions, actions
- `ConversationHistory`: Track user interactions

### API Endpoint Modifications

- No changes needed to `/ask` endpoint
- Add optional `flow_type` parameter for flow selection
- Maintain backward compatibility

### State Management Approach

- Extend `conversation_context` with flow metadata
- Add `flow_type`, `state_machine`, `history`
- Keep in-memory for mock implementation
- Design for future persistence layer

## Integration Requirements

### Maintaining Existing 4 Flows

#### Note on Existing Flows

Note: Only 1 flow "product" currently implemented. Assuming 4 flows means expanding to multiple product-related flows.

- **Compatibility:** Existing API calls work unchanged
- **Flow Selection:** Default to "product" flow if not specified
- **Isolation:** Each flow maintains separate state

### Backward Compatibility

- Existing `AskResponse` types unchanged
- Context structure backward compatible
- No breaking changes to `/ask` endpoint

### Test Coverage Requirements

- Unit tests for new state machine
- Integration tests for multiple flows
- Backward compatibility tests
- Error handling tests

### Documentation Updates

- API documentation for flow selection
- Flow definition schema
- State management guide
- Migration guide for custom flows

## Success Criteria Verification

### Code Analysis Findings

- ✅ **Architecture:** Clean modular design with separation of concerns
- ✅ **Current Flow:** Basic linear conversation implemented
- ✅ **State Management:** InMemoryPendingStore with TTL
- ✅ **API Structure:** Single endpoint with AskResponse contract
- ✅ **Mock Data:** Printer dataset with RealSearchEngine

### Implementation Guidance

- ✅ **State Machine Pattern:** Recommended for flexibility
- ✅ **Flow Registry:** For extensibility
- ✅ **Backward Compatibility:** Maintain existing behavior
- ✅ **Error Handling:** Add recovery mechanisms

### Implementation Technical Specifications

- ✅ **Core Changes:** Identified required modifications
- ✅ **New Components:** Defined necessary classes
- ✅ **API Changes:** Minimal, backward compatible
- ✅ **State Approach:** Extended context with metadata

### Integration and Compatibility Requirements

- ✅ **Multiple Flows:** Design for 4+ flows
- ✅ **Compatibility:** No breaking changes
- ✅ **Testing:** Comprehensive coverage plan
- ✅ **Documentation:** Update requirements specified

## Next Steps

1. **Implement State Machine Pattern** in ConversationLoopManager
2. **Create Flow Registry** for multiple conversation flows  
3. **Add Flow Definitions** for product search variations
4. **Extend State Management** with history tracking
5. **Update Tests** for new architecture
6. **Add Error Recovery** mechanisms
7. **Document Flow Creation** guide

## External References

- **State Machine Patterns:** [Wikipedia](https://en.wikipedia.org/wiki/State_machine)
- **Azure OpenAI API:** [Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- **FastAPI Best Practices:** [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- **Python Data Classes:** [Python Docs](https://docs.python.org/3/library/dataclasses.html)

## Conclusion

The current pixie-core system provides a solid foundation with Azure LLM integration and basic conversation flow. The architecture supports extension to more complex flows through state machine patterns and flow registries. Key priorities are maintaining backward compatibility while adding flexibility for multiple conversation types.</content>
filePath="/Users/drphil/Documents/Werk/pixie-core/.copilot-tracking/research/20250908-conversation-loop-flow-research.md"
