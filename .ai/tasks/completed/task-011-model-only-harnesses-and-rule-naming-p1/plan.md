# Phase 1 plan

Scope: Phase 1 of 2. Phase 2 remains deferred until this phase validates and owner integration occurs.

## Subtasks

| ID | Name | Key Steps (summary) | Depends On | Status | Type | Model (Claude) | Model (Codex) |
|---|---|---|---|---|---| --- | --- |
| T-01 | Knowledge inventory relocations | Inspect contract → isolated tests → implement → verify | — | reviewed | leaf |  |  |
| T-02 | Inventory amendment compatibility | Inspect contract → isolated tests → implement → verify | T-01 | reviewed | leaf |  |  |
| T-03 | Instruction metadata and capability checker | (children: T-03a, T-03b) | T-02 | reviewed | composite |  |  |
| T-03a | Instruction metadata parser | Metadata fixtures → parser → verify | T-02 | reviewed | leaf |  |  |
| T-03b | Capability-record checker | Record fixtures → validator → verify | T-03a | reviewed | leaf |  |  |
| T-04 | Instruction name and reference checks | Inspect contract → isolated tests → implement → verify | T-03 | reviewed | leaf |  |  |
| T-05 | Harness adapters | (children: T-05a, T-05b) | T-04 | reviewed | composite |  |  |
| T-05a | Adapter declarations | Verify schema → fixtures → declare → verify | T-04 | reviewed | leaf |  |  |
| T-05b | Always-on moves | RED → Git moves → update consumers → verify | T-05a | reviewed | leaf |  |  |
| T-06 | Read-only legacy artifact reporter | Inspect contract → isolated tests → implement → verify | T-05 | reviewed | leaf |  |  |
| T-07 | Ownership-safe deployment planning | Inspect contract → isolated tests → implement → verify | T-06 | reviewed | leaf |  |  |
| T-08 | Deployment transactions and recovery | Inspect contract → isolated tests → implement → verify | T-07 | reviewed | leaf |  |  |
| T-09 | Registered project links | Inspect contract → isolated tests → implement → verify | T-08 | reviewed | leaf |  |  |
| T-10 | Active consumer deployment freeze | Inspect contract → isolated tests → implement → verify | T-09 | reviewed | leaf |  |  |
| T-11 | Deployment source revision | Inspect contract → isolated tests → implement → verify | T-10 | reviewed | leaf |  |  |
| T-12 | Unowned leftover reporting | Inspect contract → isolated tests → implement → verify | T-11 | reviewed | leaf |  |  |
| T-13 | Deployment and setup entry points | Inspect contract → isolated tests → implement → verify | T-12 | reviewed | leaf |  |  |
| T-14 | Source instruction metadata | Inspect contract → isolated tests → implement → verify | T-13 | reviewed | leaf |  |  |
| T-15 | Global instruction edit guidance | Inspect contract → isolated tests → implement → verify | T-14 | reviewed | leaf |  |  |
| T-16-fix-preserve-public-identity | Preserve public identity ledger check | Reproduce registry failure → preserve exact line assertion → verify | T-15 | reviewed | leaf |  |  |

| T-17-fix-amendment-test-baseline | Reconstruct amendment fixture input | Reproduce stale fixture → reconstruct source input → verify | T-16-fix-preserve-public-identity | reviewed | leaf |  |  |


## Execution Strategy

Run in dependency order as one sequential stack. Shared files are edited sequentially and each leaf owns one behavioral component or bounded interface. After T-05b RED is committed, the Orchestrator performs the two explicit git mv operations, then the same worker implements consumer and oracle updates before the GREEN commit; source deletions and destinations are staged explicitly. The T-14 Validator independently maps each strict checker diagnostic to an allowed phase-two source or table, retains its evidence and fails the phase for any other diagnostic. Final naming and the final zero-exit condition remain phase 2.

## Decomposition Decisions

The original scope was split at the required recorded boundary before execution. Seventeen phase-one leaves and two composites preserve independently verifiable components. Coherent merge alternatives were rejected for consumer freeze, source provenance and leftover reporting because each has a separately testable result and refusal boundary; metadata migration and global-edit guidance are separate for the same reason. No behavior is merged merely to meet the soft eight-leaf target. The runtime promotion tripwire remains active.

| Subtask | Decision | Signals | Rationale |
|---|---|---|---|
| T-01 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable knowledge inventory relocations behavior cluster with its positive and negative cases. |
| T-02 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable inventory amendment compatibility behavior cluster with its positive and negative cases. |
| T-03 | composite | S1=4, S2=2, S3=2, S4=false, S5=2 | Instruction front matter and capability blocks have independently testable formats and criteria. |
| T-03a | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | Instruction metadata grammar. |
| T-03b | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | Capability-record grammar and diagnostics. |
| T-04 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable instruction name and reference checks behavior cluster with its positive and negative cases. |
| T-05 | composite | S1=5, S2=2, S3=2, S4=false, S5=2 | Adapter declarations and source relocation are independently testable; their combined compatibility is validated after both children. |
| T-05a | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | Adapter record declarations. |
| T-05b | leaf | S1=5, S2=1, S3=1, S4=false, S5=1 | Atomic source moves with all existing consumers. |
| T-06 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable read-only legacy artifact reporter behavior cluster with its positive and negative cases. |
| T-07 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable ownership-safe deployment planning behavior cluster with its positive and negative cases. |
| T-08 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable deployment transactions and recovery behavior cluster with its positive and negative cases. |
| T-09 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable registered project links behavior cluster with its positive and negative cases. |
| T-10 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable active consumer deployment freeze behavior cluster with its positive and negative cases. |
| T-11 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable deployment source revision behavior cluster with its positive and negative cases. |
| T-12 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable unowned leftover reporting behavior cluster with its positive and negative cases. |
| T-13 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable deployment and setup entry points behavior cluster with its positive and negative cases. |
| T-14 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable source instruction metadata behavior cluster with its positive and negative cases. |
| T-15 | leaf | S1=4, S2=1, S3=1, S4=false, S5=1 | One observable global instruction edit guidance behavior cluster with its positive and negative cases. |
