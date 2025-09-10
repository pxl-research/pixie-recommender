# Step 4: Prepare delete patch for file removal

## Objective
Create a single patch that removes `pixie/core/mock_search.py` and (in a later step) the empty `repositories/` directory — do not commit.

## Prerequisites
- Step 3: verification that file is unused
- Git working tree clean or changes isolated

## Actions
1. Create a git branch locally if desired (but do not push or commit without approval).
2. Prepare a patch (apply_patch or `git rm` staged change) that removes `pixie/core/mock_search.py`.
3. Also include deletion of the empty `pixie/core/repositories/` directory if it's safe (directory removal may be represented by deleting contents; git removes empty dirs implicitly).
4. Keep the patch staged but do not finalize commit; save the diff output for review.

## Success Criteria
- A patch/diff is prepared and available for review.

## Next Step
Continue to: `./steps/05-delete-files-and-dir.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
