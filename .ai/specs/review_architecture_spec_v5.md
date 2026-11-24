# Specification-driven, risk-based pull request review

**Edition 5.0 · Architecture and acceptance contract for a single-host pilot**

## 1. Purpose and design decisions

Find distinct, consequential defects before the first useful report on a pinned change. Evaluate the behavior promised by the approved feature specification, including behavior entirely absent from the diff. Preserve precision, confidentiality, resource ceilings and an honest account of incomplete work. Among configurations that meet the quality and latency gates, select the lowest total cost. The owner sets numeric acceptance thresholds before the pilot.

Edition 4 already included linked requirements, evidence validation and reversible grouping. Two decisions complete that design. First, each review pins an authoritative specification and an explicit delivery scope and accounts for every applicable acceptance criterion. Second, every internal candidate receives a recorded adjudication before external publication. Establishing that a defect exists and deciding when it warrants action are separate decisions. The service recommends action and can emit a configured revision-bound check. The project owner retains merge, waiver, specification-change and remediation authority.

## 2. Components and authority

| Component | Inputs and responsibilities | Output and authority |
|---|---|---|
| Intake and context builder | Pin revision, integration state, specification, delivery plan and policy. Build a change manifest and bounded source index | Immutable run envelope, provenance, known search limitations |
| Deterministic supervisor | Apply rules, validate plan and evidence contracts, schedule across PRs, enforce limits, drive adjudication and freeze report | Only component allowed to change review state. Publication uses a separate restricted adapter |
| Lead reviewer | For substantive changes, read purpose, raw change, assigned criteria and relevant source. Design scenarios, identify omissions, directly investigate complex paths and resolve semantic questions | Scoped jobs and evidence. One logical lead; strong calls are budgeted individually |
| Workers | Tools, narrow inexpensive reviewers, blind explorers, cross-component reviewers and validators | Private structured results. Workers can propose jobs and cannot dispatch, publish, change thresholds or edit the PR |
| Feature ledger and report store | Transactional local tables, immutable source/evidence artifacts, dispatch and delivery journals | Reconstructible per-PR and integrated feature views |

Use a modular application, one transactional store, bounded worker processes and a model gateway on one host. Model names are deployment settings. Measure the routes on the intended repository and hardware.

## 3. Intake, specification authority and scope

Pin project, PR, receipt time, absolute deadline, base, head, merge base, tested integration tree where available, dependency revisions, policy/tool versions, access domain and resource profile. Record whether each claim applies to the branch, integration tree or both. A failed merge-tree construction creates an integration gap. Distinguish introduced, activated/aggravated, integration-only, pre-existing and attribution-unknown defects using comparable base evidence when needed.

**Required input for a feature PR.** Resolve the approved spec through trusted project configuration, an approved issue-to-spec mapping or an owner-approved manifest. Store its project-scoped canonical identity, immutable revision or content digest, source anchors, approval evidence, owner and access scope. Capture referenced normative annexes and their versions. Verify identity, access and approval separately. A path or link in the PR description is a discovery hint. If the spec lives in the same PR, compare with the last approved baseline and accept the new text as normative only with separately verified approval of that exact revision. Report proposed changes to expected behavior explicitly.

**Interpretation.** Distinguish binding requirements, acceptance examples, recommendations, non-goals and explanatory prose. Store each binding clause with a stable project-scoped criterion key, exact source span, expected observable property, preconditions, relevant exceptions and applicable milestone. If a document has no identifiers, derive versioned anchors and persist cross-version mappings. Preserve original clauses and qualifiers when splitting compound criteria. A model may draft a mapping; trusted source text governs. Ambiguous wording, conflicting authorities, inaccessible annexes and uncertain extraction go into a clarification record with competing interpretations. Only an authorized owner can settle a genuine product decision. A confirmed requirement violation needs a sufficiently clear applicable obligation.

