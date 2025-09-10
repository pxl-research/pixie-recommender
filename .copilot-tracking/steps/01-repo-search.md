# Step 1: Repo-wide search for `mock_search`

## Objective
Find all references (imports, comments, tests) to `mock_search` or `MockSearchEngine` so we can confirm it's safe to remove.

## Prerequisites
- Repo root available: `/Users/drphil/Documents/Werk/pixie-core`
- Tools: shell with `grep`/`rg` or IDE search

## Actions
1. Run a repo-wide search for `mock_search`, `MockSearchEngine`, and `mock_search.py`.
2. Record every file path and a one-line excerpt where it appears.
3. Categorize each hit as: import/usage, test, comment, or other.
4. If any code imports or instantiates `MockSearchEngine`, mark it as "requires manual change" and list files.

## Success Criteria
- A list of all hits is saved (copy in the issue or as a comment in task-index).
- No runtime imports found except possibly in commented or test-only code.

## Next Step
Continue to: `./steps/02-update-test-comment.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
