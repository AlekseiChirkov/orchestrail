# ADR-0029: Decisions for Task 011 — Adapter-declared deployment targets and canonical instruction names

## Status

Accepted

## Date

2026-11-26

## Related Task

- Task: [Model-only harnesses and rule naming](../specs/011-model-only-harnesses-and-rule-naming.md)
- Related files: `harness/`, `docs/name-map.json`, `scripts/lint-instructions.py` and
  `tests/fixtures/validator-runtime/inventory-amendment.json`.

## Summary

Use adapter-declared deployment paths, a shared instruction namespace, and a
reviewed amendment to the frozen validator inventory.

## Context

[ADR-0009](0009-task-unknown-roadmap-decisions-2026-09.md) Decision 2 sets the
adapter and capability design. [ADR-0009](0009-task-unknown-roadmap-decisions-2026-09.md)
Decision 3 establishes the four rule kinds and the canonical workflow commands.
[ADR-0028](0028-task-011-harness-deployment-engine.md) records how the deployment
engine applies the adapters in one transaction.

## Decisions

### Decision 1: Declare targets and keep one instruction namespace

**What was decided:** ADR-0003 is superseded for its deployment targets only. Read
`harness/<name>/deploy.env` to resolve global and project paths. Retain the
`rule-` prefix and duplicated always-on essentials from
[ADR-0003](0003-task-unknown-rules-as-prefixed-skills.md). Principles retain their
`principle-` prefix. Each source has the same installed name across adapters,
and `docs/name-map.json` records the migration. Commands use the canonical names
without compatibility aliases. Keep prior task history and finalization journal
authority intact.

**Why:** A common namespace lets all supported harnesses load the same instruction
source. Declared targets keep provider-specific paths in the adapter.

**Alternatives:** Per-harness instruction names would require separate workflow
references. Fixed deployment paths would keep provider-specific logic in the
shared installer.

**Consequences:** The engine uses `<config>/orchestrail/deploy/<harness>.json`
to track ownership and reads the physical-root project registry for link refresh.
Installed global instructions combine the always-on body, the capability
declaration and the current hook installation record. Workflows rely on declared capabilities plus
actual session tool access and permission at dispatch.

**Related files:** `harness/`, `docs/name-map.json`, and `scripts/deploy-skills.py`.

### Decision 2: Record the scoped inventory amendment

**What was decided:** Amend the frozen inventory of
[ADR-0018](0018-task-06-1-bounded-validator-runtime.md) through the schema-2
`tests/fixtures/validator-runtime/inventory-amendment.json`. Keep the frozen
baseline, check identities and existing accepted extensions.

**Why:** The name map and exact expression deltas expose the effects of the
migration on each check.

**Alternatives:** Replacing the frozen inventory would discard the audit trail.

**Consequences:** Bind path-only updates to the reviewed name map and document
approved contract changes with the before and after expressions and independent
verdicts. ADR-0018 remains provisional for the validator runtime architecture.

**Related files:** `tests/fixtures/validator-runtime/inventory-amendment.json` and
`tests/validator-runtime-oracle.py`.

### Decision 3: Keep instruction verification standalone

**What was decided:** Run `scripts/lint-instructions.py`,
`scripts/check-lint-instructions.py` and `scripts/check-deploy-skills.py` directly. Follow
[ADR-0019](0019-task-unknown-spec-draft-devils-advocate-review.md) Decision 3 for
focused checks outside the frozen validator.

**Why:** Focused command-line checks can verify the new instruction and
deployment contracts without changing the frozen result inventory.

**Alternatives:** Registering the checks in the full validator would expand the
frozen inventory.

**Consequences:** Run these commands explicitly. The existing sync preflight
keeps its full validator and independently required checks.

**Related files:** `scripts/lint-instructions.py`, `scripts/check-lint-instructions.py`,
and `scripts/check-deploy-skills.py`.

## Questions and Answers

No external questions and answers were recorded during this task.

## Rejected Options

Per-harness instruction names, replacement of the frozen validator baseline,
and new registrations in the frozen validator.

## Implications for Future Work

Keep path and name changes coordinated across the source, installed skills and
the name map. Apply independently reviewed inventory amendments to the affected
expressions. Run the documented rollback before restoring a deployment from the
prior source.

## Verification

On 2026-11-26 the standalone command `python3 -I scripts/lint-instructions.py`
ran against an isolated Git export of
`64c0acadc6b2120d070d518000c779ae645c18c7`, with Python 3.14.4 on Linux x86_64.
It finished in 4.789 seconds against a 30-second target, exited 0, and emitted
zero findings and two informational results for optional reserved-name lists.
The measured tool was the repository's Python checker invoked directly, with an
isolated home, configuration and state root. Independent scoped review at that
revision also verified the canonical names, dispatch capability checks and
unchanged finalization authority. The standalone instruction suite deployed both
harnesses to a disposable fixture and compared their assembled instructions and
installed skill bytes with the sources.

This evidence covers the tested source revision and isolated installation
fixtures. The integrated validation, owner integration and live deployment are
recorded separately.

## References

- [Architecture](../memory/architecture.md#harness-adapters)
- [Runbook](../context/runbook.md#deployment-rollback)
- [Migration audit](../../docs/audits/2026-11-25-rule-migration-map.md)