**Incomplete inputs.** Continue independent code, compatibility and risk checks even when a requested spec cannot be accessed. Report specification conformance as unknown and mandatory coverage as incomplete where affected. An approved non-feature or mechanical exemption records the trusted policy rule and evidence of applicability. A clean diff or an empty list of extracted criteria cannot exempt a feature PR.

## 4. One specification, several PRs

For each approved spec revision maintain a delivery manifest. Each criterion or independently testable slice has a responsible milestone or PR, dependencies, acceptance point (this PR, integration milestone or release), safe intermediate-state conditions and source of approval. A PR can implement multiple criteria; a criterion can span multiple PRs. For stacked changes pin the parent revision actually used. A claimed dependency must be present in the tested composition before its behavior is credited. An external issue can identify future work but cannot by itself change an approved acceptance point.

| Scope of criterion at this snapshot | Required treatment |
|---|---|
| Due in this PR | Verify the observable behavior in the pinned applicable tree, including omissions and disallowed behavior. Record conformance or evidence gap |
| Shared across PRs | Verify this PR's named slice and boundary contract. Keep feature-level behavior pending until tested in the required integrated composition |
| Due later under an approved plan | Record milestone/owner and verify any intermediate invariants now, including compatibility and feature-flag behavior. Future scope does not excuse a current regression |
| Previously delivered | Reuse only still-valid evidence. Recheck if changed consumers, contracts, dependencies or configuration affect the earlier behavior |
| Unassigned, disputed or missing plan | Record uncertainty. Do not invent a deadline or flag every future feature as a current omission. Mark affected conformance/coverage incomplete |

For a declared single-PR delivery, the approved intent to deliver the whole feature can assign all binding criteria without a separate hand-authored table. For multiple PRs the mapping may come from existing approved planning artifacts. Machine suggestions carry provisional status until backed by that source. Record explicit exclusions and reasons. Check for orphan criteria, duplicate ownership with inconsistent expectations, missing dependencies and cycles.

**Feature acceptance.** On an integration or final milestone review, reconcile all due criteria against the actual integrated tree, including cross-PR interactions and removals. Trigger this check from the trusted milestone event, or explicitly request it if the integration event source is unavailable. Preserve original PR findings and subsequent integration observations separately. A union of green PR reports cannot mark the feature complete. Concurrent PR updates append snapshot-bound observations; advance the current feature view only against the expected ledger version and matching spec/target. Recompute on conflict. Record superseded revisions and re-open affected criteria.

**Worked example.** An approved order API specification requires one order per tenant and idempotency key, plus replay of the original response after a client timeout. The approved plan assigns the scoped unique constraint and backwards-compatible migration to PR A. PR B owns the HTTP replay behavior and activation. On A, absence of HTTP replay is planned work. A global unique constraint across all tenants is a current defect, even with the endpoint disabled, if it violates A's storage contract. On B, test replay against A's actual schema and a reachable existing order. At the final milestone test the complete retry across request handling and durable state in the integrated tree. A link to a passing migration test supplies no evidence about replaying the response.

## 5. Planning and coverage in both directions

1. Enumerate binding source clauses independently of the diff. Produce a source-to-criterion inventory, marking unmapped passages and ambiguous extraction. Per clause record scope assignment, scenarios, expected evidence and status. For critical or long specifications verify inventory coverage in a second pass against the original text, including annexes and cross-references.
   Gate inventory completeness for every spec using a separately grounded check. Build a source-unit manifest from the pinned original, including table cells, nested notes, examples containing binding text, annexes and unresolved references. Every meaningful unit must map to criteria or have a supported nonbinding classification. Use a verified structured requirements source or a separate source-grounded review of classifications for prose. Cache the verified mapping by exact spec, annex, policy and authority fingerprints. Merely counting the first extractor's rows is insufficient. Unknown units keep affected coverage open.
