# ADR-0026: Three-digit specification numbers

## Status

Accepted for the current working-tree renumbering; integration evidence is pending.

## Date

2026-11-25

## Context

The owner requested a review of specification names and a consistent `001`, `002`,
and subsequent numbering format, including completed specifications. The prior set
included a zero-based number, a suffix and gaps. The previous ordering decision is
recorded in ADR-0023; the new request changes its numbering convention.

## Decision

Give every current specification a unique contiguous three-digit prefix starting at
`001`, in its prior numeric order, treating the former `06-1` as a distinct record
after `06`. Include completed specifications without changing task, requirement,
audit or PR identifiers. The mapping is in `.ai/specs/README.md`. Keep historically
pinned Git commands pointing to the path that existed at their recorded revision.
New specifications use the next free three-digit prefix across both directories.

Existing human-readable titles remain where they describe the scope; headings and
filenames use the same prefix. This supersedes ADR-0023's decision to keep completed
specification numbers unchanged, while retaining its intent of unambiguous numbering.

## Consequences

The knowledge-inventory check reads a pinned pre-renumbering baseline. Until a
reviewed renumbering commit exists and the ledger is updated to an appropriate
post-renumbering baseline, it reports the old tracked paths as missing; the working
tree alone cannot provide that future commit. The audit tool's existing report-schema
labels remain stable even though its migration-spec lookup uses the new filename.
Installation synchronization and any commit or integration are separate actions.

## Verification

The mapping, local references, the audit-tool lookup and the authoring format require
verification on the renumbered tree. Full inventory validation requires the future
baseline update described above.
