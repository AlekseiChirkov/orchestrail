# Adjudicate and report an offline review comparison

Use the pinned case packets, observed comparison configuration, and the coordinator's
first-observation archive. Close the comparison under the procedure in
[bounded dispatch](dispatch.md). Keep preparation, adjudication, and report calculation
in separate coordinator and adjudicator views.

## Prepare an adjudicator packet

For each case whose two original attempts have terminal observations, verify the
observations against the coordinator manifest. Match the case ID, assigned arm, first
attempt ID, and pinned packet digest. Hash each archived first report and compare its
digest to the terminal observation before using any claim. Preserve a missing report or
a failed verification as a gap in the case record.

Keep the original reports, theming, dispatch ledger, arm mapping, run costs, and
historical reference map in the coordinator's private view. Assign opaque finding IDs and
convert reviewer and historical claims to the same template below. Shuffle their ordering.
Remove provenance hints, including arm names, report layout, timestamps, filenames that
identify an arm, and source links that disclose historical outcomes. Keep the reproducible
case evidence needed to verify a claim. Give the adjudicator the pinned case evidence and
the resulting packet, with only the authority needed to decide its claims.

| Adjudicator packet field | Record |
| --- | --- |
| Case and finding IDs | Opaque identifiers that remain stable for this batch |
| Anchor | Path or behavior boundary in the pinned case |
| Expectation | Approved requirement or pinned evidence of the expected behavior |
| Trigger | Conditions needed to observe the discrepancy |
| Observation | Actual behavior and supporting evidence at the tested revision |
| Consequence | Material effect that would follow from the discrepancy |

The adjudicator checks expectation, trigger, observed behavior, and material consequence
against the pinned case. Pool verified historical claims with newly discovered findings.
Group equivalent claims under a canonical ID using the recorded matching approach. Canonical
IDs apply to confirmed defects and equivalent refuted claims. Assign severity using the
recorded convention before the private arm map is disclosed. Every confirmed claim for the
same canonical defect in a case uses the same severity. If the frozen batch contains
conflicting severities, exclude the pair from scoring and record the affected canonical
IDs as evidence gaps. Preserve both first observations and their charges.

## Freeze the adjudication batches

Create one record for every opaque claim in the adjudicator packet. Use this template for
an independently assessed claim.

| Verdict field | Record |
| --- | --- |
| Case and finding IDs | IDs from the adjudicator packet |
| Anchor and evidence | Evidence used to check the claim |
| Canonical ID | Required for a confirmed defect or refuted claim; use null when unresolved without a match |
| Verdict | `confirmed`, `refuted`, or `unresolved` |
| Severity and rationale | Assigned severity and why the evidence supports the disposition |

Mark a batch complete when every claim has an independent disposition. An independent
`unresolved` verdict records a gap and counts as a disposition. At closure freeze an
unfinished batch as `incomplete`. Record the finding
ID and a specific evidence-gap reason for each pending claim and leave its verdict absent.
Preserve assessed verdicts, first observations, and costs for excluded pairs too.

Record the freeze time and digest of each batch in the coordinator archive. Verify the
record against its digest before reporting. Reveal the mapping only after every batch has
frozen. Retain any late evidence in a separate record. A new trial cannot replace an
original report or outcome in the primary comparison.

## Reconcile and score

Include all enrolled cases in the report. For each pair record the status, exclusions and
reasons, first observations and report digests, available costs, batch status, unresolved
findings, pending claim gaps, and coverage gaps. When exposure is identified, exclude the
affected cases and related cases that may share the exposure. Invalidate the cohort when
exposure cannot be bounded. Record scope gaps and packet mismatches explicitly.

Score a pair only if both first observations are complete and valid for the same pinned
packet, the pair is free of known exposure, and all claims have independent dispositions
in a frozen batch. Keep unresolved dispositions separately. Count a canonical
defect or refuted claim once per case and arm. Historical-only claims help adjudicate and
match findings. They do not count as detections by either arm unless that arm reported
them. Count exclusive confirmed defects by comparing the arms' canonical IDs within each
case. Distinguish all confirmed defects from the consequential subset.

Use the signed treatment total minus baseline total for consequential defects, refuted
claims and available elapsed seconds and first-attempt charges. Report observed charges
separately, including partial pairs, excluded pairs, common work and retries.

| Decision report field | Record |
| --- | --- |
| Provenance | Actual configuration and case, first-observation, and verdict freeze references |
| Enrollment | Enrolled count, both-first-observations-completed count, and eligible scored count |
| Pair status | One complete or incomplete entry per pair, with reasons, evidence gaps, and costs |
| Outcomes | Each arm's confirmed, consequential, exclusive, refuted and unresolved counts |
| Measurements | Available per-arm time and charges, signed deltas, observed spend and measurement gaps |
| Interpretation | Exploratory results or insufficient evidence, with reasons |

## Report historical evidence

Use `python3 -IB docs/offline-review/fixtures/paired_report.py --historical` with a normalized
coordinator snapshot on standard input. Include cases and their two frozen first
observations, adjudication and contamination evidence. Common and retry costs can be null
or omitted. The scorer accepts missing settings, deadlines, reservations and measurements.
It retains valid pairs with unknown time or cost and reports the affected deltas as null.
Observed spend is a subtotal and total exposure is unknown. An `exploratory` result
describes observed differences. With zero eligible pairs, the result is `insufficient evidence`.
Record the model, tools, scope uncertainty, cohort composition and configuration differences
alongside the output.

## Verify with controlled fixtures

From the repository root, run the contract tests.

```bash
python3 -IB -m unittest discover -s docs/offline-review/fixtures -p test_paired_report.py
```

The fixture verifier `paired_report.py` accepts a synthetic JSON document on standard
input and emits a report on standard output. Its input is a normalized, coordinator-owned
snapshot assembled after verification. The tests provide repeatable complete, incomplete,
and contaminated snapshots.

The bounded fixture evaluates a cutoff, threshold equality, required measurements and
reserved spend. It returns `trial`, `no trial` or `insufficient evidence` under its
supplied decision settings.

- Supply `settings` with the pinned `digest`, `cutoff_seconds`, `minimum_pairs`,
  `minimum_incremental_defects`, `maximum_incremental_false`, `maximum_incremental_seconds`,
  `maximum_incremental_cost`, and `consequential_severities`. The fixture's
  `unresolved_policy` defaults to `record`. Use `insufficient-evidence` when the locked
  policy requires a decision to wait on unresolved dispositions in scored pairs.
- Supply `cases` with `case_id`, `packet_digest`, `contaminated`, and `coverage_gaps`.
  Include the two `observations` by arm in the [terminal record format](paired-reviews.md).
  A never-dispatched review projected at cutoff may have a null `attempt_id`.
  The coordinator supplies `finding_variants` after freeze. Include `adjudication` with
  `status`, `frozen_at` in elapsed seconds, `verdicts`, and `pending_claims`. Each verdict
  has `finding_id`, `verdict`, `canonical_id`, `severity`, and `rationale`. Pending
  claims carry `finding_id` and `reason`. Historical-only adjudication records are
  retained in the archive and omitted from this scoring projection.
- Supply the `cohort_contaminated` flag, `common_cost`, `retry_cost`, and
  `unresolved_reservations` amounts. Express amounts as decimal strings in the single
  locked currency unit.

The fixtures record independently unresolved claims as gaps while allowing their pairs to
remain eligible. They exercise these calculations on verified record shapes. Operator
verification of signatures, archives, isolation, and source approval comes before scoring.