2. Map each due criterion to user-visible entry points, implementation paths, states and credible tests or traces. Search for entirely missing behavior. Test presence under the supported conditions and check boundaries, failures and forbidden outcomes when applicable. An omission can be anchored to the criterion and the owning entry point even when there is no added line to annotate. An empty text search alone cannot establish absence.
3. Work in reverse from changed behavior to its requirement, supported rationale or independent technical invariant. Unmapped code can be a legitimate refactor, enabling change, out-of-scope behavior or unexplained change. Investigate consequence before proposing a defect. A spec's silence cannot override a known data-integrity, privacy or compatibility invariant.
4. Combine the criterion obligations with mandatory risk rules. They can share a job or evidence while retaining independent acceptance records. Plan from the raw diff, changed-file manifest, known consumers, rollout context and authoritative text. Verify the plan against both inventories before finalization. Record new risks even if no spec sentence mentions them.

Each obligation has a property, scope, scenario, assumptions, evidence contract, mandatory/optional flag, independence requirement and stop condition. Track applicability, execution, explored scope, property outcome and evidence sufficiency independently. A violation can be confirmed while sibling cases remain unexplored. Per-criterion conformance takes the values satisfied in scope, violated, undetermined, or justified inapplicable. Future scope is a scheduling decision, never evidence of satisfaction.

## 6. Risk routes, catalog and independent discovery

Version each rule with applicability signals, source coverage, evidence types, exclusions, required depth, independence and tested fixtures. Combine rules by union. A one-line tenant configuration change can require deeper analysis than a large mechanical rewrite.

| Route | Minimum execution |
|---|---|
| Mechanical | Positive equivalence proof across the entire affected semantics, directives and metadata, plus scope/exemption evidence. Unsupported inputs prevent this shortcut |
| Local | Known bounded impact, applicable tools and narrow specialist; stratified audits of apparently clean outcomes |
| Substantive | Lead plans questions from the specification and change. Start ready rule checks in parallel. Investigate complex questions directly when decomposition would duplicate context |
| High or critical | Mandatory deep scenario, independent discovery using raw sources before seeing the lead's plan/findings, and independent evidence for consequential conclusions. Unresolved material scope remains visible |

Starter catalog, grouped for readability:

| Family | Review directions |
|---|---|
| Behavior | Functional logic; requirements completeness; input boundaries; errors and partial completion |
| Trust | Authentication and session lifecycle; authorization and tenant isolation; untrusted input at sensitive operations; secrets, cryptography and privacy |
| State and delivery | Data integrity; transactions; concurrency; retries and idempotency; events and queues; distributed consistency; caching |
| Interfaces and values | Schema and migration; contracts and compatibility; numeric precision and money; time and time zones; encodings and serialization; pagination and query ordering |
| Runtime and maintenance | Resource cleanup and cancellation; performance and availability; dependencies and build; configuration and rollout; observability; tests and regression; approved project constraints |

Apply the basic functional, boundary, error, regression and dependency checks to executable changes. Add domain-specific rules as needed. For migrations inspect both versions during rollout; for retries inspect state across partial success; for public contracts inspect producer and supported consumers. A planning model cannot cancel a mandatory check. Unknown dynamic wiring, unsupported languages, missing consumers and parser truncation require bounded investigation or an explicit gap.

## 7. Tasks, context and experiments

Start an obligation as soon as its dependencies are ready. Group questions sharing evidence method and source context, while retaining separate answers. Split work when a worker can establish an independently useful fact. Assign one reviewer the whole scenario when a defect could arise between individually correct components. Preserve a blind exploratory lane for critical changes, with direct access to pinned source and entry points independently of the shared index. Sample clean routing decisions, negatives and rejected candidates with logged selection probabilities. Independent reviewers record their own trace before seeing others' conclusions.

