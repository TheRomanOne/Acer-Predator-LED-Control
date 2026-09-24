# Claude Code Engineering Instructions

Follow these rules for every code change.

## Core Principles

- Prefer simple, readable, maintainable code over clever code.
- Reuse and extend existing code before creating new abstractions.
- Consolidate related logic instead of duplicating behavior across files.
- Keep responsibilities separated: UI, state, domain logic, API, persistence, infrastructure, and tests should not be mixed without a clear reason.
- Make the smallest coherent change that solves the problem properly.
- Optimize for long-term maintainability, not just making the current task pass.

## Understand Before Changing

Before implementing:

- Inspect the relevant code paths, interfaces, tests, and existing patterns.
- Identify where the behavior logically belongs.
- Search for existing functions, classes, utilities, types, constants, and abstractions that can be reused.
- Avoid introducing a second implementation of logic that already exists elsewhere.
- Preserve established project conventions unless there is a good architectural reason to improve them.

## Architecture

- Use modular files with clear ownership and purpose.
- Keep public interfaces small, explicit, and stable where practical.
- Prefer dependency injection and explicit data flow over hidden coupling or global state.
- Avoid hard-coded values when they represent configuration, policy, shared constants, or domain concepts.
- Keep domain/business logic independent from frameworks and transport layers where practical.
- Do not let convenience code gradually turn one module into a catch-all.
- When a feature exposes weak architecture, improve the relevant boundary instead of layering more patches on top.

Architecture is allowed to evolve.

- Existing structure is not sacred if it no longer fits the problem.
- Refactor when doing so reduces duplication, clarifies ownership, simplifies interfaces, or makes future changes safer.
- Prefer incremental architectural improvements over unnecessary large rewrites.
- Preserve behavior during refactors unless behavior changes are explicitly required.

## Reuse and Duplication

Before adding new code, ask:

1. Does equivalent logic already exist?
2. Can an existing function or module be generalized cleanly?
3. Is this logic likely to have more than one caller?
4. Would extracting it improve clarity, or merely add indirection?

Rules:

- Do not copy-paste logic between call sites.
- Consolidate repeated validation, parsing, transformation, mapping, serialization, and business rules.
- Prefer one authoritative implementation of each rule or concept.
- Do not create wrappers that only rename another function without adding useful semantics.
- Do not create multiple helpers that perform nearly identical operations with minor differences; unify them when practical.

## Functions and Helpers

- Functions should have one clear responsibility.
- Prefer meaningful domain-oriented names over generic names such as `handle_data`, `process_item`, or `helper`.
- Keep parameter lists small; use structured inputs when several values belong together.
- Avoid unnecessary helper functions for trivial one-line operations used once.
- Extract helpers when they remove duplication, isolate complexity, improve testability, or express an important concept.
- Avoid chains of tiny helpers that make control flow harder to follow.
- Prefer pure functions for transformations and calculations when practical.

## Types and Data Models

- Use clear types and structured models instead of loosely shaped dictionaries/objects when the data has a stable schema.
- Reuse existing domain models rather than creating parallel representations of the same concept.
- Keep conversions between representations explicit and localized.
- Validate data at system boundaries rather than repeatedly throughout internal code.
- Represent finite states with enums, literals, tagged unions, or equivalent typed constructs where appropriate.

## Error Handling

- Fail explicitly and with useful context.
- Do not silently swallow exceptions.
- Catch errors only when the code can meaningfully recover, translate, enrich, or clean up after them.
- Preserve original causes when re-raising errors.
- Do not use exceptions for ordinary control flow when a clearer alternative exists.
- Validate external inputs and assumptions at boundaries.

## State and Side Effects

- Keep state ownership clear.
- Minimize global mutable state.
- Keep I/O, network calls, filesystem access, database operations, and other side effects separated from core logic where practical.
- Avoid hidden mutations; prefer explicit inputs and outputs.
- Make lifecycle and cleanup responsibilities explicit for resources such as files, sockets, workers, GPU memory, and database connections.

