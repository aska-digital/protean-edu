# protean-edu contract

Owner: leo (architecture, stage 2). Domain: architecture. Class (a).
Locked at dispatch, 2026-10-09. Read-back evidence: docs/leo-receipt.md.

## 1. Purpose

protean-edu teaches one person — a non-technical user, first student Ahraz — to read the code
their agents write, well enough to direct the work and review it. The plugin does not do the
work. It explains the decision, the command, and what the student can check himself, in plain
words. The agent keeps working; the lessons are the point.

## 2. Invariants

- I1. One slash command, /edu, registered only through ctx.register_command. Hermes core files
  are never edited.
- I2. State is exactly one JSON file: $HERMES_HOME/protean-edu-state.json. Keys are exactly the
  three in §4. /edu off preserves level and lesson.
- I3. Lessons are static markdown files in lessons/, numbered by filename. Finding the next
  lesson is a directory sort. It is never an LLM call.
- I4. A missing or malformed lesson is reported as missing or malformed. Nothing is invented,
  synthesized, or faked.
- I5. The teaching injection appends to the user message only, is at most 160 characters, is a
  no-op when disabled, and is assembled by string operations from lesson fields — never generated.
- I6. The plugin never calls an LLM, never runs shell, never reads secrets, never opens a network
  connection, and never writes any file except its state file.
- I7. Teaching is off by default. enabled is false until /edu on. A fresh install with the plugin
  present behaves exactly like Hermes without it.
- I8. Advancement past a lesson requires the student's own attestation that the Proof Run (§7)
  passed. The plugin cannot observe the external world; the attestation is honor-based, and the
  plugin must never claim it verified something it did not.

## 3. Command surface

Kept from the skeleton: on, off, status, next, help.
Added by this contract: review.

| command | reads | writes | must never |
|---|---|---|---|
| /edu on | existing state (to preserve level/lesson) | enabled=true | wipe level or lesson; require network; turn on anything else |
| /edu off | state | enabled=false | wipe level or lesson; delete the state file |
| /edu status | state only | nothing | mutate anything; call an LLM |
| /edu next | state, lessons/ directory, current lesson file | on "yes": level+1, lesson=next id | advance when disabled; skip a missing lesson; invent a lesson; rewrite lesson files |
| /edu review | state, current lesson file | nothing | judge the student's work; run the check for the student; advance level |
| /edu help | nothing | nothing | change behavior |

Candidates considered:

- /edu review — ACCEPTED. It is the review gate made runnable. It prints the current lesson's
  title, the first sentence of "Why this matters", and the "Check it yourself" line. Read-only.
- /edu ask — REJECTED. Answering a question needs an LLM. An LLM inside the plugin is a second
  agent, forbidden by §8. Questions belong in the normal chat; the injection already carries the
  current lesson into every turn.
- /edu why — REJECTED. The why already has two homes by design: the lesson's "Why this matters"
  heading and the injection's first sentence. A third path would invite an LLM summary, which is
  a second agent. If the student wants the why, /edu review prints its first sentence.
- /edu glossary — REJECTED. A glossary is lesson content, not a command. It lives under the
  "Glossary" heading in each lesson file. A command would duplicate content and add surface
  without adding capability.

## 4. State shape

One file, three keys, no additions:

- enabled: bool, default false.
- level: int, default 1. The ordinal of the current lesson. 1-based. The authoritative pointer.
- lesson: str or null, default null. The slug of the current lesson (filename stem after the
  number). A human-readable echo of level; null means "not started".

Extension rule: a new key may be added only if a lesson cannot be resumed without it, and only
with the operator's approval. Resume needs only the three keys above, so none is added now. Any
future key must be added with a default that keeps existing state files valid (setdefault
semantics), and its name, type, and default must be recorded in this contract. No database, ever.

Why no key for the gate: the Proof Run attestation is carried by the argument of /edu next (§7),
not by state. The plugin cannot observe whether the student actually ran the check, so storing a
"checked" flag would record an attestation, not a fact.

## 5. Lesson files

Location: lessons/ at the repo root. One file per lesson.
Naming: lessons/NNN-slug.md — NNN is a three-digit zero-padded number (001–999), slug is
lowercase words joined by hyphens. The number in the filename is the level.

Required headings, in order:

1. `# Lesson N: Title` — N must equal the filename number.
2. `## Why this matters` — 1–3 sentences. The first sentence is the only part the injection may
   quote.
3. `## The idea` — the teaching body. Plain words. Never injected.
4. `## Check it yourself` — exactly one check: one line, one imperative sentence, runnable by a
   non-technical person. This is the Proof Run for the lesson.
5. `## Next` — one line: the next lesson's number and slug, or "None — this is the last lesson."

Optional heading: `## Glossary` — terms used in the lesson.

Parser rules (deterministic, no LLM):