Context proceeds from focused question, relevant source and exact criterion to neighboring contracts, callers, consumers and tests, then bounded read-only search. Report unsupported connections, hidden dependencies, truncated output and missing context. Critical checks specify minimum inputs in policy. Share the index, deterministic artifacts and narrowly relevant context; meter all model input actually billed. Tag confirmed facts separately from assumptions. Align grouping with measured context duplication, correlated misses and response truncation.

A worker returns run/snapshot, task/attempt, method/version, one answer per scenario, checked scope, evidence, criteria met, candidate defects (including incidental discoveries), gaps, dependencies and bounded follow-up proposals. The runtime records actual reads and tool observations. Validate schema, generation, access, artifact references and completeness. Accept independently complete portions of truncated output. Missing answers remain open. Technical retries and substantive rechecks have separate limits. Cap total jobs, descendants, rounds, expansion, output and retries; check dependency cycles.

Where permitted, run bounded deterministic checks such as type analysis, focused contract tests, differential base/head checks, property checks or simulated ordinary failure transitions. Establish the expected outcome from a trusted contract; a changed result can be intentional. Preserve inputs, environment, versions, oracle, outputs and limitations. Environment failure, flaky output, invalid test assumptions or a passing test outside the affected scenario cannot confirm or refute a defect.

If lead planning fails, continue rule- and criterion-derived obligations, record the missing semantic pass and use a bounded fallback when the profile permits. A neutral assignment specifies property, scope, question, assumptions, method/depth, required evidence, escalation condition and resource envelope. Deduplicate jobs only when these fields, snapshot and independence needs match. For critical negative conclusions, perform the required independent check even when no candidate was produced. A selected post-report audit cannot retroactively improve first-report metrics.

## 8. Candidate adjudication before publication

Workers submit internally. One programmatic adjudication step is mandatory for **every candidate**. The supervisor may complete it directly when a configured rule can verify all required facts, invoke the lead for a bounded semantic check, or dispatch an independent validator. The budget controls the depth and timing of validation. A candidate that cannot be settled by the cutoff retains an explicit unresolved disposition.

| Stage | Decision and persisted evidence |
|---|---|
| Identity and grouping | Verify run, snapshot, source anchors and evidence access. Reversibly group by violated property, root cause, reachable path and conditions. Preserve original IDs, differing impacts and all evidence; allow later split |
| Factual assessment | Check the current applicable expectation, reachability, actual behavior, impact, counterevidence and PR attribution. Record confirmed, refuted with counterevidence, or unresolved with the missing fact. Failure to reproduce alone is unresolved |
| Quality of the proposed comment | Check location or missing-behavior anchor, clear trigger, expected and observed effect, material consequence and evidence link. Rewrite vague wording from verified facts. Verify any suggested remedy separately, or omit it. A poor comment does not erase a real defect |
| Timing and action | Apply the trusted gate and scope policy to the assessed fact. Record severity, current exposure, milestone, dependency, action, reason, authority and any required owner follow-up |
| Visibility and audit | Put a unique actionable item in the appropriate report section. Link duplicates to their canonical item. Retain originals, rejected claims, decision evidence and unresolved items in the access-controlled ledger |

**Choose the cheapest sufficient validator.** Direct verification is suitable for a reliable pinned tool result with a trusted oracle and a deterministic scope/action rule. A narrow independent validator handles an ordinary contested behavior. Use stronger cross-component analysis for conflicting traces, unclear attribution or expensive false positives. A critical blocker requires the independent method specified by policy; the candidate's author cannot serve as its sole validator. Supply the independent reviewer the property, anchors and relevant source, withhold the proposed conclusion until its initial trace is committed. Check refutations and discretionary deferrals by stratified audit. A validator can introduce a new hypothesis only through the ordinary candidate path.

