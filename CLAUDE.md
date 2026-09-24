# Engineering Rules

These rules apply to every code change. Procedures live in skills:
`implement-change` (any feature or fix), `refactor` (structural changes), `write-tests`, and `self-review` (run before declaring work done).

## Core principles

- Simple, readable, maintainable code over clever code. Optimize for long-term maintainability, not just passing the current task.
- Reuse and extend existing code before creating new abstractions. One authoritative implementation per rule or concept.
- Make the smallest coherent change that solves the problem properly.
- Keep responsibilities separated: UI, state, domain logic, API, persistence, infrastructure, and tests don't mix without a clear reason.
- Leave the codebase at least as coherent as you found it.
- **Test-driven.** Write a failing test before the code that makes it pass: red → green → refactor. See `write-tests`.

## Version control

- `main` is always releasable. Never commit directly to it.
- Every feature or fix is developed on its own branch cut from `main` (`feature/<slug>` or `fix/<slug>`), with small focused commits.
- Merge back into `main` only after the work is complete: tests, lint and type checks pass, the `self-review` checklist is done, and the change has been verified in the running app where applicable. Delete the branch after merging.
- Never force-push `main` or rewrite shared history.

## Web app layout

Web apps keep a firm split into two top-level directories:

- `backend/`: Python with FastAPI or Flask. Owns domain logic, persistence, and device/system access. Has its own dependency file, config, and tests (pytest).
- `frontend/`: npm, React, and TypeScript. Owns UI and client state only. Has its own `package.json`, config, and tests.

The two talk only over the HTTP/WebSocket API. Neither imports the other's code. Keep API request/response schemas defined in the backend and mirror them explicitly in typed frontend API clients. Don't put business logic in the frontend.

## Architecture

- Modular files with clear ownership. Don't let any module become a catch-all.
- Small, explicit, stable public interfaces. Don't leak internals across module boundaries.
- Dependency injection and explicit data flow over hidden coupling or global state.
- Keep domain logic independent of frameworks and transport layers where practical.
- Existing structure isn't sacred. If a feature exposes a weak boundary, improve the boundary instead of patching on top. Prefer incremental improvements to rewrites.

## Code style

- Follow the project's formatter, linter, naming, and directory conventions.
- One clear responsibility per function. Use domain-oriented names (never `handle_data`, `process_item`, `helper`).
- Keep parameter lists small; group related values into structured inputs.
- Don't write a helper for a trivial one-liner used once, a wrapper that only renames, or near-duplicate helpers. Extract only when it removes duplication, isolates complexity, improves testability, or names an important concept.
- Prefer pure functions for transformations and calculations; prefer early returns over deep nesting.
- Keep abstractions proportional to real complexity. No speculative generalization.
- Comments explain *why*, constraints, invariants, and non-obvious decisions, not what the code does. No commented-out code.

## Types and data

- Use typed models for data with a stable schema, not loose dicts/objects. Reuse existing domain models; don't create parallel representations.
- Keep conversions between representations explicit and localized.
- Validate at system boundaries, not repeatedly inside internal code.
- Model finite states with enums, literals, or tagged unions.

## Errors

- Fail explicitly with useful context. Never silently swallow exceptions.
- Catch only to recover, translate, enrich, or clean up. Preserve the original cause when re-raising.
- Don't use exceptions for ordinary control flow.

## State, side effects, concurrency

- Clear state ownership, minimal global mutable state, no hidden mutation.
- Keep I/O, network, filesystem, DB, and device access separate from core logic.
- Make lifecycle and cleanup explicit for files, sockets, workers, GPU memory, DB connections, and device handles.
- Use concurrency only for a real benefit. Make cancellation, timeouts, retries, and cleanup explicit. No unmanaged fire-and-forget tasks. Don't mix blocking and async code carelessly.

## Configuration and dependencies

- Use the project's existing config mechanism. Don't scatter values or add a second config system.
- Don't hard-code values that represent configuration, policy, shared constants, or domain concepts.
- Never commit secrets, tokens, credentials, or private keys.
- Prefer the stdlib or existing dependencies. Add a new one only for clear value, never one that overlaps an existing library. Wrap vendor-specific behavior behind project-owned interfaces.

## Performance

- Correctness and clarity first. Optimize measured bottlenecks, not hypothetical ones.
- Avoid obvious waste: repeated work, duplicate queries, repeated model loading, redundant serialization, per-item overhead where a clear batched path exists.
- Cache only when lifecycle, invalidation, and memory cost are understood.

## Interfaces and cleanup

- When an interface changes, update all callers and remove the old path. Don't keep parallel old and new flows unless backward compatibility is part of the contract.
- Remove dead code, unused imports, stale comments, and abandoned compatibility paths made obsolete by your change. Don't do unrelated broad cleanup.
- No "temporary" shortcuts that create a second code path or source of truth.
- Update docs when behavior, configuration, setup, or public interfaces change.
