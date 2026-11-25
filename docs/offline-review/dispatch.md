# Dispatch and reconcile offline reviews

## Historical operator procedure

Prepare the cohort and verify rehearsal and isolation. Record the actual model and tools.
Use matching conditions within each pair and record each original attempt ID and packet
digest before launch. Start ready reviews and blinded adjudications as slots become
available. Wait for terminal evidence when capacity is occupied. Reconcile uncertain
attempts after interruption and keep their original identities.

Close when all work is terminal or record an operator stop and its reason. Preserve first
reports, mark queued work as `not started`, unresolved launched work as `partial` or its
observed terminal state, and unfinished adjudication as `incomplete`. Keep late evidence
separate. Record observed time and spend and use null for unknown measurements.
Historical dispatch accepts absent formal approvals, locked settings and hard limits.

Use `python3 -IB docs/offline-review/fixtures/dispatch_fixture.py --historical` to
check a ledger snapshot. Supply the current capacity in `settings.slots` and the
units and attempt states described below. Omit estimated costs, enforced deadlines
and reservation amounts. Set `operator_close` to true after recording a stop
reason in the ledger. The output reports eligible units, occupied slots, uncertain
attempts and terminal updates. The operator owns launch and storage.

## Bounded synthetic fixture procedure

Use a private, file-based coordinator ledger. The operator validates eligibility,
records reservations and launches independent sessions through the approved harness.
Both reviewer variants use the same locked model, tools, time limit, spend limit and
packet. Keep launch and adjudication routing outside reviewer-visible files.

## Lock the experiment settings

Before main dispatch, verify approved cases and a valid rehearsal. Record and lock
the settings version or digest, case selection, authorized model and tools, session
time and charge limits, shared session count and spend ceiling, currency, comparison
deadline, severity and matching rules, decision thresholds and data access policy.
Use elapsed seconds from one recorded comparison start. Preserve the original clock
basis across restarts. Record costs as exact decimal amounts in the same currency.

Enroll one baseline review, one coverage-enhanced review and one adjudication batch
per case. Assign each unit a stable identity. Mark baseline and treatment only in
coordinator records and the private routing instructions. Rehearsal uses six
independent review units across three cases with up to six simultaneous sessions
subject to the same admission checks. Batch readiness depends on both original
observations for that case reaching terminal status. Provide the adjudicator only
the approved packet, opaque findings and permitted historical claims.

## Reserve, launch and reconsider

For each ready unit, determine an enforceable session deadline and a maximum charge.
Queue units without both bounds. Check the following together before launch.

- A shared slot is available. Review and adjudication sessions occupy the same pool.
- Session time and charge fit their per-session limits. The session deadline fits the
  remaining comparison time.
- Settled charges plus all current and unresolved reservations plus the proposed maximum
  charge are at or below the shared ceiling. Count common work, any retry and excluded
  attempts in this ledger even when their costs are excluded from the paired metrics.

Evaluate later ready units if an earlier one cannot fit. When a slot is free at 7 of
10 units, a 3-unit unit fits and a 4-unit unit waits. While the pool is full, wait for
completion or reconciliation and re-evaluate as soon as something changes. A slow
case does not block unrelated ready reviews or adjudication.

Before launch, write one journal entry binding the unit, original attempt ID, packet
digest, launch and deadline times, reserved slot and bounded charge. Durably save
the entry before issuing the launch. Use the recorded attempt identity for any
authorized status lookup. Apply each reservation once and recalculate the remaining
limits before admitting another unit. An eligibility list evaluated on one snapshot
shows which units fit individually. It grants no aggregate reservation.

When a session terminates, preserve its first observation and report separately from
dispatch accounting. Record the verified termination and release its slot. Replace
its maximum charge with the settled amount when known. If the amount is still
unknown, retain the maximum as an unresolved reservation. Record any missing
measurement for scoring. Any authorized retry is separate diagnostic work with its
own resource reservation and cannot modify the primary first observation.

## Recover and close

After interruption, load the original settings, deadline, reservations and attempt
identities. Reconcile each attempt against the approved session harness. If launch or
termination is uncertain, keep its slot and maximum charge reserved. A local timeout
or lost response alone does not prove the session ended. Never resubmit the uncertain
first attempt. Preserve any terminal observations, and reconsider queued work only
after verified evidence changes readiness or available resources.

Close by the comparison cutoff. Earlier closure is possible if all enrolled units
are terminal, or if no queued unit can fit the remaining limits and no pending
completion or reconciliation could affect capacity or the decision before cutoff.
On closure:

- Record each queued review as `not started` and each launched review without a
  terminal first observation as `timed out`. Keep the first report digest where a
  report is already frozen, and record the reason for each non-completed status.
- Freeze unfinished adjudication batches as `incomplete`. Record an evidence gap
  for each pending claim. Keep completed verdicts.
- Preserve all frozen first records. Carry unresolved maximum charges into reported
  spend exposure, and record results arriving after closure separately.

## Verify with controlled fixtures

Run this test suite from the repository root.

```bash
python3 -IB -m unittest discover -s docs/offline-review/fixtures -p test_dispatch.py
```

The verifier `fixtures/dispatch_fixture.py` consumes one synthetic JSON ledger on
standard input. Its `settings` object contains `slots`, `spend_limit`,
`session_spend_limit`, `session_seconds` and `cutoff_seconds`. The remaining fields
are `elapsed_seconds`, `settled_cost` and an ordered `units` list. Each unit has an
`id`, `case_id`, `kind` (`review` or `adjudication`), `variant` (either review
variant, or null for adjudication), `maximum_cost`, `maximum_seconds` and `attempt`.
An unlaunched unit has a null attempt. A started attempt carries its original `id`,
`state`, `reserved_cost` and `deadline` as elapsed seconds from comparison start.
States are `active`, `uncertain`, `terminated` when the outcome is frozen and only
charge settlement is pending, and `terminal` when both termination and settlement
are known. An active or uncertain attempt may carry an already frozen
`observation_status`.

A result shows individual eligibility, wait reasons, occupied slots, uncertain attempt
IDs, total exposed spend and the projected terminal statuses on closure. The verifier
models a snapshot only. The operator maintains launch evidence, authenticates status,
records detailed first observations and persists the ledger.
