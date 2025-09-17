#!/usr/bin/env python3
"""
Test script to specifically test the category filtering fix.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pixie.core.conversation.simplified_conversation_manager import SimplifiedConversationManager
from pixie.core.conversation.flow_config import ConversationFlowManager
from pixie.core.conversation.llm_orchestrator import MockLLMOrchestrator

def mock_search_function(query: str, context: dict | None = None):
    """Mock search function for testing - now checks category properly."""
    category = None
    if context and isinstance(context, dict):
        category = context.get("category")
    
    print(f"🔍 Search called: query='{query}', category='{category}'")
    
    # Mock different categories with different results
    if category == "laptops":
        return [
            {"id": 1, "name": "MacBook Pro", "price": 2299, "category": "laptops"},
            {"id": 2, "name": "Dell XPS 13", "price": 1499, "category": "laptops"},
        ]
    elif category == "printers":
        return [
            {"id": 3, "name": "HP LaserJet Pro", "price": 299, "category": "printers"},
            {"id": 4, "name": "Canon PIXMA", "price": 199, "category": "printers"},
        ]
    else:
        # If no category or unknown category, return all products (old buggy behavior)
        print(f"⚠️  No category filter - returning ALL products!")
        return [
            {"id": 1, "name": "MacBook Pro", "price": 2299, "category": "laptops"},
            {"id": 2, "name": "Dell XPS 13", "price": 1499, "category": "laptops"},
            {"id": 3, "name": "HP LaserJet Pro", "price": 299, "category": "printers"},
            {"id": 4, "name": "Canon PIXMA", "price": 199, "category": "printers"},
            {"id": 5, "name": "KitchenAid Mixer", "price": 399, "category": "mixers"},
        ]

def test_direct_search():
    """Test the _generate_direct_results method to see if category is passed correctly."""
    print("=== Testing Direct Search Category Filtering ===\n")
    
    # Initialize components
    flow_manager = ConversationFlowManager()
    orchestrator = MockLLMOrchestrator()
    conversation_manager = SimplifiedConversationManager(
        search_fn=mock_search_function,
        flow_manager=flow_manager,
        llm_orchestrator=orchestrator
    )
    
    print("Testing laptop search...")
    try:
        result = conversation_manager._generate_direct_results(
            question="Ik zoek een laptop",
            category="laptops"
        )
        print(f"Result type: {result.type}")
        if result.text:
            print(f"Results preview: {result.text[:200]}...")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("Testing printer search...")
    try:
        result = conversation_manager._generate_direct_results(
            question="Ik zoek een printer", 
            category="printers"
        )
        print(f"Result type: {result.type}")
        if result.text:
            print(f"Results preview: {result.text[:200]}...")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_search()
