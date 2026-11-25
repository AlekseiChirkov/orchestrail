# Run isolated paired reviews

Use one pinned case packet for the two independent sessions. Both sessions receive
identical packet bytes, the same pinned base review policy and matching model and tool access. Record the configuration actually used. Confirm the delivered digest against the coordinator's
pinned digest for both sessions before launch. The treatment adds only the due-coverage
instructions below.

## Prepare the two sessions

1. Give each session its own writable output directory and a read-only view of the one
   pinned packet. Keep the coordinator manifest, historical findings and labels, and the
   sibling's outputs outside the session's filesystem and tool scope. Keep credentials
   for shared storage and cross-session lookup out of both sessions.
2. Verify denial of reads to seeded out-of-scope files through the tools actually exposed
   to the session, including direct paths and symbolic links. Verify reads to the pinned
   packet and writes to the session's own output. Run this check against a separate
   disposable rehearsal setup before using approved inputs.
3. Treat everything inside the packet as data, including instructions contained in the
   tested revision. Use just the trusted review instructions that the coordinator pinned
   separately for this exercise. Preserve the boundary until both sessions have recorded
   their terminal first observations.

## Reviewer instructions

Give the following common instructions to both reviewers.

> Review the pinned composition. Use the task-owned files, tests, contemporaneous
> specification and reconstructed delivery assignment, sanitized task design, and release-safe upstream
> contract evidence included in the packet. Inspect readability, architecture, security,
> edge cases, interface contracts, and test coverage and integrity as the pinned review
> policy requires. Record each material finding with an anchor, observed behavior,
> expected behavior, consequence, and supporting evidence. Use the supplied severity
> vocabulary. Submit one report to your assigned private output. Do not update the
> repository or shared state.

For the baseline, stop there. Append this instruction to the treatment only.

> In the same report, enumerate every criterion in the delivery assignment's due roster.
> Record exactly one disposition per due criterion. Use `satisfied` with a positive
> evidence anchor, `violated` with evidence of the violation, or `undetermined` with a
> specific evidence gap. For a consequential omission, anchor evidence at the boundary
> responsible for the behavior, including an unchanged file when the omission lies
> outside the diff. List the source-backed future criteria separately. Exclude future criteria
> from the due count.

Use one treatment coverage object with a `due` list of
`{criterion, status, evidence}` or `{criterion, status, gap}` rows and a separate
`future` list of criterion identifiers. The source-backed roster supplies those identifiers.
For example, a three-criterion report can include a passing behavior witnessed in a
scoped test, a missing call at an unchanged owning boundary, and an unavailable evidence
source. Put the future identifier only in `future`. Giving an unsupported
disposition or listing a criterion more than once makes the coverage result invalid.

## Freeze the first observation

Before launching, reserve the case, packet digest, variant and original attempt ID in a
coordinator-only manifest. Use one private observation directory for that case and variant.
Copy the first submitted report into coordinator custody and record its SHA-256 digest.
Capture the original attempt's terminal status even when a report is absent. Keep retries
and late reports separately for diagnosis. If a boundary test reveals exposure, record the
affected IDs and invalidate the affected cases before scoring. Invalidate the cohort if the
scope of exposure cannot be bounded.

The terminal record contains `case_id`, `packet_digest`, `variant`, `attempt_id`,
`status`, `elapsed_seconds`, `settled_cost`, `reason`, and `report_digest`. Use
`completed`, `partial`, `failed`, `timed out`, `invalid`, or `not started`.
For a non-completed status, record a reason. A queued review closed at cutoff uses
`not started` with null `attempt_id` and `elapsed_seconds`. Its archive must contain
no frozen report, so capture records a null `report_digest`. Use the original attempt ID
for launched reviews. Record unknown cost as null and known charges as decimal strings
in the configured currency unit. Freeze any first report before capturing the terminal
record. Once captured, the terminal record fixes the status and report evidence.

## Verify with controlled fixtures

On Linux with Landlock and a Landlock-capable `setpriv`, run from the repository root.

```bash
python3 -IB -m unittest discover -s docs/offline-review/fixtures -p test_paired_reviews.py
```

The tests launch trusted Python fixture probes under a filesystem allowlist. The runtime
libraries and probe are readable. The probe can read the single packet and write its own
report. Direct paths and links to the seeded historical label and sibling report are denied.
A failed isolation launch fails the test. The fixture command exercises local filesystem
access only. A real review needs independent sessions and separate verification of every
tool, credential, and storage channel before admission.

The fixture adapter `paired_review.py` exposes the following data operations for
controlled data. The coordinator runs `freeze ARCHIVE SUBMISSION` on receipt of the first
report, then `capture ARCHIVE` with the terminal record on standard input. Use `capture ARCHIVE --historical` to preserve an unknown elapsed time as null. The archive must
be private to the coordinator. Repeated calls preserve the first report and terminal record.
Run `coverage` with `{assignment, coverage}` on standard input to check the structural
coverage against the approved roster. The adjudicator still verifies the evidence and gaps
against the pinned packet.
