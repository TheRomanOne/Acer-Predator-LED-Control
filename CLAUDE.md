# Engineering Rules

## Communication

- Responses are compact and to the point: only what the user needs to act or decide. No restating the request, no narrating routine steps, no repeating what earlier messages already said.
- Prefer a short list or table over prose when it carries the same information.
- End every response with a **Bottom line** section: one to three sentences with the outcome and the next action (or the decision needed).

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

# LED Studio (this repository)

RGB lighting control for the Acer Predator Helios 16 AI (PH16-73) on Windows and Ubuntu. Every
lighting zone is a HID LampArray; the app drives it directly over hidapi (no WMI, no kernel
module). `README.md` has the zone table, hardware notes and the MagKey (A/W/S/D) story.
`INSTRUCTIONS.md` is the earlier long form of the rules above; the rules above win.

## Commands

Backend (`backend/`, Python 3.13 venv at `backend/.venv`; use `.venv/bin/` on Linux):

```bash
cd backend && .venv/Scripts/pip install -e ".[dev]"          # first time
cd backend && .venv/Scripts/python -m pytest                  # all tests
cd backend && .venv/Scripts/python -m pytest tests/test_sunrex.py -k off_is   # one test
cd backend && .venv/Scripts/python -m ruff check . && .venv/Scripts/python -m mypy   # lint + strict types
cd backend && .venv/Scripts/python -m led_studio.main         # serve on 127.0.0.1:8765 (opens the hardware)
cd backend && .venv/Scripts/python -m led_studio.cli list     # also: identify | fill <id> R G B | release
```

Frontend (`frontend/`, Node 24):

```bash
cd frontend && npm test                          # vitest, all
cd frontend && npx vitest run src/color.test.ts  # one file
cd frontend && npm run typecheck && npm run lint # tsc -b, oxlint
cd frontend && npm run dev                       # Vite on 5173, proxies /api (incl. WebSocket) to 8765
```

`run_app.cmd` / `run_app.ps1` / `run_app.sh` start both servers (first run installs deps) and
kill whatever holds ports 8765/5173 first. `.claude/launch.json` defines `backend` and
`frontend` previews. Only one backend may run at a time: a second instance fights the first
for the HID devices.

## Backend architecture

Strict layering; each layer only imports the ones below it:

- `hid/transport.py`: the only module that imports `hid` (hidapi). Everything above it works
  on bytes and is tested with `tests/fakes.py` (in-memory LampArray emulator, vendor transport
  fake). Reports carry their report ID as byte 0 in both directions (hidapi convention).
- `hid/descriptor.py` + `hid/reports.py`: pure parsing/packing of HUT 1.5 LampArray reports.
  Report IDs differ per vendor, so they are parsed from the report descriptor, never
  hard-coded. Sunrex firmware stalls GET_REPORT unless the requested length is exact, so use
  the `*_REPORT_SIZE` constants. `hid/sunrex.py` is the separate Sunrex vendor protocol
  (usage page 0xFF02, four 9-byte unnumbered feature reports, ~15 ms apart, NOT-sum checksum).
- `devices/`: `LampArray` (one HID collection, lamp-index addressed), `MagKeyController`
  (vendor interface of the same keyboard), `Zone` (array + normalised layout + optional
  MagKey). `open_zones()` is the single discovery entry point used by both `main` and `cli`.
- `patterns/`: `model.py` is the Pydantic schema of a pattern and is simultaneously the API
  contract and the on-disk format; `render.py` is a pure function
  (pattern, layouts, time) -> colours, floats in 0..1 until final quantisation.
- `playback/`: `Player` owns take/release control and pushes only changed lamps (a whole-zone
  `fill` when uniform), tracking per-zone `ZoneHealth`; `PlaybackLoop` is the asyncio ticker
  that renders on the loop, pushes zones in parallel threads, and re-asserts LampArray control
  every second because the Acer lighting service silently retakes zones.
- `storage/patterns.py`: one JSON file per pattern under the data dir, plus the active
  pattern id, restored on startup.
- `api/app.py`: `create_app(zones, store, fps)` with everything injected so `tests/test_api.py`
  runs against fakes. `LocalOnlyMiddleware` rejects non-loopback Host/Origin (no auth
  otherwise). `/api/ws/frames` streams rendered frames; slow clients only ever get the latest.
- `config.py`: `LED_STUDIO_*` env vars via pydantic-settings; host is validated loopback-only.

## Frontend architecture

- `src/api/types.ts` mirrors the backend schemas by hand; `src/api/client.ts` is the only
  place that calls `fetch`/WebSocket. Mock it at that boundary in tests.
- `src/editor/reducer.ts` holds the editor state (draft pattern, selected layer, zone shown
  in preview) as a pure reducer; `src/hooks.ts` wraps devices/status/frame subscriptions.
- `src/keys.ts` maps HID keyboard usages to key-cap labels for the keyboard lamp map; the
  backend reports each lamp's `input_binding` for this.
- Editing a draft previews it live on the hardware (`POST /api/playback/preview`), so the
  physical lights follow whatever the running frontend does.

## Hardware behaviour worth knowing

- Taking control = LampArrayControl autonomous=0 plus MagKey mode Off on the keyboard's
  vendor interface. Releasing only sets autonomous=1; the MagKey mode is left off.
- The Acer Lighting Service (`AcerLightingService`/`ALSSvc`) re-applies its profile from
  `C:\ProgramData\OEM\AcerLightingService\LightingProfile\LightingProfile.ini` on its own
  schedule (observed: right after resume from Modern Standby). Its keyboard-wide vendor
  modes (wire values in that ini: `Direct`=0xFF, `STATIC`=1, ... `MAG_Off`=0x40) use the
  same four-report framing as the MagKey commands with byte 3 of the colour report = 0
  instead of 1. Only the MagKey range (0x40..0x4E) is currently modelled in `hid/sunrex.py`.
