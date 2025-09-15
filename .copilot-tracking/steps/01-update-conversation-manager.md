# Step 1: Update ConversationLoopManager Initialization

## Objective

Update the ConversationLoopManager to automatically use Azure LLMs instead of requiring dependency injection, simplifying the initialization process.

## Prerequisites

- Azure LLM wrapper classes are implemented (from previous migration steps)
- azure_llm_set.create_azure_llm_set() factory function exists

## Actions

1. Modify ConversationLoopManager.__init__ to remove LLM parameters and create Azure LLMs internally
2. Replace dependency injection with direct factory calls to azure_llm_set.create_azure_llm_set()
3. Update the Pixie class to not pass LLM instances to ConversationLoopManager
4. Ensure RealSearchEngine is still properly initialized

## Success Criteria

- ConversationLoopManager creates its own Azure LLM instances
- No external LLM dependencies required for initialization
- Pixie class initialization remains simple
- Existing conversation flow still works

## Next Step

Continue to: 02-add-error-handling.md

## Cleanup

When this step is completed successfully, this file can be deleted.
