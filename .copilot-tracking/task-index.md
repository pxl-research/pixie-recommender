# Task: MockSearchEngine → RealSearchEngine cleanup

## Goal
Voltooien van de overgang van `MockSearchEngine` naar `RealSearchEngine` door de resterende cleanup uit te voeren: verwijderen van `pixie/core/mock_search.py`, bijwerken van verouderde comments, verwijderen van lege directory `pixie/core/repositories/`, en zorgen dat linters (`ruff`, `black`) en tests (`pytest`) green zijn.

## Progress Tracking
- [ ] Step 1: Repo-wide search for `mock_search` → `./steps/01-repo-search.md`
- [ ] Step 2: Update test comment in `tests/test_conversation_loop.py` → `./steps/02-update-test-comment.md`
- [ ] Step 3: Verify `pixie/core/mock_search.py` is unused → `./steps/03-verify-unused.md`
- [ ] Step 4: Prepare delete patch for file removal → `./steps/04-prepare-delete-patch.md`
- [ ] Step 5: Delete `mock_search.py` and remove empty `repositories/` dir → `./steps/05-delete-files-and-dir.md`
- [ ] Step 6: Run `ruff --fix` and `black` on changed files → `./steps/06-run-ruff-black.md`
- [ ] Step 7: Run test suite (`pytest`) and fix failures → `./steps/07-run-tests.md`
- [ ] Step 8: Final lint/format/type-check and confirm clean → `./steps/08-final-lint-typecheck.md`
- [ ] Step 9: Produce patchset summary and test/lint results for review → `./steps/09-produce-patchset.md`
- [ ] Step 10: Await explicit approval to commit and push → `./steps/10-await-approval.md`

## Current Status
**Next Step**: `./steps/01-repo-search.md`

## Completion
When all steps are checked off and their files deleted, delete this index file.
