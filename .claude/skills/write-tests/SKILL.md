---
name: write-tests
description: Test-driven development workflow and testing rules. Use before writing any implementation code, and whenever behavior changes, a bug is fixed, or tests fail.
---

# Write Tests (Test-Driven)

## The TDD cycle

Work in small red → green → refactor loops:

1. **Red.** Write one test for the next small piece of behavior (or one that reproduces the bug). Run it and confirm it fails *for the expected reason*, not because of an import or setup error.
2. **Green.** Write the minimum implementation that makes it pass. Run the tests.
3. **Refactor.** Clean up the code and the tests while everything stays green, applying the rules in CLAUDE.md.
4. Repeat until the feature is complete.

Don't write implementation code without a failing test that demands it. The exceptions are pure scaffolding (project setup, config wiring) and code that talks directly to hardware or the OS. For those, keep the untestable part as a thin adapter behind an interface, and test everything above it with fakes.

## Tooling for web apps

- `backend/`: pytest. Use FastAPI's `TestClient` or Flask's `test_client` for API tests.
- `frontend/`: the project's runner (Vitest by default for new Vite projects) plus React Testing Library. Mock the API client at its boundary, not `fetch` scattered across components.

## What to test

- Every behavior you changed or added.
- Public behavior and important edge cases, not implementation details. A test should survive an internal refactor that preserves behavior.
- Bug fixes: add a regression test that fails without the fix, when practical.
- Validation at system boundaries, including malformed or unexpected external input.

## How

- Reuse existing fixtures, factories, and helpers instead of duplicating setup. If setup is already duplicated across tests, consolidate it.
- Keep tests deterministic and isolated: no reliance on test order, wall-clock time, randomness without a seed, network, or real hardware unless the test is explicitly an integration test.
- Put side-effecting dependencies (I/O, devices, network) behind injectable interfaces so core logic can be tested with fakes.
- Follow the project's existing test layout, naming, and framework. Don't add a second test framework.

## When tests fail

- Fix the code, or fix a test that is genuinely wrong. Explain which one and why.
- Never weaken, skip, or delete a valid test just to make a change pass.
- Report the real results, including any failures you couldn't resolve.
