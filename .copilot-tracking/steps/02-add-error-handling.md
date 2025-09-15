# Step 2: Add Error Handling to Azure LLM Calls

## Objective

Add basic error handling to Azure LLM calls to prevent crashes and provide meaningful error messages.

## Prerequisites

- Previous step completed: 01-update-conversation-manager.md
- Azure LLM classes are properly initialized

## Actions

1. Add try/catch blocks around all Azure LLM method calls in ConversationLoopManager
2. Log exceptions with appropriate log levels (error for failures, info for retries)
3. Return appropriate AskResponse error types when LLM calls fail
4. Ensure graceful fallback behavior (don't crash the conversation flow)

## Success Criteria

- Azure LLM calls are wrapped in error handling
- Exceptions are logged but don't crash the application
- Error responses are returned in appropriate AskResponse format
- Conversation flow continues even when LLM calls fail

## Next Step

Continue to: 03-update-environment-config.md

## Cleanup

When this step is completed successfully, this file can be deleted.
