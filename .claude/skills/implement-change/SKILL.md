---
name: implement-change
description: Disciplined workflow for implementing a feature, bug fix, or behavior change. Use whenever you are about to write or modify code for a task, before editing any files.
---

# Implement a Change

Follow these steps in order. The engineering rules in CLAUDE.md apply throughout.

## 0. Start a branch

- Make sure `main` is clean and up to date, then create the work branch: `git switch -c feature/<slug>` (or `fix/<slug>` for bug fixes).
- All commits for this task go on that branch. Never commit to `main` directly.

## 1. Understand the existing design

- Read the relevant code paths, interfaces, tests, and existing patterns before editing.
- Note the project's conventions (formatter, linter, naming, layout, config mechanism, error style).
- For a web app, decide whether the change belongs in `backend/`, `frontend/`, or both (an API change touches both sides through the API contract only).

## 2. Find the ownership boundary

- Decide which module logically owns the behavior (UI, state, domain, API, persistence, or infrastructure).
- If no module fits cleanly, or the owner is already a catch-all, consider improving the boundary first (see the `refactor` skill) instead of patching on top.

## 3. Search for reuse

Before writing new code, search for existing functions, classes, utilities, types, constants, and abstractions. Answer each question:

1. Does equivalent logic already exist?
2. Can an existing function or module be generalized cleanly?
3. Will this logic have more than one caller?
4. Would extracting it improve clarity, or just add indirection?

Never write a second implementation of logic that already exists.

## 4. Write a failing test first

Follow the `write-tests` skill. Before writing implementation code, write a test that states the new behavior (or reproduces the bug). Run it and confirm it fails for the expected reason.

## 5. Implement the simplest coherent solution

- Write just enough code to make the failing test pass, then refactor while the tests stay green.
- Make the smallest change that solves the problem properly, not the smallest diff that makes it pass.
- Validate external input at the boundary and keep side effects out of core logic.
- Put new configuration values in the existing config mechanism, never inline.

## 6. Consolidate duplication

- If your change introduced or exposed duplicated validation, parsing, mapping, serialization, or business rules, unify them into one authoritative implementation.
- If you changed an interface, update every caller and remove the obsolete path.

## 7. Verify

Run whatever the project provides: tests, linting, type checks, and formatting. Report failures honestly and never weaken a valid test to get a pass.

## 8. Self-review

Run the `self-review` skill on the branch diff (`git diff main...HEAD`) before reporting the work as done.

## 9. Merge

Only once steps 7 and 8 are clean:

- `git switch main`, `git merge --no-ff feature/<slug>` (keeps the feature as one visible unit in history), then `git branch -d feature/<slug>`.
- If `main` moved while you worked, merge `main` into the branch first, re-run the checks, then merge.
- Report the merge commit and what was verified.
