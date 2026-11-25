# Specification reference review

## Scope and method

Reviewed active and completed specifications for numbering-related references after the
three-digit migration, using the mapping in `.ai/specs/README.md`. Searched numbered
specification references and quoted report headings, checked local Markdown destinations,
and compared cited requirement and data-model identifiers with their target files. Reviewed
ambiguous matches in context; example paths, report schema labels, historical source
revisions and literal identifiers are not current specification numbers.

## Corrections

- The accepted audit retains `## Blockers for spec 09` as a report-schema heading. The
  migration specification now cites that exact heading, whose historical number refers to
  current specification 011. The accepted report and its schema remain unchanged.
- Corrected stale references to the installer relationship, context-tiering notes, delivery
  prerequisites, model comparisons, packets, reports, telemetry, verification and effort
  records. These are reference corrections, not changes to specification numbering.
- Retained the accepted audit's historical owner codes and report fields, as well as literal
  migration values. A number embedded in an identifier is not automatically renumbered.

## Remaining reconciliation

The former parallel-execution specification 23 was consolidated into the program specification
027. Peer specifications already identify its numbered requirements and data models as
historical and require reconciliation before implementation. The old requirement numbers
cannot be mechanically retargeted to 027: its program contracts are not a one-to-one copy.
That semantic reconciliation remains open; this reference review does not certify the full
behavioral consistency or implementation readiness of the specifications.
