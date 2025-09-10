# Step 1: Create Azure LLM Wrapper Classes

## Objective
Create specialized Azure OpenAI LLM classes for Relevance, SQL, and Refinement tasks that extend the existing AzureOpenAILLM base class.

## Prerequisites
- Previous step completed: N/A (first step)
- Required tools/dependencies: Existing AzureOpenAILLM class available
- Environment variables configured for Azure OpenAI

## Actions
1. Analyze existing mock LLM interfaces (MockRelevanceLLM, MockSQLLLM, MockRefinementLLM)
2. Read the base AzureOpenAILLM implementation to understand structure
3. Create AzureRelevanceLLM class that implements is_relevant() method
4. Create AzureSQLLLM class that implements generate_sql() method  
5. Create AzureRefinementLLM class that implements refine_question() method
6. Each class should use specific prompts optimized for their task
7. Add appropriate error handling for Azure API failures in each class
8. Test that each class can be instantiated with environment variables

## Success Criteria
- Three new files created: azure_relevance_llm.py, azure_sql_llm.py, azure_refinement_llm.py
- Each class extends AzureOpenAILLM and implements required methods
- Classes use task-specific prompts for optimal performance
- Basic error handling implemented for API failures
- Classes can be imported and instantiated without errors

## Next Step
Continue to: `02-update-llm-factory.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
