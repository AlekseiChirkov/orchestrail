# Task and specification numbering review

The review compared every top-level task state in `.ai/tasks/` with the specification
named by `spec_path`, and compared the resulting pointers with all 27 specification files.
This is a location and numbering review; it does not revalidate delivery or acceptance.

Eleven task directories were renamed to use their specification's three-digit number:

| Specification | Former task number | Current task number |
|---|---:|---:|
| Sensitive data scrub | 00 | 001 |
| Git source of truth | 01 | 002 |
| Run-log vocabulary validation | 02 | 003 |
| Hook-based logging | 03 | 004 |
| Model catalog cache | 04 | 005 |
| Cost and duration telemetry | 05 | 006 |
| Harness Git rails | 06 | 007 |
| Test suite runtime | 06-1 | 008 |
| State tool | 07 | 009 |
| Rules and workflows audit | 08 | 010 |
| Task finalization | 24 | 025 |

Specification 026 points to the completed phase-one task numbered 25. Its local
finalization journal records the original and current task paths, and the finalization
helper requires the current path to retain the original basename. The journal also records
an obsolete pre-renumbering specification path. Renaming that task without a supported
journal migration would break recovery and resolution, so it remains unchanged. The quick
inline-code fix has no `spec_path` and is not a numbered specification task. The remaining
15 specifications have no task state pointing to them; this observation is not a delivery
verdict. Historical references to former paths and frozen audit evidence remain historical.

Specification numbers, requirement identifiers, test results and delivery status were not
changed by this review. The task-finalization implementation remains integrated while its
own archival is separate; the runtime task was closed with its documented scope outstanding.