| Situation | Action decision |
|---|---|
| Confirmed, due now, violates a configured merge gate or mandatory intermediate invariant | Recommend **fix before merge** and emit the configured failure for the exact snapshot |
| Confirmed, material and attributable to this PR, outside the blocking policy | Recommend **fix in this PR** with rationale; advisory unless project policy elevates it |
| Confirmed, safe to defer under approved policy | **Track for follow-up** with affected scope, owner or responsible role, target milestone/review date, explicit rationale and residual risk |
| Confirmed but proposed deferral lacks authority, owner, safety evidence or required exception | **Owner decision required**. Preserve any existing blocking decision while awaiting authorization |
| Future deliverable is legitimately absent; intermediate state meets its contract | Record planned scope in the matrix. Do not create a defect for future work. A separate actual regression is independently actionable |
| Evidence refutes the claim, or another record captures the same cause | **Dismiss with evidence** or **link duplicate**. Preserve the decision record and all relevant support |
| Ambiguous requirement, materially conflicting evidence or time ran out | **Clarify or investigate** with named missing evidence. Material mandatory uncertainty prevents a successful coverage gate |

Pre-existing debt and optional improvements appear separately when project policy requests them. Distinguish ordinary permitted follow-up from an exception to a gate. Any gate exception requires trusted owner authorization referencing finding, snapshot/scope, rationale, expiry and follow-up. It changes permitted action only within that scope. It cannot change factual conformance or make missing evidence sufficient. A model cannot silently defer a blocker, create external tickets, edit the spec, or apply a fix. A verdict does not need a guessed percentage of confidence.

**Twenty-candidate example.** Four duplicate submissions link to canonical records, leaving sixteen distinct claims. Five are refuted, three remain unresolved and eight are confirmed. Of the eight, two block merge, three warrant a nonblocking fix in this PR, two qualify for tracked follow-up and one awaits an owner decision. The first report shows these sections, any material unresolved gaps, and a reconciliation of all twenty inputs. Actual candidate counts are independent of criterion coverage. Grouping never consumes a candidate without a traceable terminal or pending disposition.

**Freeze invariant.** Assign a durable receipt ID to every accepted original submission. Close the input epoch at a transactional cutoff and seal a decision row for each receipt in that epoch. The row contains factual verdict, comment-quality outcome, action/timing, reason, decision authority and evidence, with explicit pending or inapplicable reasons where necessary. A duplicate points to one canonical predicate and has its own check for different reachability, impact or scope; split it if those differences change the decision. A confirmed blocking instance remains blocking regardless of grouping or an advisory decision on another instance. Enforce conservation of receipt IDs, unique ownership of originals and valid decision references for all external findings. Capture complete unresolved rows automatically at timeout. Later receipts enter a continuation epoch. If invariants fail, withhold substantive publication and any passing check; the watchdog may deliver a technical incomplete report.

## 9. Resources, money and deadlines

Use a host-wide atomic allocator for all runs and projects. Configure host/service limits and OS/controller/finalizer headroom. Track measured pressure as well as outstanding resource reservations. Bound the entire descendant process tree with aggregate, per-run and per-job limits for memory, CPU, process count, disk and output. On Linux use delegated cgroups plus quota-limited scratch storage. If the isolation required by a job is unavailable, select a permitted method or record a gap. Include local inference and accelerator memory if applicable.

The model gateway accounts for the provider's actual shared concurrency and rolling request/token quota buckets. Reserve conservative uncached input and maximum billable generation, including reasoning according to the provider's tariff. Store the price version, ceiling and realized charge. If maximum liability cannot be enforced, disable that route under a hard spend cap. Uncertain external calls retain their occupancy/liability until reconciled or conservatively accounted for. A retry needs its own reservation.

Use rolling groups. When a ready job fits measured and reserved capacity, permissions, spend and the downstream deadline, dispatch it without waiting for siblings. Protect separate capacity for required discovery, candidate validation and local finalization. Schedule backwards from the receipt-based deadline, allowing time for queueing, provider tails, validation, persistence and delivery attempts. Never borrow a protected slot whose release cannot be bounded. This applies even to mandatory discovery sharing a slot with validation. Record best-effort limitations when quota isolation is unavailable. Give waiting PRs fair shares and age required work; bound intake and account for overload outcomes.

