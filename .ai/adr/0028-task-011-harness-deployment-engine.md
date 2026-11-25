# ADR-0028: Decisions for Task 011 — Harness deployment engine

## Status

Accepted

## Date

2026-11-25

## Related Task

- Task: `.ai/tasks/todo/task-011-model-only-harnesses-and-rule-naming-p1/`
- Related pull requests: [#147](https://github.com/AlekseiChirkov/orchestrail/pull/147), [#148](https://github.com/AlekseiChirkov/orchestrail/pull/148), [#153](https://github.com/AlekseiChirkov/orchestrail/pull/153)
- Related files: `scripts/deploy-skills.py`, `scripts/sync.sh`, `scripts/setup-new-project.sh`

## Summary

Shell entry points select the source and run the existing preflight. One standard-library
Python entry point deploys declared provider targets and updates registered project links.

## Context

ADR-0009 defines the model harness abstraction. Implementing it requires shared ownership
and transaction rules across all declared harnesses and support for sync from a selected
source tree. The directory layout and active-consumer protection are specified in the
harness migration contract.

## Decisions

### Decision 1: Keep the deployment transaction in one entry point

**What was decided:** Keep planning, ownership checks, journal recovery and registered
project refresh in `scripts/deploy-skills.py`, with separate functions for each operation.
Read target paths from the adapters. Keep instruction lint and retired-object reporting
as separate commands.

**Why:** One engine gives the shell entry points a common source-selection and preflight
boundary and keeps the deployed runtime surface within the offline source checks.

**Alternatives:** Separate planning, project and transaction modules would add files that
every selected source tree and offline check would need to account for. Discovery rejected
that packaging cost for the current scope.

**Consequences:** The engine coordinates all assigned harness targets under a single
non-blocking lock and validates the full plan before replacing managed content. Manifests
record ownership and source revision, and the journal admits only known digests during
recovery. Keep planning separate from writes within the engine. Further modularization
must preserve the source-selection, transaction and offline verification boundaries.

**Related files:**
- `scripts/deploy-skills.py`
- `scripts/check-deploy-skills.py`
- `scripts/report-legacy-artifacts.sh`

## Questions and Answers

| Question | Answer | Impact on implementation |
|---|---|---|
| How should implementation issues be resolved? | The owner delegated decisions and repairs within the task. | Preserve the specification and verify each repair before publishing the stack. |

## Rejected Options

A thin entry point plus separately distributed planning, project and transaction modules.

## Implications for Future Work

Adding an adapter requires a valid declaration and instruction sources. Source code remains
provider-neutral. Installer and synchronization changes must preserve ownership conflict
handling and the existing staged verification mode.

## Verification

The isolated deployment and instruction suites passed at `06236d4e8a6b188fc235481255ab69af7c2c73d4`. The complete
contract validator passed with 725 checks and two optional private-hygiene skips. A full
`sync --stage` build reproduced both declared harnesses’ skill bytes and assembled global
instructions from source.

## References

- ADR-0009, Decision 2
- Harness migration specification, DM-5–DM-8, REQ-42–REQ-45 and REQ-63
- Task state, Solution Design and archived Variants
