#!/usr/bin/env python3
"""
Test script to verify mixer questions work end-to-end via the API.
"""


import requests


def test_mixer_conversation():
    """Test a full mixer conversation flow via the API."""
    print("🤖 Testing mixer conversation via API...")

    api_base = "http://localhost:8012"

    try:
        # Test 1: Ask about mixers
        print("\n1. Testing initial mixer question...")
        response = requests.post(
            f"{api_base}/ask",
            json={"message": "Ik zoek een nieuwe mixer voor in de keuken"},
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response type: {data.get('type')}")
            print(f"✅ Prompt: {data.get('prompt', '')[:100]}...")

            if data.get("type") == "ask_user":
                pending_id = data.get("pending_id")
                print(f"✅ Got pending_id: {pending_id}")

                # Test 2: Answer budget question
                print("\n2. Testing budget response...")
                response2 = requests.post(
                    f"{api_base}/ask",
                    json={"pending_id": pending_id, "message": "minder dan 400 euro"},
                )

                if response2.status_code == 200:
                    data2 = response2.json()
                    print(f"✅ Response type: {data2.get('type')}")
                    print(f"✅ Prompt: {data2.get('prompt', '')[:100]}...")

                    # Test 3: Answer type question
                    if data2.get("type") == "ask_user":
                        print("\n3. Testing type response...")
                        response3 = requests.post(
                            f"{api_base}/ask",
                            json={"pending_id": pending_id, "message": "planetmixer"},
                        )

                        if response3.status_code == 200:
                            data3 = response3.json()
                            print(f"✅ Response type: {data3.get('type')}")
                            print(f"✅ Content: {data3.get('prompt', '')[:200]}...")

                            # Continue with a few more questions
                            if data3.get("type") == "ask_user":
                                print("\n4. Testing brand response...")
                                response4 = requests.post(
                                    f"{api_base}/ask",
                                    json={
                                        "pending_id": pending_id,
                                        "message": "KitchenAid",
                                    },
                                )

                                if response4.status_code == 200:
                                    data4 = response4.json()
                                    print(f"✅ Response type: {data4.get('type')}")

                                    if data4.get("type") == "answer":
                                        print("🎉 Got final answer!")
                                        print(
                                            f"Answer: {data4.get('text', '')[:200]}..."
                                        )
                                    else:
                                        print(
                                            f"Continue with: {data4.get('prompt', '')[:100]}..."
                                        )

        else:
            print(f"❌ API request failed: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Is the server running on localhost:8012?")
    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_api_health():
    """Test if the API is running."""
    print("🏥 Testing API health...")

    try:
        response = requests.get("http://localhost:8012/health")
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"⚠️ API returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API is not reachable")
        return False


if __name__ == "__main__":
    if test_api_health():
        test_mixer_conversation()
    else:
        print("⚠️ API not available, skipping conversation test")
        print("Start the API with: docker compose -f docker-compose.dev.yml up")