Batch compatible validations; prioritize consequential candidates and required evidence without allowing candidate floods to starve unfinished discovery. Stop optional work at cutoff, commit verified portions and freeze unresolved material work as gaps. The watchdog can seal a minimal local report while the host/store operate. Pilot hypothesis: ordinary PR p95 within five minutes, local report cutoff eight minutes from receipt. Measure actual delivery separately. Provider/host outages and oversized PRs belong in the workload denominator. No configured ceiling is raised by a model.

At intake and after material cost, availability or timing changes, check the feasibility of the minimum required route with its downstream validation and finalization. When already infeasible, record the reason immediately and switch to the partial-report path. Dispatch only independently useful work that still fits and preserves finalization. At both run and shared budget scopes require settled spend plus active reservations plus uncertain liabilities plus the proposed maximum charge to stay within the hard ceiling. These ledger buckets are disjoint. Include paid tools, metered subcalls, retries and provider-specific fees; broker or disable calls with uncontrolled nested charges. Report settled cost and an upper bound including outstanding liabilities.

For each consequential negative or satisfied criterion, record checked paths, preconditions, the authenticated source/evidence and uncovered paths. Critical negative checks must satisfy the particular property's independence contract. A general blind discovery pass cannot substitute for verification of a consumer it never examined.

## 10. Persistence, invalidation and security

Store runs, source snapshots, criterion versions and assignments, obligations, tasks, attempts, evidence, candidates, canonical findings, decisions/authorizations and report records. Join tables support many-to-many traceability. Maintain append-only decision history, resource ledger and delivery outbox. Partition caches, artifacts, prompts and logs by project and access domain.

Atomically reserve and journal dispatch intent, attempt generation and lease before a remote call. Commit validated results and local transitions together. Check the generation before accepting completion; retain late artifacts and uncertain costs separately. Recover the original deadline, reservations, process trees and durable work after restart. Use provider idempotency/status if available; never assume an expired local lease freed a remote slot or prevented charging.

Reuse deterministic results only when relevant snapshot inputs, toolchain, config, contracts and transitive dependencies match. Treat semantic negatives conservatively across revisions. Invalidate affected conformance and action decisions on spec/plan changes, approval withdrawal, waiver expiry, dependency updates, newly observed consumers or target changes. Rebinding an anchor requires checking clause meaning and qualifiers, not only text similarity. Revalidate the current feature view on changes, preserving historical findings and the immutable first report.

Treat repository text, specs, linked content and tool output as untrusted operational input. Only verified approvals can establish product authority; even an approved product requirement cannot grant execution privileges. Enforce least privilege, read-only snapshots, command allowlists, resource limits, isolated disposable tool environments, restricted network/secrets and controlled artifact capture. Apply project rules on permitted model providers, redaction, data residency, retention and deletion. Keep credentials and publishing privileges outside workers. When redaction removes necessary evidence, report the limitation.

Maintain a versioned project knowledge register for authoritative requirements, verified facts, hypotheses, conflicts and superseded entries. Record source, scope, prerequisites and invalidation rules. After a fix, recheck the root cause, affected scenarios and new impact area. Classify late findings as initially missed, subsequently introduced, pre-existing or undetermined before assigning them to quality metrics.

Run untrusted code and parsers without access to control sockets, host credentials, production services or provider keys. Deny network by default, fetch approved dependencies through a separate controlled path, reject filesystem escapes through links or archives and prevent project install hooks from executing during trusted setup. Use a verified isolation boundary suitable for mutually untrusted projects, or disable execution where it is unavailable. Resource limits alone do not establish isolation. Stop dispatch and external data transfer on a detected boundary violation; retain safe evidence of the incident and withhold a successful status.

