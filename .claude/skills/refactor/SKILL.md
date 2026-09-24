---
name: refactor
description: Guidance for structural changes such as moving responsibilities, consolidating duplicate logic, reshaping module boundaries, or changing interfaces. Use when a task calls for restructuring code, or when a feature exposes weak architecture that should be fixed instead of patched around.
---

# Refactor

Existing architecture is allowed to evolve. Use this skill when the current structure no longer fits the problem.

## When to refactor

Refactor only when doing so does at least one of the following:
- reduces duplication,
- clarifies ownership,
- simplifies an interface,
- makes future changes safer.

Don't refactor for taste alone, and don't bundle unrelated broad cleanup into a feature change. It makes the change harder to review.

## How

1. **Establish a safety net.** Check that tests cover the behavior you're about to move. If they don't, add characterization tests first.
2. **Preserve behavior.** A refactor must not change behavior unless the task explicitly requires it. Keep behavior changes and structural changes in separate, identifiable steps.
3. **Work incrementally.** Prefer a series of small, verifiable moves over a large rewrite. Run the tests after each meaningful step.
4. **Consolidate to one source of truth.** When merging duplicate logic, choose or build the authoritative implementation, point every caller at it, and delete the rest.
5. **Finish migrations.** When an interface changes, update all callers and remove the old path. Keep the old path only if backward compatibility is part of the project's contract, and never leave it indefinitely behind flags or wrappers.
6. **Clean up.** Remove dead code, unused imports, stale comments, and redundant branches that the refactor made obsolete. Update docs that describe the moved structure.

## Boundary checks

After the refactor, confirm:
- each module has one clear purpose and owner,
- domain logic doesn't depend on frameworks, transport, or I/O,
- dependencies flow explicitly (injected or passed in) rather than through globals or hidden coupling,
- public interfaces are smaller or clearer than before, not larger.
