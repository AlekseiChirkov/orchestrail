# state-archive — task-011-model-only-harnesses-and-rule-naming-p1

Archived after discovery: complete.
Read by Validation-phase workflows when full context is needed.
Do not edit manually.

## Archived Task Analysis
### Goal
Phase 1 of 2 — Deliver harness infrastructure, capability records, ownership-safe deployment, checker and inventory repair while preserving user-owned files and historical records; names and integrated checks remain in phase 2.

### Affected Parts
Deployment and project setup, harness adapters, registry consumers, skill ownership, workflow and rule metadata and names, validator inventory amendment, standalone checks, documentation and knowledge records.

### Codebase Analysis
- `scripts/sync.sh`: verify current global and project deployment; it writes legacy targets and copies harness skills directly (lines 109–222, 259–332).
- `scripts/setup-new-project.sh`: verify project scaffolding; it creates legacy rule directories (lines 85–140).
- `harness/claude/capabilities.md` and `harness/codex/capabilities.md`: verify current mechanism and git-rails declarations; canonical six capability records are not present (lines 3–46 and 3–12 respectively).
- `rules/orchestration.md` and `rules/workflow-globals.md`: verify current metadata and orchestrated contract (line 2 in each).
- `workflows/spec-run.md`: verify current orchestration entry point and stack procedure (lines 2–5).
- `tests/validator-runtime-oracle.py` and `scripts/validate-contracts.sh`: verify frozen inventory and legacy checks; the oracle includes a subsequently approved state-tool extension (oracle lines 47–59, 101–103; validator lines 865, 1308–1325).
- Full validator previously reported `test_public_identity_matches_exact_ledger_and_preserves_knowledge` failing on a former task path already absent at source revision; the run was interrupted later and is not a complete suite result. No baseline was changed.
- `rules/phase-finalize.md` and `workflows/phase-finalize.md`: verified the later finalization sources; the initial unmapped-source guard was resolved by the owner-authorized DM-10/DM-11 reconciliation. The naming and read-only journal relocation work belongs to deferred phase 2.
- Files read: 11/12 (8 entry-points, 3 deeper: the orchestration and globals rules and the validator oracle). Other source descriptions and cross-spec dependencies require later focused validation.
- Source revision: 8857b631858bcde083a5a087371f72aa303d9058. Registry inspection: one registered root; one active state, this Discovery. Claude and Codex skill directories are present; the legacy global rules directory is absent. Inspection was read-only.

### Open Questions
The finalization sources have been classified and mapped and the resulting specification independently reviewed. The identity inventory baseline failure and the relocated finalization journal require implementation and verification under REQ-72 and REQ-73. No implementation is claimed.

## Archived Solution Design — Variants
- A: One standard-library deployment entry point with internally separated planning, project and transaction functions; standalone checker, reporter and oracle are separate components. Fewer copied runtime files and the specification's AST checks cover the entry point, but the engine needs careful internal boundaries.
- B: A thin deployment entry point with separately imported planning, project and transaction modules. Modules isolate responsibilities, but require extra source-selection, packaging and static network/subprocess coverage across every imported file.

## Archived Solution Design — Rejected
B adds distribution and security-scan surfaces before they are needed. A fixture-only or rebaselined inventory loses existing baseline guarantees and is rejected by REQ-72.