## 11. Reporting, freshness and external effects

Freeze the report and delivery intent in one transaction. Show the reviewed revisions, tested integration tree, spec/plan digest and approval, scope and criterion matrix with evidence; unique confirmed defects by action and severity; owner decisions, permitted deferrals and covered future work; uncovered mandatory checks; reconciled candidate counts; cost, resources and receipt-to-freeze/delivery times. An external defect statement must have confirmed factual evidence, a passing comment-quality check and an authorized disposition, which may itself request an owner's ruling on remediation. For unresolved matters publish the verification gap in neutral terms, for example “replay after timeout remains unverified because the consumer contract was unavailable.” Keep probable theories, refutations and per-candidate reasoning in the access-controlled ledger. An unpublished confirmed claim awaiting an adequate comment remains accounted for and cannot enable a passing gate. Inline comments are reserved for grounded actionable claims. Report omitted behavior against a source criterion and responsible boundary if a line comment would mislead.

Keep execution, policy coverage, code findings, spec conformance, proposed action, feature acceptance, freshness and delivery independent. A fully performed review may establish a violation. A clean but unfinished review is incomplete. A successful machine check requires project gate compliance, sufficient required coverage, applicable spec verification and a fresh matching snapshot. Only approved exceptions change gate behavior. First-report contents stay immutable; later evidence yields an explicitly linked correction or new run.

Publish through a restricted adapter with a stable key for project/PR/snapshot/report. Prefer conditional writes or revision-bound checks. Check freshness including externally stored spec and scope at publication. If the platform cannot safely attach a current passing status, retain a labeled snapshot report and withhold that status. On ambiguous delivery reconcile external state before retrying. Record a local report, delivered report and late delivery as different outcomes. External ticket creation, remediation, merge or spec edits require separate authority.

**Authoritative gate identity.** Key eligibility to the complete tuple of head, target/integration revision, spec and approval versions, delivery plan, policy and applicable waiver versions/expiry. New approvals, withdrawals, target updates and waiver expiry invalidate previous eligibility even with the same PR head. Reconcile change events and missed events by polling, and retire superseded checks. A project that uses this system to authorize merge must atomically bind its merge decision to the still-current tuple or use an equivalent conditional gate at merge time. A head-only platform check and asynchronous revocation cannot prevent the race. Where merge-time enforcement is unavailable, expose advisory snapshot results only.

Evaluate the machine outcome deterministically: a confirmed unwaived blocking condition yields fail even if an external comment is held for repair; otherwise a mandatory evidence gap yields incomplete; otherwise apply the configured passing criteria. Persist independent gap indicators even on failure. Delivery and freshness never turn a failed or incomplete assessment into a pass.

## 12. Experiments, rollout and acceptance

Start with tools alone, tools plus cheap workers under rules, the same workers with lead planning, a capable singleton with equivalent context/tools, and the two-lane architecture. Ablate requirement mapping and semantic adjudication independently **offline** on the same held-out tasks. Compare at matched cost, latency and precision. Use original PR states without future fixes/labels, real defects, clean controls, seeded rare cases, multi-PR series and independently adjudicated new discoveries. Split related changes by repository or time; treat a feature series as one cluster in uncertainty estimates.

Measure distinct severity-weighted first-report recall and critical recall by class, precision, missed binding clauses, erroneous current-PR omissions, unsafe deferrals, false blockers, wrongly dismissed defects, action agreement against independent owner/policy labels, human triage time, peak RAM, complete coverage, on-time delivery, latency and total cost including failed work. Separate defects found internally from actionable findings actually delivered. Count overloaded, partial, cancelled and undelivered reviews. Log random audit selection probabilities. Compare methods on matched work; raw yield of difficult escalations is biased. Lock absolute floors, allowed recall margins, confidence method, rare-class sample sizes, availability, spend and latency before holdout evaluation. Compare to one achievable reference configuration using simultaneous paired bounds. Retain simpler configurations where quality is preserved. No route is production-qualified solely from a design review.

