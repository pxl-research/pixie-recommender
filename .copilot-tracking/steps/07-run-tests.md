# Step 7: Run test suite (`pytest`) and fix failures

## Objective
Run the full test suite locally and fix any failures introduced by cleanup.

## Prerequisites
- Steps 1-6 completed
- `pytest` available

## Actions
1. Run `pytest -q` at repo root.
2. If tests fail, open the failing tests and apply minimal fixes.
3. Re-run tests until green.

## Success Criteria
- All tests pass locally.

## Next Step
Continue to: `./steps/08-final-lint-typecheck.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
