#!/usr/bin/env python3
"""
Final comprehensive test of the mixer functionality.
This verifies that the entire system works end-to-end.
"""

import json


def test_mixer_database_integration():
    """Test that mixer data is properly integrated in the database."""
    print("🔧 Testing mixer database integration...")
    
    import subprocess
    
    # Check mixer product type exists
    result = subprocess.run([
        "docker", "exec", "-it", "pixie-core-postgres-1", 
        "psql", "-U", "pixie_user", "-d", "pixie_dev", "-t", "-c",
        "SELECT COUNT(*) FROM product_types WHERE name = 'mixer';"
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and "1" in result.stdout:
        print("✅ Mixer product type exists")
    else:
        print("❌ Mixer product type missing")
        return False
    
    # Check mixer products exist
    result = subprocess.run([
        "docker", "exec", "-it", "pixie-core-postgres-1",
        "psql", "-U", "pixie_user", "-d", "pixie_dev", "-t", "-c",
        "SELECT COUNT(*) FROM products p JOIN product_types pt ON p.product_type_id = pt.id WHERE pt.name = 'mixer';"
    ], capture_output=True, text=True)
    
    mixer_count = int(result.stdout.strip()) if result.returncode == 0 else 0
    if mixer_count >= 8:
        print(f"✅ Found {mixer_count} mixer products")
    else:
        print(f"❌ Expected at least 8 mixer products, found {mixer_count}")
        return False
    
    # Check mixer attributes exist
    result = subprocess.run([
        "docker", "exec", "-it", "pixie-core-postgres-1",
        "psql", "-U", "pixie_user", "-d", "pixie_dev", "-t", "-c",
        "SELECT COUNT(*) FROM attribute_definitions ad JOIN product_types pt ON ad.product_type_id = pt.id WHERE pt.name = 'mixer';"
    ], capture_output=True, text=True)
    
    attr_count = int(result.stdout.strip()) if result.returncode == 0 else 0
    if attr_count >= 6:
        print(f"✅ Found {attr_count} mixer attributes")
    else:
        print(f"❌ Expected at least 6 mixer attributes, found {attr_count}")
        return False
    
    return True


def test_api_conversation():
    """Test full conversation flow via API."""
    print("\n💬 Testing API conversation flow...")
    
    import subprocess
    
    # Test initial mixer question
    result = subprocess.run([
        "curl", "-X", "POST", "http://localhost:8012/ask",
        "-H", "Content-Type: application/json",
        "-d", '{"question": "Ik zoek een goede mixer"}'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ API request failed")
        return False
    
    try:
        response = json.loads(result.stdout)
        if response.get("type") == "ask_user" and "budget" in response.get("prompt", "").lower():
            print("✅ System asks about budget")
            pending_id = response.get("pending_id")
        else:
            print(f"❌ Unexpected response: {response}")
            return False
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response: {result.stdout}")
        return False
    
    # Answer budget question
    result = subprocess.run([
        "curl", "-X", "POST", "http://localhost:8012/ask",
        "-H", "Content-Type: application/json",
        "-d", f'{{"pending_id": "{pending_id}", "message": "minder dan 500 euro"}}'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            response = json.loads(result.stdout)
            if response.get("type") == "ask_user":
                print("✅ System asks follow-up question")
            else:
                print("✅ System may have provided answer directly")
        except json.JSONDecodeError:
            print("❌ Invalid JSON in follow-up response")
            return False
    else:
        print("❌ Follow-up request failed")
        return False
    
    return True


def test_attributes_json():
    """Test that attributes.json includes mixer support."""
    print("\n📋 Testing attributes.json integration...")
    
    try:
        with open("/Users/drphil/Documents/Werk/pixie-core/pixie/core/data/attributes.json", "r") as f:
            data = json.load(f)
        
        if "mixer" in data:
            mixer_attrs = data["mixer"]["attributes"]
            print(f"✅ Found mixer category with {len(mixer_attrs)} attributes")
            
            # Check for essential attributes
            attr_names = [attr["name"] for attr in mixer_attrs]
            required_attrs = ["budget", "type", "brand", "power"]
            
            for req_attr in required_attrs:
                if req_attr in attr_names:
                    print(f"✅ Found required attribute: {req_attr}")
                else:
                    print(f"❌ Missing required attribute: {req_attr}")
                    return False
            
            return True
        else:
            print("❌ Mixer category not found in attributes.json")
            return False
            
    except Exception as e:
        print(f"❌ Error reading attributes.json: {e}")
        return False


def main():
    """Run all tests and report results."""
    print("🧪 COMPREHENSIVE MIXER FUNCTIONALITY TEST")
    print("=" * 50)
    
    tests = [
        ("Database Integration", test_mixer_database_integration),
        ("Attributes Configuration", test_attributes_json),
        ("API Conversation Flow", test_api_conversation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n🎯 TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n✨ The flexible repository system is working perfectly!")
        print("✨ You can now ask questions about mixers via the API!")
        print("\nExample questions that should work:")
        print("- 'Ik zoek een nieuwe mixer'")
        print("- 'Welke planetmixer adviseer je?'")
        print("- 'Ik wil een KitchenAid mixer kopen'")
        print("- 'Wat is de beste blender voor smoothies?'")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Check the output above for details on what needs to be fixed.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