**Rollout.** First validate the central hypotheses with replayable snapshots and blinded labels. Build a safe single-host core with trusted spec intake, delivery manifest, simple fixed routing, two-way coverage, independent critical checks, adjudication, isolation, hard caps, recovery and outbox. Then improve context, experiments, cross-revision reuse and scheduling with measured ablations. Defer learned routing and distributed workers until workload evidence supports them.

Include a capable singleton followed by one independent blind pass as a simpler alternative to a specialist pool. Compare quality under equal total spend and deadline, then compare total cost at matched quality. Lock the defect matching rule before evaluation and have blinded adjudicators pool previously unknown findings into common labels for all configurations. If no reference meets the predeclared absolute floors, no production route is qualified.

| Acceptance fixture | Required observable outcome |
|---|---|
| Approved single-PR criterion entirely absent from code and diff | Criterion gets a review obligation. Supported omission can become a located confirmed finding |
| Two PRs implement one spec; first lands behind a flag | Current slice and intermediate safety are reviewed. Future activation remains pending |
| Each stacked PR passed alone but consumer and producer disagree after integration | Final acceptance requires combined evidence and retains integration defects |
| PR edits its own spec or claims an unapproved postponement | Trusted baseline governs, disputed amendment is surfaced |
| Missing or inaccessible normative source, unassigned clause, ambiguous exception | Other checks proceed; affected conformance stays unknown |
| Short spec contains a binding exception inside an example | Source reconciliation detects the missing mapping or leaves coverage unknown |
| Critical reviewer reports success despite missing a material consumer | Unrelated exploration cannot close the specific negative; targeted evidence or a gap is required |
| Spec or dependency changes while two reviewers write results | Older evidence remains addressable; current ledger cannot advance on stale inputs |
| Validator gets twenty candidates including duplicates, weak wording and a disputed blocker | Every candidate is accounted for; genuine claims survive wording repairs; unresolved material matters are visible |
| Flaky experiment or validator fails to reproduce | No refutation without adequate counterevidence |
| Probable defect at cutoff, poor wording on a real defect, candidate arriving during freeze | Publish only the neutral open check for the probable claim; preserve the confirmed fact during wording repair; receipt epoch determines first-report membership |
| Two grouped claims differ in affected tenants or severity | Split or separately adjudicate their impacts; a blocker cannot inherit another instance's deferral |
| Approval withdrawn, plan or target changes, or waiver expires before, during or after publication on identical head | No previous pass can authorize a merge against the changed tuple; snapshot report remains historical |
| Confirmed high-impact issue proposed for later without authority | Existing gate is preserved; owner decision and risk are visible |
| Truncated worker output or one confirmed flaw in a grouped assignment | Unanswered scenarios stay open |
| Blind discovery and rejected-candidate audit | Initial context excludes earlier conclusions; required audits cannot be cancelled by the lead |
| Candidate flood, multiple PRs, hanging provider, cancellation with uncertain charge | Protected search/finalization survive, caps hold, unknown liabilities persist and incomplete work is reported |
| Minimum route already exceeds time left, or a tool adds a metered fee above the shared cap | Infeasible route is not dispatched; admissible partial work and a report remain possible |
| Crash after dispatch or publication, new head before status write | Idempotent local acceptance, reconciliation of uncertain external effects, no passing check for a different snapshot |
| Malicious input or cross-project cache access | Permissions, isolation and data boundaries hold; execution fails closed where required |
| Untrusted setup hook, child process, symlink/archive escape or credential egress attempt | No trusted setup execution, out-of-scope access or unauthorized transmission; isolate or halt the run and record the affected gap |

Use controlled worker responses to test state transitions. Test crash recovery, version races, isolation, quotas and watchdog behavior against the real runtime. Evaluate model discovery and human usefulness statistically.
