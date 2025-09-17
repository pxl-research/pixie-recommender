"""
Simplified Conversation State Machine Design

Target: Replace complex imperative logic with declarative state patterns
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ConversationState(Enum):
    """Clear, finite states for conversation flow."""

    INITIAL = "initial"
    RELEVANCE_CHECK = "relevance_check"
    CATEGORY_DETECTED = "category_detected"
    COLLECTING_ATTRIBUTES = "collecting_attributes"
    GENERATING_RESULTS = "generating_results"
    COMPLETED = "completed"
    ERROR = "error"
    NOT_RELEVANT = "not_relevant"


@dataclass
class StateTransition:
    """Declarative state transition definition."""

    from_state: ConversationState
    to_state: ConversationState
    condition: str  # Method name to check
    action: str  # Method name to execute


@dataclass
class AttributeDefinition:
    """Simplified attribute configuration."""

    name: str
    question_template: str
    required: bool = True
    validation: Optional[str] = None


@dataclass
class ConversationFlow:
    """Declarative conversation flow per category."""

    category: str
    attributes: List[AttributeDefinition]
    max_iterations: int = 3
    fallback_sql_template: str = ""


# Example configuration - declarative instead of hardcoded
CONVERSATION_FLOWS = {
    "printers": ConversationFlow(
        category="printers",
        attributes=[
            AttributeDefinition("budget", "Wat is je budget voor een printer?"),
            AttributeDefinition("brand", "Heb je een voorkeur voor een bepaald merk?"),
            AttributeDefinition(
                "technology", "Welke printtechnologie prefereer je (inkjet/laser)?"
            ),
            AttributeDefinition(
                "connectivity", "Welke verbindingsopties wil je (WiFi, USB, Ethernet)?"
            ),
        ],
        max_iterations=4,
        fallback_sql_template="SELECT * FROM products WHERE product_type_id = {type_id}",
    ),
    "laptops": ConversationFlow(
        category="laptops",
        attributes=[
            AttributeDefinition("budget", "Wat is je budget voor een laptop?"),
            AttributeDefinition("brand", "Heb je een voorkeur voor een bepaald merk?"),
            AttributeDefinition("screen_size", "Welke schermgrootte zoek je?"),
        ],
        max_iterations=3,
    ),
}

# State machine transitions - declarative
STATE_TRANSITIONS = [
    StateTransition(
        ConversationState.INITIAL,
        ConversationState.RELEVANCE_CHECK,
        "should_check_relevance",
        "check_relevance",
    ),
    StateTransition(
        ConversationState.RELEVANCE_CHECK,
        ConversationState.NOT_RELEVANT,
        "is_not_relevant",
        "handle_not_relevant",
    ),
    StateTransition(
        ConversationState.RELEVANCE_CHECK,
        ConversationState.CATEGORY_DETECTED,
        "has_category",
        "detect_category",
    ),
    StateTransition(
        ConversationState.CATEGORY_DETECTED,
        ConversationState.COLLECTING_ATTRIBUTES,
        "needs_attributes",
        "start_attribute_collection",
    ),
    StateTransition(
        ConversationState.COLLECTING_ATTRIBUTES,
        ConversationState.GENERATING_RESULTS,
        "has_enough_attributes",
        "generate_search_results",
    ),
    StateTransition(
        ConversationState.COLLECTING_ATTRIBUTES,
        ConversationState.COLLECTING_ATTRIBUTES,
        "needs_more_attributes",
        "ask_next_attribute",
    ),
    StateTransition(
        ConversationState.GENERATING_RESULTS,
        ConversationState.COMPLETED,
        "has_results",
        "return_results",
    ),
    StateTransition(
        ConversationState.GENERATING_RESULTS,
        ConversationState.ERROR,
        "search_failed",
        "handle_search_error",
    ),
]


class SimplifiedStateMachine:
    """
    Clean state machine implementation with:
    - Clear state definitions
    - Declarative transitions
    - Separation of conditions from actions
    - Easy testing and debugging
    """

    def __init__(self, initial_state: ConversationState = ConversationState.INITIAL):
        self.current_state = initial_state
        self.context = {}
        self.transitions = {
            (t.from_state, t.condition): (t.to_state, t.action)
            for t in STATE_TRANSITIONS
        }

    def transition(self, condition: str) -> Optional[str]:
        """Execute state transition if condition is met."""
        key = (self.current_state, condition)
        if key in self.transitions:
            new_state, action = self.transitions[key]
            self.current_state = new_state
            return action
        return None

    def is_terminal_state(self) -> bool:
        """Check if conversation is complete."""
        return self.current_state in [
            ConversationState.COMPLETED,
            ConversationState.ERROR,
            ConversationState.NOT_RELEVANT,
        ]


class SimplifiedConversationManager:
    """
    Clean conversation manager using state machine pattern.

    Benefits:
    - ~100 lines instead of 447
    - Declarative configuration
    - Easy to test and debug
    - Clear separation of concerns
    - Predictable state transitions
    """

    def __init__(self, llm_orchestrator, search_coordinator, pending_store):
        self.llm_orchestrator = llm_orchestrator
        self.search_coordinator = search_coordinator
        self.pending_store = pending_store
        self.flows = CONVERSATION_FLOWS

    def handle_new_question(self, question: str) -> dict:
        """Handle new question using state machine."""
        machine = SimplifiedStateMachine()
        machine.context = {"question": question}

        while not machine.is_terminal_state():
            # Get next action based on current state
            action = self._get_next_action(machine)
            if not action:
                break

            # Execute action and get condition for next transition
            condition = self._execute_action(action, machine)
            if condition:
                machine.transition(condition)

        return self._create_response(machine)

    def handle_reply(self, pending_id: str, reply: str) -> dict:
        """Handle reply using restored state machine."""
        # Restore state from pending store
        pending_data = self.pending_store.get_pending(pending_id)
        machine = SimplifiedStateMachine()
        machine.context = pending_data.conversation_context
        machine.current_state = ConversationState(machine.context.get("state"))

        # Process reply and continue state machine
        machine.context["latest_reply"] = reply

        while not machine.is_terminal_state():
            action = self._get_next_action(machine)
            if not action:
                break
            condition = self._execute_action(action, machine)
            if condition:
                machine.transition(condition)

        return self._create_response(machine)

    # Implementation methods would be ~50 lines of clean, focused logic
    # Each method has single responsibility
    # Easy to test in isolation
    # No complex state management in each method


"""
Key Simplification Benefits:

1. **State Clarity**: Enum states vs string-based stage tracking
2. **Declarative Config**: CONVERSATION_FLOWS vs hardcoded logic  
3. **Predictable Transitions**: STATE_TRANSITIONS table vs complex conditionals
4. **Separation of Concerns**: Each class has single responsibility
5. **Testability**: Clean interfaces for mocking and unit testing
6. **Maintainability**: Changes require config updates, not code changes
7. **Debuggability**: Clear state history and transition logging

Result: 447 lines → ~150 lines with better maintainability
"""
