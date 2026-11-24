# Prepare an offline review case

A case is one pull request or one integrated feature milestone. The two review variants
use exactly the same approved packet. Keep the coordinator record and reviewer packet
in separate locations. Give review sessions access only to the reviewer packet and their
assigned instructions.

## Select the case and verify approvals

1. Assign the case an opaque ID. Record its feature group and cohort in the coordinator
   manifest. Keep a feature group in one cohort and count an integrated milestone once.
   Use three distinct rehearsal cases. For a historical comparison, reserve 10–15 approved,
   disjoint cases from one approved repository, including clean controls, a missing due
   requirement, and a defect that appears only after integration.
2. Pin readable base and tested trees. For a pull request record base, head, and target
   identities. For a milestone record the target, base, integrated tree, and all constituent
   revisions. Recover the scoped diff, tests, and task-owned paths for that composition.
3. Resolve the approved specification and every binding annex to exact contents. Resolve the
   approved delivery assignment to a version and due/future criterion rosters. Verify both
   approvals against trusted sources and the exact versions. Retain the approval references
   privately. Exclude a case with missing approvals, inaccessible annexes, or mismatched
   versions, and record the case ID and the reason for exclusion.

## Pin the packet

Use a JSON object for the reviewer packet. Record the opaque `case_id`, `composition`,
`base_tree`, `tested_tree`, scoped `diff` and `tests`, `owned_paths`, sanitized
`task_design`, release-safe `upstream_contract`, pinned `review_instructions`,
approved `specification`, and approved `assignment`.

- Set `composition.kind` to `pr` with `base`, `head`, and `target`, or `milestone`
  with `base`, `target`, `integrated_tree`, and an ordered `constituents` list.
- For the synthetic fixture, represent each readable tree as an object mapping its
  workspace-relative file paths to text. Use an empty object for a readable empty tree.
- Put specification text in `specification.content` and each binding annex in
  `specification.annexes` as an object with `name` and `content`. Record the specification,
  individual annex and assignment digests in the private admission record.
- Put the approved assignment's `version`, `due`, and `future` rosters in the packet.
  Keep each criterion identifiable across the reviewer and comparison records.

Inspect all contents and tool-visible paths for references to historical findings, previous
reviews, later fixes, comments, and outcome-bearing task state. Remove those references.
Keep source references, approval references, labels, dispatch and variant mapping, first
observation identities, and resource reservations in the private coordinator manifest. In
the case of uncertain masking or unusable evidence, exclude the case and record the reason.

Serialize the packet as UTF-8 JSON with sorted object keys, compact separators, unescaped
Unicode, and no trailing newline. Preserve list order. Hash the resulting bytes with SHA-256.
Record the digest once and reference it for both variants. Compare the digest of the packet
actually delivered to each review to the pinned digest before admitting either review. Keep
the pinned packet read-only and retain admission and excluded case records with the coordinator.

## Verify on synthetic data

From the repository root, run:

```bash
python3 -I docs/offline-review/fixtures/test_case_packets.py
```

The fixture adapter `prepare_case.py` reads a JSON object with a pre-sanitized `packet`
and a private `coordinator` object. Supply `coordinator.approvals.specification` and
`coordinator.approvals.assignment` as `{reference, digest}`, using the same canonical
JSON digest for each approved value. The fixture adapter verifies that the synthetic records
match those digests. The operator establishes trust in the approval and sanitizes the
content before running a real review. Treat the full adapter output as coordinator-only
and expose just its `packet` field to reviewers.
