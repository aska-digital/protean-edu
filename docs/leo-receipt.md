# leo-receipt — protean-edu contract

Dispatch: 2026-10-09. Owner: leo. Domain: architecture. Class (a).

## Preflight read-back

- Config: /Users/kethuda/.hermes/profiles/leo/config.yaml → provider: nous,
  model.default: inclusionai/ling-3.1-flash. Matches the brief. No model switch.
- Ownership matrix: /Users/kethuda/.hermes/team-skills/ops/OWNERSHIP-MATRIX.md, dispatched at
  2026-10-09T08:11:58Z with md5=3fc27c834313d92c520ea3bf7cd18b38; re-verified on disk this
  session, same md5.
- Skeleton: `git log -1` → 8b60569b9dc2a6eff67b6013cb48cac95b990c0c,
  "feat: register /edu as a Hermes plugin command", ahrazzle, Fri Oct 9 03:25:15 2026 -0500.
- Tests: `python3 -m pytest tests/test_edu_command.py -q` → 5 passed.
- Remote: none configured (`git remote -v` empty). None created.
- Environment note: the login shell rc has a broken cd (exit 126 on bare commands); all terminal
  calls used explicit workdir/absolute paths.

## Decisions refused to reopen (brief facts, carried as locked)

- Repo name and path (protean-edu, /Users/kethuda/Documents/protean-projects/protean-edu); no
  remote.
- Format: Hermes plugin (plugin.yaml + register(ctx)), not a fork, not a skill.
- Docs basis: the two plugin doc pages; /plugins/ is the catalog store, not a third API.
- Placement: own repo; no directory under NousResearch/hermes-agent/plugins/; no catalog PR now.
- Admission rules: public hooks and ctx.register_* only; no self-update; declare capabilities;
  disclose risk.
- register_command signature and the /edu non-collision with built-ins.
- Skeleton command set (on/off/status/next/help) as the base.
- State file name and its three keys; /edu off preserves level and lesson.
- Audience (Ahraz, first student; non-technical; he reviews, the mode does the work) and the
  teaching rule (decision, command, checkable fact; plain words; no lecture).

## Decisions locked by this contract (within allowed decisions; owner may veto at review)

- Command surface: on/off/status/next/help kept; review added; ask/why/glossary rejected with
  reasons (contract §3).
- State: three keys only, no additions; extension rule recorded (§4).
- Lessons: lessons/NNN-slug.md, five required headings plus optional Glossary; directory-sort
  navigation; missing or malformed lessons reported, never invented (§5).
- Injection: pre_llm_call, user-message append only, 160-character cap, fixed content set, four
  no-op conditions (§6).
- Gate: the Proof Run; two-phase /edu next with self-attested "yes" (§7).
- Prohibitions and update-stable surfaces (§8–§9).

## Files written (owned files only)

- /Users/kethuda/Documents/protean-projects/protean-edu/docs/contract.md
- /Users/kethuda/Documents/protean-projects/protean-edu/docs/leo-receipt.md

Not touched: __init__.py, tests/, plugin.yaml, README.md. No remote created. No code written.

## Exit evidence

docs/contract.md exists. docs/leo-receipt.md exists and ends with the line STABLE.

STABLE
