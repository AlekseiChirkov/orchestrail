# ADR-0026: Three-digit specification numbers

## Status

Accepted; branch integration remains a separate action.

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

The knowledge-inventory check reads a pinned baseline. The identity ledger now names
`bda0f3e928c119da5a7d8d108c6daf89a4777b0f`, the commit containing the reviewed
renumbering and the owner-approved removal of the superseded source file. The audit
tool's existing report-schema labels remain stable even though its migration-spec
lookup uses the new filename. Installation synchronization and integration are separate.

## Verification

The mapping, audit-tool lookup, authoring format and knowledge inventory were checked
on the renumbered branch. The full contract suite passed 725 checks with 2 skips and
no failures. Final contextual-reference edits were applied during the run; the inventory
and authoring checks were repeated afterward.
