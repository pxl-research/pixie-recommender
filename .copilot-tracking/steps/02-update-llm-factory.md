# Step 2: Update LLM Factory/Creation Logic

## Objective
Replace the mock_llm_set.py with an azure_llm_set.py that creates Azure OpenAI LLM instances instead of mock ones.

## Prerequisites
- Previous step completed: Step 1 - Azure LLM wrapper classes created
- Required tools/dependencies: New Azure LLM classes available
- Environment variables for Azure OpenAI configured

## Actions
1. Create new azure_llm_set.py file based on existing mock_llm_set.py structure
2. Implement create_azure_llm_set() function that returns tuple of Azure LLM instances
3. Function should read environment variables for Azure configuration
4. Instantiate AzureRelevanceLLM, AzureSQLLLM, AzureRefinementLLM with env config
5. Add error handling for missing environment variables
6. Add error handling for Azure authentication failures
7. Update imports in any files that currently use create_mock_llm_set()
8. Ensure return type annotations match the new Azure LLM classes

## Success Criteria
- azure_llm_set.py file created with create_azure_llm_set() function
- Function successfully creates and returns tuple of Azure LLM instances
- Proper error handling for configuration and authentication issues
- All imports updated from mock to azure LLM set
- Function can be called without errors when environment is properly configured

## Next Step
Continue to: `03-update-conversation-manager.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