## Configuration

- Do not scatter configuration values throughout the codebase.
- Use the project's existing configuration mechanism.
- Separate environment-specific configuration from application logic.
- Never commit secrets, tokens, credentials, or private keys.
- Avoid adding a new configuration system if one already exists.

## Dependencies

- Prefer standard-library or existing-project solutions when they are sufficient.
- Add dependencies only when they provide clear value and avoid substantial custom complexity.
- Do not introduce overlapping libraries that solve the same problem without a strong reason.
- Keep dependencies isolated behind project-owned interfaces when vendor-specific behavior would otherwise spread through the codebase.

## Testing

- Update or add tests for behavior that changes.
- Test public behavior and important edge cases rather than implementation details.
- Reuse test fixtures and helpers instead of duplicating setup.
- Keep tests deterministic and isolated.
- A bug fix should include a regression test when practical.
- Do not weaken or delete valid tests merely to make a change pass.

## Performance

- Prefer correctness and clarity first.
- Optimize measured bottlenecks, not hypothetical ones.
- Avoid obviously wasteful repeated work, unnecessary allocations, duplicate queries, repeated model loading, or redundant serialization.
- Cache only when lifecycle, invalidation, and memory cost are understood.
- For batchable or vectorizable workloads, avoid unnecessary per-item overhead when a clear batched implementation exists.

## Concurrency and Async Code

- Use concurrency only when it provides a real benefit.
- Keep ownership, cancellation, timeouts, retries, and cleanup explicit.
- Avoid fire-and-forget tasks unless their lifecycle is intentionally managed.
- Do not mix blocking and async code carelessly.
- Protect shared mutable state or redesign to avoid sharing it.

## APIs and Interfaces

- Keep APIs minimal and unsurprising.
- Prefer explicit arguments and return values over hidden environmental assumptions.
- Avoid leaking internal implementation details across module boundaries.
- Maintain backward compatibility when it is part of the project's contract; otherwise prefer a clean interface over preserving accidental design mistakes.
- When changing an interface, update all callers and remove obsolete paths rather than maintaining redundant old and new flows indefinitely.

## Code Cleanup

When changing an area of code:

- Remove dead code made obsolete by the change.
- Remove unused imports, stale comments, redundant branches, and abandoned compatibility paths.
- Do not leave commented-out implementations behind.
- Do not perform unrelated broad cleanup that makes the requested change harder to review.

## Comments and Documentation

- Write code that explains itself through good structure and naming.
- Use comments to explain *why*, constraints, invariants, or non-obvious decisions—not to narrate obvious code.
- Update documentation when behavior, configuration, setup, or public interfaces change.
- Keep documentation aligned with the actual implementation.

## Implementation Style

- Follow the project's existing formatter, linter, naming conventions, and directory structure.
- Prefer early returns over deeply nested conditionals when they improve clarity.
- Keep abstractions proportional to actual complexity.
- Avoid speculative generalization for hypothetical future requirements.
- Avoid "temporary" shortcuts that create a second code path or duplicate source of truth.
- Prefer deleting obsolete code over preserving it indefinitely behind flags or wrappers unless compatibility requires it.

## Change Discipline

For each task:

1. Understand the existing design and behavior.
2. Find the correct ownership boundary for the change.
3. Reuse or improve existing abstractions where possible.
4. Implement the simplest coherent solution.
5. Consolidate duplication introduced or exposed by the change.
6. Update tests.
7. Run the relevant tests, linting, type checks, and formatting available in the project.
8. Review the diff for unnecessary complexity, duplicated logic, dead code, and accidental changes.

## Final Standard

A good change should leave the codebase at least as coherent as it was before.

Do not merely make the requested behavior work. Prefer solutions that:

- have one clear source of truth,
- reuse existing logic,
- minimize duplication,
- keep responsibilities well separated,
- remain easy to test,
- are easy for another engineer to understand,
- and allow the architecture to evolve cleanly as the project grows.
