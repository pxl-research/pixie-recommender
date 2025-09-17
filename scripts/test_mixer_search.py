#!/usr/bin/env python3
"""
Test script to verify that the conversation system can handle mixer questions.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pixie.core.search import SearchEngine


def test_mixer_search():
    """Test if the search engine can find mixers."""
    print("🔍 Testing mixer search functionality...")
    
    engine = SearchEngine()
    
    # Test simple search for mixers
    print("\n1. Testing simple mixer search...")
    results = engine.search("SELECT * FROM products WHERE name ILIKE '%mixer%'", None, "mixer")
    print(f"Found {len(results)} mixer products")
    
    for result in results[:3]:  # Show first 3
        print(f"  - {result['name']} ({result['brand']}) - €{result['price']:.2f}")
    
    # Test search with context
    print("\n2. Testing search with context...")
    context = {"category": "mixer"}
    results = engine.search("SELECT * FROM products WHERE brand = 'KitchenAid'", context, "mixer")
    print(f"Found {len(results)} KitchenAid products")
    
    # Test category-based search
    print("\n3. Testing category-based search...")
    results = engine.search("SELECT * FROM products", None, "mixer")
    mixer_results = [r for r in results if "mixer" in r.get("name", "").lower() or "blender" in r.get("name", "").lower()]
    print(f"Found {len(mixer_results)} mixer/blender products from category search")
    
    return True


def test_attributes_json():
    """Test if attributes.json includes mixer attributes."""
    print("\n📋 Testing attributes.json for mixer support...")
    
    from pixie.core.data.attributes import get_attributes_for_category
    
    # Check if mixer category exists in attributes
    try:
        mixer_attrs = get_attributes_for_category("mixer")
        if mixer_attrs:
            print(f"✅ Found {len(mixer_attrs)} attributes for mixer category")
            for attr in mixer_attrs:
                print(f"  - {attr.get('name', 'Unknown')}: {attr.get('question', 'No question')}")
        else:
            print("⚠️ No attributes found for mixer category in attributes.json")
            print("This means we need to update the attributes.json file")
    except Exception as e:
        print(f"⚠️ Could not load mixer attributes: {e}")
        print("This might be expected if attributes.json doesn't include mixers yet")


if __name__ == "__main__":
    try:
        test_mixer_search()
        test_attributes_json()
        print("\n🎉 Mixer search tests completed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
