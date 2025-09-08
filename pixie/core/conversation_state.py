"""Conversation state management for progressive product refinement."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConversationState:
    """Represents the state of a product discovery conversation."""
    
    original_question: str
    detected_category: Optional[str] = None
    applied_filters: Dict[str, Any] = field(default_factory=dict)
    conversation_step: int = 0
    needs_refinement: bool = True


class ConversationStateManager:
    """Manages conversation state for multi-turn product discovery."""

    def __init__(self):
        self._states: Dict[str, ConversationState] = {}

    def create_state(
        self, 
        pending_id: str, 
        original_question: str,
        detected_category: Optional[str] = None
    ) -> ConversationState:
        """Create new conversation state."""
        state = ConversationState(
            original_question=original_question,
            detected_category=detected_category,
            applied_filters={},
            conversation_step=0,
            needs_refinement=True
        )
        self._states[pending_id] = state
        return state

    def get_state(self, pending_id: str) -> Optional[ConversationState]:
        """Get conversation state by pending_id."""
        return self._states.get(pending_id)

    def update_state(
        self, 
        pending_id: str, 
        filter_updates: Dict[str, Any],
        increment_step: bool = True
    ) -> Optional[ConversationState]:
        """Update conversation state with new filter information."""
        state = self._states.get(pending_id)
        if not state:
            return None
            
        # Update applied filters
        state.applied_filters.update(filter_updates)
        
        if increment_step:
            state.conversation_step += 1
            
        # Check if we have enough information to stop refining
        state.needs_refinement = self._should_continue_refinement(state)
        
        return state

    def remove_state(self, pending_id: str) -> None:
        """Remove conversation state when conversation is complete."""
        self._states.pop(pending_id, None)

    def _should_continue_refinement(self, state: ConversationState) -> bool:
        """Determine if conversation needs more refinement."""
        applied = state.applied_filters
        
        # If we have category, budget, and brand - that's usually enough
        has_category = "category" in applied or state.detected_category
        has_budget = "budget" in applied
        has_brand = "brand" in applied
        
        # Basic heuristic: need at least 2 out of 3 key filters
        filter_count = (
            (1 if has_category else 0) + 
            (1 if has_budget else 0) + 
            (1 if has_brand else 0)
        )
        
        # Stop refining if we have enough filters OR too many steps
        return filter_count < 2 and state.conversation_step < 3

    def get_missing_filters(self, state: ConversationState) -> List[str]:
        """Get list of filters that haven't been applied yet."""
        possible_filters = ["budget", "brand", "technology"]
        applied = state.applied_filters
        
        missing = []
        for filter_type in possible_filters:
            if filter_type not in applied:
                missing.append(filter_type)
                
        return missing

    def format_applied_filters_summary(self, state: ConversationState) -> str:
        """Create human-readable summary of applied filters."""
        applied = state.applied_filters
        parts = []
        
        if state.detected_category:
            parts.append(f"Category: {state.detected_category}")
            
        if "budget" in applied:
            budget = applied["budget"]
            if isinstance(budget, dict):
                if budget["max"] == float("inf"):
                    if budget["min"] > 0:
                        parts.append(f"Budget: €{budget['min']}+")
                    else:
                        parts.append("Budget: No preference")
                elif budget["min"] == 0:
                    parts.append(f"Budget: Under €{budget['max']}")
                else:
                    parts.append(f"Budget: €{budget['min']}-€{budget['max']}")
                    
        if "brand" in applied:
            brand = applied["brand"]
            if brand == "any":
                parts.append("Brand: No preference")
            else:
                parts.append(f"Brand: {brand}")
                
        if "technology" in applied:
            tech = applied["technology"]
            if tech == "any":
                parts.append("Technology: No preference")
            else:
                parts.append(f"Technology: {tech}")
                
        return "; ".join(parts) if parts else "No filters applied yet"

    def create_search_filters(self, state: ConversationState) -> Dict[str, Any]:
        """Convert conversation state to search filters for catalog."""
        filters = {}
        
        # Add category from detected or applied filters
        if state.detected_category:
            filters["category"] = state.detected_category
        elif "category" in state.applied_filters:
            filters["category"] = state.applied_filters["category"]
            
        # Add other filters directly
        for key in ["budget", "brand", "technology"]:
            if key in state.applied_filters:
                filters[key] = state.applied_filters[key]
                
        return filters
