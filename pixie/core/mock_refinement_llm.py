raise ImportError(
    "Mock LLMs have been removed. Use the Azure LLM implementations in pixie.core.azure_* or"
    " configure AZURE_OPENAI_* env vars so create_mock_llm_set returns Azure LLMs."
)
