# protean-edu design notes

Deliberate decisions that must not be "fixed" later by mistake. The contract
(docs/contract.md) is the single source of truth. These notes record why.

## The lesson-advance gate is honor-based (2026-10-09)

`/edu next yes` advances the lesson on the student's own attestation that the
Proof Run passed. The plugin cannot watch the student's screen, run shell, or
make a network call (contract §9 binding), so it cannot verify the check was
run. Typing "yes" is the student's own hand on the record, nothing more.

This is deliberate, not a gap. protean-edu is for self-directed learning. The
learner is trusted to be honest with themselves. Enforcing verification would
need shell, network, or screen access the contract forbids, widening the
security surface for no gain in a self-directed tool.

What must not change:

- Do not add a "verified" badge or claim from the `yes` attestation.
- Do not try to run the check automatically. It stays honor-based.
- If automation is ever desired, it needs an explicit contract amendment that
  widens the §9 binding, not a quiet code change.

Reference: docs/contract.md §7 (two-phase next), §8, §9 (binding). Issue #2.
