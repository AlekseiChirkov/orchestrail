> Active scope: Phase 1 of 2 — Offline review comparison. Phase 2 remains deferred pending phase 1 validation, historical comparison and owner decision.

## Subtasks

| ID | Name | Key Steps (summary) | Depends On | Status | Model (Claude) | Model (Codex) |
|----|------|---------------------|------------|--------| --- | --- |
| T-01 | Pin approved case packets | Define the shared packet and coordinator manifest fields → Specify canonical digest pinning and masking at admission for PR and integrated milestone compositions → Build synthetic examples for PR | — | reviewed |  |  |
| T-02 | Verify isolated paired reviews | Provide matched variant instructions and one first-observation record format → Define the allowed packet and output boundaries → Verify isolation and first artifact capture with seeded out-of-packet markers and check the four-criterion coverage fixture | T-01 | reviewed |  |  |
| T-03 | Document bounded dispatch and recovery | Define locked admission settings and operator reservation and attempt records → Specify ready review and adjudication selection → Verify two slots | T-02 | reviewed |  |  |
| T-04 | Derive blinded paired decisions | Define opaque finding projection → Provide report fields for pair eligibility → Verify equality | T-03 | reviewed |  |  |
| T-05 | Verify offline rehearsal readiness | Run three synthetic rehearsal cases with six independent observations using the preceding procedure and artifacts → Verify fail-closed readiness for mismatch → Record reproducible fixture results and index the operator entry point | T-02, T-03, T-04 | reviewed |  |  |
| T-06 | Capture unstarted cutoff observations | Reproduce cutoff capture → Validate unstarted observations → Verify scoring | T-05 | reviewed |  |  |

## Execution Strategy

Run the listed order as a single sequential stack. Both review outputs and due-coverage checks form one paired-review component. Separating operator dispatch from the paired-review templates gives resource admission and recovery an independent contract. The final rehearsal verifies the whole composition. Batch independent reads and run synthetic checks concurrently only when they have separate writable outputs.

## Decomposition Decisions

| Subtask | Decision | Signals | Rationale |
|---------|----------|---------|-----------|
| T-01 | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One verifiable protocol component covering AC-45. |
| T-02 | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One verifiable protocol component covering AC-46, AC-47. |
| T-03 | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One verifiable protocol component covering AC-49. |
| T-04 | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One verifiable protocol component covering AC-50. |
| T-05 | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One verifiable protocol component covering AC-48. |
| T-06 | leaf | S1=3, S2=1, S3=1, S4=false, S5=1 | One shared fix group for cutoff observation compatibility. |
