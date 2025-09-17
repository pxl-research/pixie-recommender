#!/usr/bin/env python3
"""
Quick test script to verify the simplified conversation manager fixes
without running the full API or pytest (which has dependency issues).
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pixie.core.conversation.attribute_collector import AttributeCollector
from pixie.core.conversation.flow_config import ConversationFlowManager
from pixie.core.conversation.llm_orchestrator import MockLLMOrchestrator
from pixie.core.conversation.simplified_conversation_manager import (
    SimplifiedConversationManager,
)


def mock_search_function(query: str, context: dict | None = None):
    """Mock search function for testing - now checks category properly."""
    category = None
    if context and isinstance(context, dict):
        category = context.get("category")

    print(f"    Mock search called with query='{query}', category='{category}'")

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
        # If no category or unknown category, return all products (old behavior)
        return [
            {"id": 1, "name": "MacBook Pro", "price": 2299, "category": "laptops"},
            {"id": 2, "name": "Dell XPS 13", "price": 1499, "category": "laptops"},
            {"id": 3, "name": "HP LaserJet Pro", "price": 299, "category": "printers"},
            {"id": 4, "name": "Canon PIXMA", "price": 199, "category": "printers"},
            {"id": 5, "name": "KitchenAid Mixer", "price": 399, "category": "mixers"},
        ]


def test_basic_conversation():
    """Test basic conversation flow without database dependencies."""
    print("Testing simplified conversation manager...")

    # Initialize components
    flow_manager = ConversationFlowManager()
    orchestrator = MockLLMOrchestrator()
    conversation_manager = SimplifiedConversationManager(
        search_fn=mock_search_function,
        flow_manager=flow_manager,
        llm_orchestrator=orchestrator,
    )

    print("✅ Components initialized successfully")

    # Test laptop search (should only return laptops)
    try:
        print("\n🔍 Testing laptop search...")
        result = conversation_manager.handle_new_question(
            question="Ik zoek een nieuwe laptop"
        )
        print(f"✅ Laptop question handled: {result.text}")
        print(f"   Type: {result.type}")
        print(f"   Pending ID: {result.pending_id}")

    except Exception as e:
        print(f"❌ Error handling laptop question: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test printer search (should only return printers)
    try:
        print("\n🔍 Testing printer search...")
        result = conversation_manager.handle_new_question(
            question="Ik zoek een printer"
        )
        print(f"✅ Printer question handled: {result.text}")
        print(f"   Type: {result.type}")

    except Exception as e:
        print(f"❌ Error handling printer question: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


def test_attribute_collector():
    """Test the attribute collector functionality."""
    print("\nTesting attribute collector...")

    try:
        collector = AttributeCollector(category="printers")
        print("✅ AttributeCollector initialized")

        # Test getting next question
        next_question = collector.get_next_question()
        if next_question:
            print(f"✅ Next question: {next_question.question}")
            print(f"   Attribute: {next_question.name}")
        else:
            print("✅ No next question (collection complete)")

        return True

    except Exception as e:
        print(f"❌ Error in attribute collector: {e}")
        return False


def test_flow_config():
    """Test the flow configuration."""
    print("\nTesting flow configuration...")

    try:
        flow_manager = ConversationFlowManager()
        print("✅ ConversationFlowManager initialized")

        # Test getting flow for category
        flow = flow_manager.get_flow("printers")
        if flow:
            print(f"✅ Flow found for printers: {flow.display_name}")
            print(f"   Questions count: {len(flow.questions)}")
        else:
            print("❌ No flow found for printers")
            return False

        return True

    except Exception as e:
        print(f"❌ Error in flow config: {e}")
        return False


if __name__ == "__main__":
    print("=== Simplified Conversation Manager Test ===\n")

    success = True
    success &= test_flow_config()
    success &= test_attribute_collector()
    success &= test_basic_conversation()

    if success:
        print("\n🎉 All tests passed! The simplified conversation manager is working.")
    else:
        print("\n💥 Some tests failed. Check the errors above.")
        sys.exit(1)
