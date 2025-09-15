# Step 4: Update Tests for Azure API Calls

## Objective

Update test suite to work with real Azure API calls while maintaining fallback to mocks when environment variables are not available.

## Prerequisites

- Previous step completed: 03-update-environment-config.md
- Environment configuration is updated

## Actions

1. Modify test fixtures to detect Azure environment variables
2. Create conditional logic: use Azure LLMs if env vars present, fallback to mocks otherwise
3. Update test expectations for real API responses vs mock responses
4. Ensure tests pass in both Azure and mock modes

## Success Criteria

- Tests automatically detect and use Azure LLMs when configured
- Graceful fallback to mock LLMs when Azure vars not set
- Test suite passes in both modes
- No hardcoded dependencies on specific LLM implementations

## Next Step

Continue to: 05-test-complete-flow.md

## Cleanup

When this step is completed successfully, this file can be deleted.
