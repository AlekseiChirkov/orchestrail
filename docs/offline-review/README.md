# Run an offline review comparison

Compare the existing review policy with the same policy plus explicit coverage of
source-backed due criteria. Both reviewers see the same pinned packet. An independent
adjudicator assesses opaque findings before the coordinator reveals their variant.

## Prepare and rehearse

1. Identify a repository and contemporaneous sources within the permitted data scope.
   Prepare a private coordinator manifest and a [pinned packet](case-packet.md) for
   each case. Ensure a reviewer can resolve all permitted inputs from that packet.
2. Rehearse with three distinct cases held apart from the main comparison. Prepare six
   [independent review sessions](paired-reviews.md), one per case and variant. Apply
   matching tools and model across each pair.
3. [Check available capacity](dispatch.md#historical-operator-procedure) before launch.
   Keep the manifest outside the reviewer boundary. Verify the actual tools can read the pinned packet
   and write to their own output but cannot read seeded history or sibling material.
   Acquire and freeze each original report and record the attempt's terminal observation.
4. Verify the [blinded adjudication and decision report](adjudication-and-report.md).
   Check packet digest parity, masking, first evidence capture and the scoring
   calculation. Record a failed gate with the affected case and reason, including any
   packet mismatch or verified exposure. If a failed rehearsal could influence a
   repeat, use fresh cases and sessions for the repeat.

## Record readiness and run the historical comparison

Record the rehearsal settings and evidence identities, each case's pinned digest,
all six first observation IDs and statuses, isolation results, and evidence-report checks.
Record the prepared cohort and its source evidence. Start historical dispatch after the
rehearsal passes and historical packets are ready. Record the actual model, tools and
limitations.

For the main comparison, enroll 10–15 source-backed cases from one repository. Keep related
changes together in one cohort and admit each integrated feature milestone once.
Include clean controls, an omitted due requirement and an integrated multi-PR defect.
Keep rehearsal cases out of the main comparison. Record an insufficient-evidence result
if the eligible history lacks the required mix or a traceable delivery scope.

Use the [historical dispatch procedure](dispatch.md#historical-operator-procedure) and
freeze [blinded adjudication and the paired report](adjudication-and-report.md) at closure.
Keep both arms comparable and record deviations.

## Reproduce the synthetic verification

Use Linux with Landlock and a Landlock-capable `setpriv`. Run from the repository root.

```bash
python3 -IB -m unittest discover -s docs/offline-review/fixtures
printf '%s\n' '{"prepared_main_inputs": true}' | python3 -IB docs/offline-review/fixtures/rehearsal_fixture.py --historical
```

The suite combines independent filesystem-constrained probe processes, approved packet
construction, capacity reservations, first-report capture, coverage verification and
blind decision calculation. Its nominal integrated case reserves six review slots,
freezes the six observations, runs three synthetic adjudications and closes at the
shared spend ceiling of nine fixture units. It records three eligible pairs, passes
rehearsal and returns the synthetic historical readiness decision.

For synthetic fault scenarios, set `fault` to `packet-mismatch` or
`historical-exposure` in the fixture JSON. Each scenario blocks main dispatch with its
case ID and reason while preserving the six observations. The `prepared_main_inputs` flag simulates completed case preparation. Verify packet provenance, cohort diversity and isolation in the actual session harness before dispatch. The default CLI mode exercises the original bounded fixture contract.
