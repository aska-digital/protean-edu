# mozi-receipt — protean-edu build stage 2: contract implemented in code

Dispatch: 2026-10-09. Owner: mozi. Domain: implementation (build, stage 4). Class (a).

## Preflight

- Config: /Users/kethuda/.hermes/profiles/mozi/config.yaml → provider: opencode-go,
  model.default: step-5-preview-free. Matches the brief. No model switch. No config edited.
- Contract read in full before writing: docs/contract.md. Read-back evidence: docs/leo-receipt.md.
- No conflict found between the brief and the contract.

## What was built (contract §3–§7)

- __init__.py implements on/off/status/next(two-phase)/review/help, the deterministic lesson
  parser (§5), and the pre_llm_call injection hook (§6).
- State (§4): exactly three keys — enabled (bool, default false), level (int, default 1),
  lesson (str|null, default null). load_state uses setdefault so a partial file stays valid.
- /edu next is two-phase (§7): bare prints the current lesson title + Proof Run + the
  "When the check passes, run: /edu next yes" line and writes nothing; "yes" records the
  attestation and advances (level += 1, lesson = next slug, null if finished). Both phases
  refuse when off, on a missing lesson, and on a malformed lesson. A missing next lesson
  keeps the student in place — no gap is skipped.
- /edu review is read-only: title, first sentence of "Why this matters", and the
  "Check it yourself" line. Never judges, never runs the check.
- Injection (§6): appends to the user message only, hard cap 160 chars including the fixed
  prefix "[protean-edu]", assembled by string concatenation from the current lesson file.
  No-op when off, lesson null, or lesson missing/malformed. Pure function of state + lesson.
- Binding (§9): ctx.register_command, the pre_llm_call hook, and hermes_constants.get_hermes_home
  (with HERMES_HOME fallback). Nothing else from Hermes; the rest is stdlib (json, pathlib, os).
- plugin.yaml: added provides_hooks: [pre_llm_call] so the registered hook is declared
  (required by `hermes plugins validate`). name/version/description unchanged.

## Prove it

### 1. pytest

Command: /Users/kethuda/.hermes/hermes-agent/venv/bin/python -m pytest -q

Result:

    26 passed in 0.05s

New tests cover: two-phase next (bare then yes), next refuses when off, next refuses on
missing lesson, next refuses on malformed lesson, review is read-only, injection ≤160 chars,
injection no-op when off, injection no-op when lesson null, injection no-op on missing and on
malformed lesson, state setdefault keeps a partial file valid, on preserves level/lesson,
off never deletes the state file.

### 2. plugins validate

Command: /Users/kethuda/.hermes/hermes-agent/venv/bin/python /Users/kethuda/.hermes/hermes-agent/hermes plugins validate .

Output:

    ✓ manifest — plugin.yaml parses
    ✓ manifest fields — name, version, description present
    ✓ requires_hermes — not declared
    ✓ config schema — not declared
    ✓ requires_env — all entries UPPER_SNAKE
    ✓ loadable — entry: __init__.py
    ✓ python dependencies — none declared
    ✓ capability probe — register() ran in isolation
    ✓ declared tools — matches registrations
    ✓ declared hooks — matches registrations
    ✓ declared middleware — matches registrations
    ✓ built-in tool collisions — no tools to check
    ✓ security scan — safe
    ✓ no core override — no runtime rebinds of Hermes core
    ◆ Isolation — runs in the plugin host (plugins.isolation: host)

    Validation passed.

### 3. 160-char cap with a real over-long title

Constructed a lesson title and check line that would far exceed 160 chars, ran the injection,
and measured the emitted string:

    TITLE  : How to read a very long and detailed diff that keeps going and going and going
    CHECK  : Open the file the agent says it changed and read the diff very carefully and then compare every single line against what the agent claimed to have done
    EMITTED: [protean-edu] 1: How to read a very long and detailed…. Check: Open the file the agent says it changed and read the diff very carefully and then compare every…
    LENGTH : 159
    CAP OK : True

The emitted string is 159 characters, within the 160-character cap. The title is truncated at
40 chars on a word boundary with an ellipsis, and the check line is truncated to fit the cap.

## Files written (owned files only)

- /Users/kethuda/Documents/protean-projects/protean-edu/__init__.py
- /Users/kethuda/Documents/protean-projects/protean-edu/tests/test_edu_command.py
- /Users/kethuda/Documents/protean-projects/protean-edu/tests/fixtures/lessons/ (test fixtures:
  001-reading-a-diff.md, 002-prompts.md, 003-broken.md, 004-tests.md — tiny, five headings, a few
  words; not curriculum)
- /Users/kethuda/Documents/protean-projects/protean-edu/plugin.yaml (added provides_hooks only)

Not touched: docs/contract.md, docs/leo-receipt.md, any profile config.yaml, any Hermes core
file. No lesson prose written. No PR opened. No network call. No shell from inside the plugin.

## Exit evidence

- __init__.py implements on/off/status/next(two-phase)/review/help, the lesson parser, and the
  pre_llm_call injection exactly as the contract's §3–§7.
- docs/mozi-edu-receipt.md exists, ends with STABLE, carries the pytest count (26 passed), the
  validate output (all green), and the ≤160 char proof (159 chars).
- No lesson prose written. No PR opened. No config edited. Contract and leo-receipt untouched.

STABLE
