---
name: self-review
description: Final quality checklist for reviewing your own diff before reporting a task as complete. Use at the end of every code change.
---

# Self-Review

Read your full diff, then walk through this checklist. Fix every problem you find before reporting the work as done.

## Correctness and scope

- [ ] The change solves the requested problem and nothing unrelated slipped in.
- [ ] No accidental edits (stray debug output, formatting churn in untouched code, leftover files).
- [ ] Refactors preserved behavior unless the task asked for a change.

## Duplication and reuse

- [ ] No logic copy-pasted between call sites.
- [ ] Nothing reimplements something that already exists in the codebase.
- [ ] No near-duplicate helpers, and no wrappers that only rename.
- [ ] Each rule or concept has one source of truth.

## Structure

- [ ] New code sits in the module that logically owns it. No module turned into a catch-all.
- [ ] Responsibilities stay separated (UI / state / domain / API / persistence / infra).
- [ ] Abstractions are proportional to the real complexity. No speculative generalization, no chains of tiny helpers.
- [ ] Interfaces stay minimal and explicit. Changed interfaces have every caller updated and the old path removed.

## Robustness

- [ ] Errors fail explicitly with context. Nothing is swallowed, and original causes are preserved.
- [ ] External input is validated at boundaries.
- [ ] Resource lifecycles (files, handles, workers, connections, devices) are explicitly cleaned up.
- [ ] No new global mutable state and no hidden mutation.
- [ ] No hard-coded config values and no secrets.

## Cleanup

- [ ] Dead code, unused imports, stale comments, and obsolete compatibility paths made redundant by the change are removed.
- [ ] No commented-out code.
- [ ] Comments explain *why*, not *what*.
- [ ] Docs are updated if behavior, config, setup, or public interfaces changed.

## Verification

- [ ] The change was test-driven: every new behavior has a test that was seen failing before the implementation (see `write-tests`).
- [ ] Web apps: the backend/frontend split is intact. No cross-imports, and no business logic in the frontend.
- [ ] Tests, lint, type checks, and formatting were run, and the results are reported accurately.

## Final standard

Would another engineer find this easy to understand, test, and extend? If not, simplify before finishing.
