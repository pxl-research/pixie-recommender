# Conversation Loop Complexity Analysis

## Huidige Complexiteit (447 lines)

### Hoofdproblemen geïdentificeerd:

#### 1. **State Management Chaos**
- `context` dictionary met mixed responsibilities
- Manual state transitions (`stage`, `iterations`, `collected_attributes`, `skipped_attributes`)
- Complex conditionals voor state validatie
- Geen centrale state machine

#### 2. **Tight Coupling Between Components**
- LLM calls verspreid door de hele flow
- Search engine directly coupled aan conversation logic  
- Attribute management mixed met conversation control
- Pending store operations everywhere

#### 3. **Complex Iteration Logic**
```python
# Lines 267-279: Complex iteration tracking
if ctx["iterations"] >= self.max_iterations:
    # Generate SQL fallback
    try:
        sql = self.sql_model.generate_sql(...)
    except Exception:
        return AskResponse(type="error", reason="llm_failure")
```

#### 4. **Hardcoded Fallback Logic**
```python  
# Lines 174-209: Hardcoded category logic
if category == "printers":
    attr_sequence = ["budget", "brand", "technology", "color", "pages_per_minute"]
    for attr in attr_sequence:
        if attr not in processed:
            return f"ask_{attr}"
```

#### 5. **Mixed Responsibilities**
- Question relevance checking
- Category detection  
- Attribute collection orchestration
- SQL generation coordination
- Search result handling
- State persistence

## Complexiteit Hotspots

### Lines 67-173: `handle_new_question()`
- **106 lines** met mixed responsibilities
- Category detection, metadata lookup, context initialization
- Refinement vs direct search decision logic

### Lines 174-213: `_get_next_stage()`  
- **39 lines** met hardcoded fallback logic
- Try/except around attribute manager
- Manual sequence definitions per category

### Lines 214-447: `handle_reply()`
- **233 lines** - de grootste method
- Attribute processing, stage transitions, iteration limits
- SQL generation, search execution, result handling

## Root Causes

1. **No Separation of Concerns**: Een class doet alles
2. **Imperative Logic**: Alles in if/else chains ipv declarative patterns  
3. **Exception-Driven Flow**: Try/catch als primary control flow
4. **Stateful Mutations**: Direct context dictionary manipulation
5. **Inline LLM Orchestration**: LLM calls overal verspreid

## Simplification Strategy

### Phase 1: Extract & Isolate
1. **ConversationState** class voor state management
2. **AttributeCollector** voor attribute gathering logic  
3. **LLMOrchestrator** voor coordinated LLM calls
4. **FlowConfiguration** voor declarative conversation definitions

### Phase 2: Declarative Patterns
1. **State Machine** ipv manual state tracking
2. **Configuration-driven** flows ipv hardcoded logic
3. **Dependency Injection** ipv tight coupling
4. **Event-driven** transitions ipv imperative control

### Phase 3: Clean Interface
1. **Simple ConversationManager** als facade
2. **Single Responsibility** per component
3. **Testable Units** met mocked dependencies
4. **Clear Error Handling** with proper boundaries

## Target Architecture

```
ConversationManager (facade)
├── ConversationState (state management)  
├── AttributeCollector (gathering logic)
├── LLMOrchestrator (AI coordination)
├── FlowConfiguration (declarative flows)
└── SearchCoordinator (result handling)
```

**Verwachte Resultaat**: Van 447 lines naar ~150 lines met betere maintainability.
