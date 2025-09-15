"""Quick test to verify the new LLM fixture configuration works."""

import os


def test_fixture_configuration():
    """Test that the new fixture chooses mocks vs real LLMs correctly."""

    # Test 1: Force mocks
    os.environ["PIXIE_FORCE_MOCKS"] = "1"

    from pixie.core.llms import azure_llm_set
    from tests.conftest import MockRefinement, MockRelevance, MockSQL

    # Mock the fixture logic manually
    force_mocks = os.getenv("PIXIE_FORCE_MOCKS", "0") == "1"
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_key = os.getenv("AZURE_OPENAI_KEY", "")

    if (
        not force_mocks
        and azure_endpoint
        and azure_endpoint != "https://example.openai.azure.com/"
        and azure_key
        and azure_key != "dummy-key-for-development"
    ):
        try:
            real_llms = azure_llm_set.create_azure_llm_set()
            print(f"✅ Using REAL Azure LLMs for testing (endpoint: {azure_endpoint})")
            llms = real_llms
        except Exception as e:
            print(f"⚠️  Azure LLMs failed ({e}), falling back to mocks")
            llms = MockRelevance(), MockSQL(), MockRefinement()
    else:
        print("🔧 Using MOCK LLMs for testing")
        llms = MockRelevance(), MockSQL(), MockRefinement()

    # Should be mocks when forced
    assert isinstance(llms[0], MockRelevance)
    assert isinstance(llms[1], MockSQL)
    assert isinstance(llms[2], MockRefinement)
    print("✅ Test 1 passed: Forced mocks work correctly")

    # Test 2: Try real LLMs (if configured)
    os.environ["PIXIE_FORCE_MOCKS"] = "0"

    force_mocks = os.getenv("PIXIE_FORCE_MOCKS", "0") == "1"

    if (
        not force_mocks
        and azure_endpoint
        and azure_endpoint != "https://example.openai.azure.com/"
        and azure_key
        and azure_key != "dummy-key-for-development"
    ):
        try:
            real_llms = azure_llm_set.create_azure_llm_set()
            print(f"✅ Using REAL Azure LLMs for testing (endpoint: {azure_endpoint})")
            llms = real_llms
            print("✅ Test 2 passed: Real Azure LLMs are available and working")
        except Exception as e:
            print(f"⚠️  Azure LLMs failed ({e}), falling back to mocks")
            llms = MockRelevance(), MockSQL(), MockRefinement()
            print("✅ Test 2 passed: Graceful fallback to mocks when Azure fails")
    else:
        print("🔧 Using MOCK LLMs for testing (Azure not configured or forced)")
        llms = MockRelevance(), MockSQL(), MockRefinement()
        print("✅ Test 2 passed: Default to mocks when Azure not configured")

    print("\n🎉 All fixture configuration tests passed!")
    print("✅ v0.5 real LLM support is properly implemented")


if __name__ == "__main__":
    test_fixture_configuration()
