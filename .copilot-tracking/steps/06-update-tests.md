# Step 6: Update Tests

## Objective
Update all test files to use Azure OpenAI LLMs instead of mock LLMs, ensuring tests work with real API calls.

## Prerequisites
- Previous step completed: Step 5 - Environment configuration updated
- Required tools/dependencies: Azure LLM classes and factory available
- Test environment with proper Azure OpenAI credentials

## Actions
1. Update all test files that import create_mock_llm_set to use create_azure_llm_set
2. Replace mock LLM instantiations with Azure LLM instantiations in tests
3. Update test assertions to work with real Azure LLM responses instead of hardcoded mock responses
4. Add test environment configuration for Azure OpenAI credentials
5. Update test_mock_llms.py to test Azure LLMs instead (or rename file)
6. Ensure tests can run with or without network connectivity (skip if no credentials)
7. Add integration tests that verify end-to-end Azure LLM functionality
8. Update any test fixtures or helpers that depend on mock LLM behavior

## Success Criteria
- All tests pass with Azure LLM implementations
- Test suite can run against real Azure OpenAI APIs
- Tests properly handle network/API failures during testing
- Test coverage maintained for all LLM functionality
- Integration tests verify complete Azure LLM workflow
- Test environment properly configured for Azure API access

## Next Step
Continue to: `07-cleanup-mock-files.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
