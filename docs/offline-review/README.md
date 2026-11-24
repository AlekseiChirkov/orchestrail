# Run an offline review comparison

Compare the existing review policy with the same policy plus explicit coverage of
approved due criteria. Both reviewers see the same pinned packet. An independent
adjudicator assesses opaque findings before the coordinator reveals their variant.

## Prepare and rehearse

1. Approve the eligible repository, evidence sources, data handling rules and scope.
   Prepare a private coordinator manifest and a [pinned packet](case-packet.md) for
   each case. Ensure a reviewer can resolve all permitted inputs from that packet.
2. Rehearse with three distinct cases held apart from the main comparison. Prepare six
   [independent review sessions](paired-reviews.md), one per case and variant. Apply
   the same tool, model, time and maximum charge settings across each pair.
3. [Reserve capacity](dispatch.md) before launching each session. Keep the manifest
   outside the reviewer boundary. Verify the actual tools can read their approved packet
   and write to their own output but cannot read seeded history or sibling material.
   Acquire and freeze each original report and record the attempt's terminal observation.
4. Verify the [blinded adjudication and decision report](adjudication-and-report.md).
   Check packet digest parity, masking, first evidence capture, limits and the decision
   calculation. Record a failed gate with the affected case and reason, including any
   packet mismatch or verified exposure. If a failed rehearsal could influence a
   repeat, use fresh cases and sessions for the repeat.

## Record readiness and run the approved comparison

Record the rehearsal settings and evidence identities, each case's pinned digest,
all six first observation IDs and statuses, isolation and budget results, and
the decision-report check. Use `passed` only after every rehearsal check succeeds.
Record the approved main cohort and locked comparison-settings digest independently.
Main dispatch is eligible only when all three conditions are satisfied. Record
`pending` and list the missing prerequisites whenever any condition is unmet.

For the main comparison, enroll 10–15 approved cases from one repository. Keep related
changes together in one cohort and admit each integrated feature milestone once.
Include clean controls, an omitted due requirement and an integrated multi-PR defect.
Keep rehearsal cases out of the main comparison. Record an insufficient-evidence result
if the eligible history lacks the required mix or approval evidence.

Dispatch ready work within the [locked limits](dispatch.md) and freeze
[blinded adjudication and the paired report](adjudication-and-report.md) at close.
Keep scope, thresholds and disposition rules fixed throughout the comparison.

## Reproduce the synthetic verification

Use Linux with Landlock and a Landlock-capable `setpriv`. Run from the repository root.

```bash
python3 -IB -m unittest discover -s docs/offline-review/fixtures
printf '%s\n' '{}' | python3 -IB docs/offline-review/fixtures/rehearsal_fixture.py
```

The suite combines independent filesystem-constrained probe processes, approved packet
construction, capacity reservations, first-report capture, coverage verification and
blind decision calculation. Its nominal integrated case reserves six review slots,
freezes the six observations, runs three synthetic adjudications and closes at the
shared spend ceiling of nine fixture units. It records three eligible pairs, passes
rehearsal and leaves historical execution pending without approvals and locked settings.

For synthetic fault scenarios, set `fault` to `packet-mismatch` or
`historical-exposure` in the fixture JSON. Each scenario blocks main dispatch with its
case ID and reason while preserving the six observations. Set `approved_main_inputs`
and `locked_settings` to true to exercise the synthetic positive readiness decision.
These flags represent test inputs. A real run requires separately verified approvals,
locked settings and isolation evidence from the actual session harness. The fixture
uses local synthetic cases and does not launch historical reviews.