- Find the file for level L by sorting lessons/ by filename and matching the LLL- prefix.
- Split on lines beginning with "## ". Take the first non-empty line under each required heading.
- If the file for level L does not exist: "There is no lesson L yet." Nothing else.
- If the H1 number does not match the filename number, or any required heading is missing or
  empty: "Lesson L is malformed (reason)." Nothing else.
- The lesson body is never truncated or rewritten by the plugin.

## 6. The teaching injection

Trigger: the pre_llm_call hook, and only while enabled is true.
Target: the user's latest message, appended. Never the system prompt — the plugin docs forbid
system-prompt edits because they break the prompt cache. Never any other message.

Hard cap: 160 characters including the fixed prefix.

Allowed content, assembled by string concatenation from the current lesson file only:

- the fixed prefix `[protean-edu]`
- the lesson number and title (title truncated at 40 characters, word boundary, "…")
- the first line of "Check it yourself", truncated to fit the cap (word boundary, "…")

Example: `[protean-edu] 2: prompts. Check: open the file the agent says it changed and read the diff.`

Must never contain: the lesson body, the why, glossary entries, any lesson other than the current
one, anything LLM-generated, any instruction to the agent to teach or to grade the student, any
personal data.

No-op conditions: enabled is false; lesson is null; the lesson file is missing or malformed. In
all four cases the hook appends nothing. The hook is a pure function of the state file and the
lesson file: no clock, no randomness, no network, no LLM.

## 7. The review gate — the Proof Run

The named check is the Proof Run: rerun the exact thing the agent claims to have done, with your
own eyes, and compare what actually happens to what the agent said would happen. A claim is not
proof; the output of running it is.

The plugin's role:

- Each lesson names its Proof Run in its "Check it yourself" heading.
- /edu review prints it. Read-only.
- /edu next is two-phase:
  - `/edu next` (no argument): prints the current lesson's title and its Proof Run, then:
    "When the check passes, run: /edu next yes". Writes nothing.
  - `/edu next yes`: records the student's attestation and advances — level += 1, lesson = the
    next lesson's slug (null if the curriculum is finished) — writes state, prints the new status
    and the next lesson's title.
  - If the next lesson file does not exist, the student stays and is told so. No skipping gaps.
  - If the current lesson file is missing or malformed, both phases report that and advance
    nothing — there is no check to attest.

The limit, stated plainly: the plugin cannot see the student's screen. It cannot know the check
was actually run. The gate is therefore self-attested: typing "yes" is the student's own hand on
the record. That is a deliberate limit of a plugin that must not run shell or observe the machine.
The plugin must never present the attestation as verification.

## 8. What this plugin must not become

- A second agent. It never calls an LLM, never spawns subagents, never holds a conversation. It
  reads files and returns strings.
- A fork. It never edits hermes_cli/ or any Hermes core file. It binds only to ctx.register_* and
  the public hooks.
- A memory backend. It never stores conversation history, never reads user messages except at the
  pre_llm_call append point, never writes anything but its three-key state file.
- A tool that writes the student's code. The agent does the work. The plugin explains decisions
  and names checks. It never generates, edits, or writes project code.
- A thing that turns on by default. enabled is false until /edu on. A fresh install is
  indistinguishable from plain Hermes.
- And from the catalog admission rules, binding now: no self-update; every registered capability
  declared; risky behaviour disclosed. This plugin's risk is low: one JSON write under HERMES_HOME
  and a short append to the user message. It must not read secrets, must not run shell, must not
  send data off the machine.

## 9. What must not change when Hermes updates

The plugin binds to exactly these public surfaces:

- ctx.register_command(name, handler, description="", args_hint=""), with handler
  fn(raw_args: str) -> str | None
- the pre_llm_call hook
- hermes_constants.get_hermes_home (with the documented HERMES_HOME fallback)

It imports nothing else from Hermes. Everything else is Python stdlib (json, pathlib, os).
Undocumented internals are forbidden, because those are what updates break.

If a bound surface is missing at load, register() must fail loudly — the command simply does not
appear — rather than patching around the change or degrading silently. The contract in this
document (command names, state keys, lesson headings, injection format) is owned here, not by any
Hermes version.

## 10. Declared capabilities (for the future catalog entry)

- Registers: one slash command, /edu, subcommands on | off | status | next | review | help.
- Hooks used: pre_llm_call (user-message append only, when enabled).
- Files written: one — $HERMES_HOME/protean-edu-state.json.
- Files read: the state file and lesson files under the plugin's own lessons/ directory.
- Network: none. Shell: none. Secrets read: none. LLM calls: none. Self-update: no.

Catalog listing is a later stage: one plugin-catalog yaml pinning an exact commit. Not now.
Do not open that PR.

## 11. Not decided here

These belong to the operator or to forbidden territory, and Leo refused to touch them:

- Lesson prose, lesson order, and the curriculum itself (writing; Hazen's domain, owner-approved).
- Creating a GitHub remote or choosing an org (forbidden).
- Deployment (forbidden; D-1 is a user decision).
- Renaming the repo (forbidden).
- Any change to __init__.py or tests (frozen for this dispatch; skeleton is 8b60569).
