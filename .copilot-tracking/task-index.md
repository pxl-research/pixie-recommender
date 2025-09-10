# Task: Migrate Mock LLMs to Azure OpenAI

## Goal
Replace all mock LLM implementations (MockRelevanceLLM, MockSQLLLM, MockRefinementLLM) with real Azure OpenAI LLM implementations using gpt-5-chat model. Update ConversationLoopManager to automatically use Azure LLMs and update all tests to work with real Azure API calls.

## Progress Tracking
- [ ] Step 1: Create Azure LLM wrapper classes → `./steps/01-create-azure-llm-wrappers.md`
 - [x] Step 1: Create Azure LLM wrapper classes → `./steps/01-create-azure-llm-wrappers.md`
- [ ] Step 2: Update LLM factory/creation logic → `./steps/02-update-llm-factory.md`
 - [x] Step 2: Update LLM factory/creation logic → `./steps/02-update-llm-factory.md`
- [ ] Step 3: Update ConversationLoopManager initialization → `./steps/03-update-conversation-manager.md`
- [ ] Step 4: Implement error handling → `./steps/04-implement-error-handling.md`
- [ ] Step 5: Update environment configuration → `./steps/05-update-environment-config.md`
- [ ] Step 6: Update tests → `./steps/06-update-tests.md`
 - [x] Step 7: Remove old mock LLM files → `./steps/07-cleanup-mock-files.md`
- [ ] Step 8: Test complete flow → `./steps/08-test-complete-flow.md`

## Current Status
**Next Step**: `./steps/03-update-conversation-manager.md`

## Completion
When all steps are checked off and their files deleted, delete this index file.
