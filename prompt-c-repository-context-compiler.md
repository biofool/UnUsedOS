Repository Context Compiler — Prompt C (v2)
Purpose
Create or refresh a durable, evidence-based, selectively navigable repository context layer that helps AI coding agents:

Find the correct location for a change.
Understand the architecture relevant to that change.
Identify upstream and downstream impact before editing code.
Follow established repository conventions and patterns.
Select the correct validation and tests after making a change.
Avoid repeatedly rediscovering stable repository knowledge.
Recognize architectural risk, technical debt, contradictions, and unknowns without treating generated analysis as primary evidence.
The primary goal is coding-agent effectiveness, not documentation completeness.

Architecture documentation and technical-debt analysis are supporting outputs.

The desired result is a compact repository context system that a fresh coding agent can navigate progressively rather than loading the entire repository or all generated documentation into its context window.

Core Operating Rules
You are a staff-level software architect and security-minded maintainer performing a read-only repository analysis.

Do not modify:

application code
configuration
infrastructure
dependencies
tests
generated application artifacts
deployment resources
You may create or update only the repository-context artifacts explicitly defined in this prompt.

Treat repository evidence as authoritative for describing the implementation.

Do not document what you think the architecture should be. Document what the repository demonstrates currently exists.

Classify all important claims as:

OBSERVED — directly supported by repository evidence.
INFERRED — strongly suggested by multiple pieces of evidence but not directly established.
DECLARED — stated by documentation, ADRs, comments, or other descriptive material.
UNKNOWN — insufficient evidence exists.
Never convert an inference into an observed fact. Never convert a declared claim into an observed fact.

When evidence is unavailable, write UNKNOWN and identify what would be required to verify the claim.

Never invent:

runtime behavior
deployment topology
ownership
SLAs
threat models
business requirements
commands
Never claim the repository is secure, scalable, production-ready, or debt-free. State confidence and limitations explicitly instead. The strongest positive statement permitted is that no contrary evidence was found within the analyzed scope.

Evidence Precedence
When sources conflict, do not silently resolve the contradiction.

Use this default implementation-evidence hierarchy:

Executable source code and runtime configuration
Infrastructure-as-code and deployment configuration
Tests demonstrating actual expected behavior
Schemas, API specifications, and interface definitions
ADRs and explicit architecture decisions
Architecture documentation and runbooks
README files and developer documentation
Comments
Analyzer inference
This hierarchy does not mean lower-ranked evidence should be ignored.

Conflict Recording Schema
Every detected contradiction between sources must be recorded in .ai-context/decisions/conflicts.yaml using this shape:

- id: CONFLICT-001
  summary:
  declared_claim:
    statement:
    source:            # path (+ symbol where practical)
    evidence_type:     # ADR | docs | comment | README | spec
  observed_behavior:
    statement:
    source:            # path (+ symbol where practical)
    evidence_type:     # code | config | test | IaC
  resolution: UNKNOWN  # UNKNOWN | superseded | intentional
  resolution_evidence: # required if resolution is not UNKNOWN
  impact_if_agent_trusts_wrong_side:
Do not decide that either side of a conflict should be silently rewritten. resolution may only leave UNKNOWN when repository evidence (e.g., a later ADR, a commit deprecating the doc) establishes it.

Stage 0 — Scope Budget and Pass Plan
Before any deep analysis, establish an execution budget. Full eight-stage analysis in a single session is the exception, not the default.

0.1 Size the repository
Run cheap, deterministic commands to estimate:

total file count (excluding vendored/generated paths)
approximate lines of code by language
number of top-level modules / packages / deployable units
presence of an existing .ai-context/manifest.yaml (refresh mode vs. initial mode)
0.2 Declare a pass plan
Based on size, declare in writing, before proceeding:

which stages this session will execute, and at what depth
which components/domains are in scope this session
which are explicitly deferred
the intended publication order for this session (see Publication Order below)
Record the pass plan in .ai-context/manifest.yaml under pass_plan. The manifest must always be left resumable: a future session must be able to read it and continue without re-planning from scratch.

0.3 Prioritization for partial passes
When the full repository cannot be covered, prioritize in this order:

runtime-critical paths
frequently changed components (use VCS history where available)
security-sensitive areas
shared infrastructure
important domain boundaries
Never pretend coverage is complete. Prefer useful partial context with explicit coverage boundaries over shallow repository-wide summaries.

Publication Order — Minimum Viable Context
Publish artifacts incrementally as they are completed, not in a single batch at the end. An interrupted session must still leave usable context behind.

The value-ordered publication sequence is:

.ai-context/index.md and .ai-context/quickstart.md (skeleton acceptable; mark gaps UNKNOWN)
.ai-context/manifest.yaml with the pass plan
Change-impact entries for the highest-traffic / highest-risk components
Workflow maps for runtime-critical paths
Component files
Conventions
Test routing map
Debt register, conflicts, unknowns
Delta file
If a session ends early, everything published so far must be internally consistent and honestly marked for coverage. A thin, accurate index beats a rich, unpublished analysis.

Stage 1 — Repository Discovery and Routing
Objective
Build the minimal structural understanding required to navigate the repository intelligently.

Inspect
Identify:

repository root, languages, frameworks, package managers, build systems
major applications, services, workers, CLIs, scheduled jobs
infrastructure, databases, queues, object stores
public APIs, internal APIs, major external integrations
major subprojects, test frameworks, CI/CD systems
Read existing repository guidance first, when present:

AGENTS.md, CLAUDE.md, README*
contribution guides, architecture documentation, ADRs
CI/CD definitions, infrastructure-as-code
schemas, API specifications, runbooks
package manifests, build configuration
Exclude from broad inspection unless architecturally relevant:

vendored dependencies, dependency caches, build output
generated files, binaries, secrets, large static assets
Output
Create /.ai-context/index.md — the primary context router.

Hard requirements for index.md:

Soft ceiling: 150 lines. If it grows past this, split content downward into domain indexes rather than exceeding it.
Must embed, near the top: the repository revision at which this context was last verified, and one instruction to consumers: "Compare this revision to current HEAD. Context covering paths changed since this revision is suspect — verify against source before relying on it."
Must route to: major domains, major deployable units, architecture context, component context, workflow context, coding conventions, testing guidance, known debt and risks, conflicts, and the navigation hierarchy itself.
Must not contain detailed architecture documentation. Its job is routing.
Stage 2 — Architecture Compilation
Objective
Compile the repository into a navigable technical model.

Analyze the system at these levels.

A. System Context
Users, external systems, third-party services, trust boundaries, major business capabilities, data entering and leaving the system.

B. Deployable Units
Frontends, APIs, backend services, workers, CLIs, scheduled jobs, databases, queues, object stores, infrastructure components.

C. Components
For important modules/packages/components: responsibility, primary files, public interfaces, important dependencies, consumers, state/data ownership, architectural boundaries.

D. Runtime and Code Paths
Map representative execution paths, including where applicable: HTTP requests, authentication, authorization, registration, persistence, event processing, queues, background workers, scheduled jobs, CLI commands, external API calls, retries, failures, timeouts, recovery, transactions, idempotency, logging, metrics.

E. Change Impact
For important components: what they depend on, what depends on them, files commonly changed together, schemas/interfaces consumed and exposed, configuration relied on, tests that validate them, runtime paths they participate in, security-sensitive behavior, operationally sensitive behavior.

Level E is mandatory. Architecture analysis is incomplete if it describes what a component does but does not help a coding agent understand what may be affected when the component changes.

Diagram Rule
Generate Mermaid diagrams only when they remain readable. When a diagram would exceed roughly a dozen nodes or require dense crossing edges, provide a structured table instead. Every diagram must agree with the corresponding structured inventory; the inventory is authoritative.

Stage 3 — Coding Pattern and Convention Extraction
Objective
Determine how this repository expects new code and modifications to be structured. Do not merely repeat style-guide text; infer patterns from actual repository structure and repeated implementation behavior.

Identify, where evidence exists:

Feature placement
Where new API routes, business/domain logic, persistence logic, shared utilities, schemas/types, external integrations, and configuration normally live.

Dependency rules
Which layers may depend on which, prohibited dependency directions, module boundaries, service boundaries, direct database access rules, shared-library rules.

Error handling
Error classes/patterns, propagation conventions, HTTP/error mapping, retryable vs non-retryable errors, logging expectations.

Validation
Input-validation libraries, validation location, schema conventions, boundary validation.

Configuration
Configuration-loading patterns, environment variable handling, configuration modules, environment-specific behavior.

Logging and observability
Logging APIs, structured fields, tracing conventions, metric conventions, prohibited logging patterns.

Testing conventions
Unit-test placement, integration-test placement, E2E tests, mocks/fixtures, naming conventions, test setup.

Naming and structure
Recurring file naming, folder organization, class/function patterns, interface patterns, module export patterns.

For every convention, label its strength:

documented convention
strongly recurring observed pattern (state the approximate count of occurrences)
weak pattern (state the count)
unknown
Do not present one example as a repository-wide convention.

Stage 4 — Runtime Workflow Mapping
Objective
Give coding agents reusable feature-level execution maps.

Create workflow files for important end-to-end paths (login, account creation, checkout, payment, job creation, queue processing, notification delivery, file upload, report generation, background processing — as applicable). Only create workflows supported by repository evidence.

Each workflow file contains:

Entry Point
Where execution begins.

Execution Path
Ordered sequence of important components, for example:

POST /api/orders
    ↓
request validation
    ↓
authentication middleware
    ↓
OrderService
    ↓
OrderRepository
    ↓
database
    ↓
event publisher
    ↓
queue
    ↓
OrderWorker
Evidence
Associate stages with relevant paths, functions/classes where practical, configuration, and tests.

Failure Paths
Where relevant: validation failure, authorization failure, dependency failure, retry behavior, timeout behavior, partial failure, rollback/recovery.

Change Guidance
Which parts should be reviewed together before modifying this workflow.

Stage 5 — Dependency and Change-Impact Mapping
Objective
Create machine-readable guidance answering:

If an agent modifies X, what else should it inspect?

For important components, capture in .ai-context/change-impact/relationships.yaml:

component:
  name:
  path:

depends_on: []

used_by: []

interfaces: []

data_stores: []

configuration: []

runtime_workflows: []

decisions: []

known_risks: []

security_sensitive: false

operationally_sensitive: false

before_modifying: []

test_map_target:      # pointer into testing/test-map.yaml; commands live there, not here

evidence: []
Validation commands and test lists live only in testing/test-map.yaml (Stage 6). This file points to them via test_map_target; it does not duplicate them.

Do not imply that static import relationships alone represent complete architectural dependency. Distinguish:

code dependency
runtime dependency
data dependency
configuration dependency
interface dependency
operational dependency
Stage 6 — Test and Validation Routing
Objective
Allow a coding agent to answer:

I changed this component or workflow. What should I run to validate the change?

Map repository areas to available validation in .ai-context/testing/test-map.yaml. This file is the single source of truth for validation commands; no other context file may restate them.

Identify: unit tests, integration tests, E2E tests, contract tests, architecture tests, security tests, static analysis, linters, type checking, build validation, infrastructure validation.

Example entry:

target: auth/session

unit:
  - npm test -- auth/session

integration:
  - npm run test:integration -- auth

typecheck:
  - npm run typecheck

lint:
  - npm run lint

additional:
  - verify token expiration integration path
Never invent commands. Every listed command must exist in package manifests, CI definitions, Makefiles, or equivalent repository evidence. If validation mapping is unknown, mark it UNKNOWN.

Stage 7 — Quality and Technical-Debt Analysis
Objective
Capture risks that future coding agents should know, without allowing technical-debt analysis to dominate the repository context. Technical debt is a supporting context domain, not the primary purpose of this analysis.

Assess evidence across: correctness, domain invariants, maintainability, cohesion, coupling, duplication, dependency direction, reliability, retries, timeouts, circuit breaking, backpressure, idempotency, recovery, security, authentication, authorization, secret handling, input validation, injection exposure, sensitive-data handling, least privilege, performance, concurrency, caching, database access, rate limits, observability, health checks, rollback, configuration management, testability, delivery, data lifecycle, migrations, backup/restore.

Do not treat the absence of a tool, comment, or test as proof of a defect. Where absence prevents verification, record an evidence gap.

Separate findings into: confirmed defect, architectural risk, code smell, improvement opportunity, evidence gap.

Technical Debt Register
Maintain .ai-context/debt/register.yaml. For confirmed or strongly supported debt, retain stable IDs across refreshes.

Register item schema:

- id:                      # stable across refreshes
  title:
  category:                # code | architectural | test | documentation |
                           # dependency | migration | operational |
                           # security | organizational
  status:                  # open | in_progress | resolved | stale
  affected_paths: []
  evidence: []             # path (+ symbol); command output summary; test ref
  cause:                   # trigger or likely cause if evidenced; else UNKNOWN
  risk:                    # current behavior and the risk it creates,
                           # including blast radius, in prose
  priority:
    impact: 0              # 1–5
    likelihood: 0          # 1–5
    reach: 0               # 1–5
    score: 0               # impact × likelihood × reach
    rationale:
  smallest_safe_fix:
  remediation_notes:       # strategic option, preconditions, rollback,
                           # validation plan — brief
  estimated_effort:        # XS | S | M | L | XL (note uncertainty)
  agent_suitability:       # whether an AI coding agent can safely address it
  human_review_required:
The priority score orders the register; sort descending by score. Do not imply mathematical precision — the score is a ranking heuristic, and the rationale carries the actual argument.

Do not recommend large rewrites unless repository evidence shows incremental remediation would be unsafe or economically unreasonable.

Stage 8 — Context Publication
Create or refresh the following structure unless repository conventions clearly justify another location:

.ai-context/
├── index.md                     # ≤150 lines
├── quickstart.md                # ≤100 lines
├── manifest.yaml
│
├── architecture/
│   ├── index.md
│   ├── system-overview.md
│   ├── frontend.md
│   ├── backend.md
│   ├── infrastructure.md
│   └── data.md
│
├── components/
│   ├── index.md
│   └── <component>.md           # ≤300 lines each
│
├── workflows/
│   ├── index.md
│   └── <workflow>.md            # ≤300 lines each
│
├── change-impact/
│   ├── index.md
│   └── relationships.yaml
│
├── conventions/
│   ├── index.md
│   ├── coding-patterns.md
│   ├── dependencies.md
│   ├── errors.md
│   ├── persistence.md
│   ├── configuration.md
│   └── observability.md
│
├── testing/
│   ├── index.md
│   └── test-map.yaml
│
├── decisions/
│   ├── architecture-decisions.md
│   └── conflicts.yaml
│
├── debt/
│   └── register.yaml
│
├── unknowns/
│   └── register.yaml
│
└── deltas/
    └── latest.yaml
Do not create empty files solely to satisfy this structure. Only create domain files when useful evidence exists.

Size Ceilings
index.md: 150 lines
quickstart.md: 100 lines
any single component, workflow, or convention file: 300 lines
These are soft ceilings: exceeding one is a signal to split the file and add routing, never to keep appending. No individual context file may become a dumping ground for unrelated repository knowledge. Prefer multiple focused files over one enormous document.

Progressive Disclosure Requirements
The context hierarchy must be usable without loading everything.

A fresh coding agent should normally follow:

AGENTS.md / CLAUDE.md
        ↓
.ai-context/index.md
        ↓
staleness check (index revision vs. current HEAD)
        ↓
identify relevant domain
        ↓
relevant component or workflow
        ↓
change-impact map
        ↓
coding conventions
        ↓
relevant tests (test-map.yaml)
        ↓
source code
Index files function as routers: they summarize what exists and point to deeper context. They must not duplicate the detailed content contained below them.

Coding-Agent Quickstart
Create .ai-context/quickstart.md (≤100 lines).

Contain only the minimum high-value information a fresh coding agent needs before editing the repository:

system shape
major entry points
major architectural boundaries
important dependency rules
repository coding patterns
essential test/build commands (by reference to test-map.yaml where possible)
highest-risk areas
how to navigate .ai-context/, including the staleness check
Do not turn this into a full repository summary.

Source vs Derived Knowledge
Everything under .ai-context/ is derived repository context unless explicitly identified otherwise.

Generated context must never become primary evidence merely because another agent generated it. When possible, important claims retain evidence references to original repository sources.

Future coding agents should use .ai-context/ for routing, orientation, impact analysis, convention discovery, and test selection. For high-impact architectural or security-sensitive changes, agents must verify relevant claims against current source code and configuration before modifying behavior.

Consumer Staleness Protocol
Both index.md and quickstart.md must instruct consuming agents to:

Read last_verified_revision from the index (or manifest).
Compare it to current HEAD.
Treat any context artifact whose source_paths (per the manifest) intersect files changed since that revision as suspect — usable for routing, not for load-bearing claims — until verified against source.
Provenance
Use lightweight provenance. For important generated claims, capture where practical:

repository_revision:
path:
symbol:            # function/class/module name — preferred anchor
lines:             # ONLY for configuration values or where no symbol exists
evidence_type:
confidence:
last_verified:
Standard anchor is path + symbol, not line numbers. Line references rot on the first subsequent commit; symbol references survive most edits. Use line numbers only where no stable symbol exists (configuration values, data files). Do not create enterprise-scale provenance infrastructure.

Incremental Refresh and Diff-Driven Invalidation
If .ai-context/manifest.yaml already exists, do not automatically reanalyze the entire repository.

First determine:

previously analyzed repository revision
current revision
files changed since the previous analysis
components, workflows, dependency relationships, conventions, tests, and context files potentially affected
Then reanalyze only the affected areas unless:

foundational architecture changed
package/module structure changed substantially
dependency configuration changed broadly
the previous analysis is incomplete
evidence indicates broader invalidation
Do not assume that a changed file only affects the context file with the same name. Use dependency and workflow relationships from relationships.yaml to propagate invalidation.

Context Delta
After every refresh, create .ai-context/deltas/latest.yaml:

from_revision:
to_revision:

added: []
changed: []
invalidated: []
conflicts: []
reverified: []
unknowns_added: []
unknowns_resolved: []
Do not silently remove old knowledge. If something becomes unsupported, mark it invalidated or stale.

Manifest
Maintain .ai-context/manifest.yaml:

repository_revision:
analysis_timestamp:
analyzer_version:

pass_plan:                 # from Stage 0
  session_scope:
  stages_executed:
  stages_deferred:
  components_in_scope:
  components_deferred:

coverage:                  # honest statement of what was and was not analyzed
analyzed_domains: []
excluded_paths: []

commands_run: []
commands_not_run: []
limitations: []

artifacts:                 # per major artifact
  - path:
    source_paths: []
    last_verified_revision:

unresolved_unknowns: []
prior_analyzed_revision:
The manifest must always be resumable: a future session reads pass_plan and coverage and continues where this one stopped.

Quality Gates
Before completion, verify the following checklist. Each gate references the stage that defines the requirement; gates do not restate stage content.

Coverage and honesty

[ ] Every major deployable unit discovered in Stage 1 is represented or marked UNKNOWN.
[ ] Coverage boundaries and deferred scope are recorded in the manifest exactly as executed (Stage 0).
[ ] No claim asserts the repository is secure, scalable, production-ready, or debt-free (Core Operating Rules).
Evidence integrity

[ ] Important claims carry repository evidence per the Provenance rules; observed facts are distinguished from inference and declaration.
[ ] All detected contradictions are recorded in conflicts.yaml per the Conflict Recording Schema, with neither side silently rewritten.
[ ] Generated context is not cited as original evidence anywhere.
Coding-agent usability

[ ] For each in-scope major component, a future agent can determine: location, responsibility, dependencies, dependents, applicable conventions, relevant tests, and pre-change risks (Stages 2E, 3, 5, 6).
[ ] index.md routes correctly; index files do not duplicate lower-level content; a normal task does not require reading the entire context directory.
[ ] Size ceilings hold, or oversized files were split (Stage 8).
[ ] Publication followed the Minimum Viable Context order; partial output is internally consistent.
[ ] The staleness protocol appears in index.md and quickstart.md.
Artifact validation

[ ] All YAML parses. Internal links and references resolve. Diagrams agree with structured inventories (inventories authoritative, Stage 2).
[ ] Every command listed in test-map.yaml exists in repository evidence (Stage 6).
[ ] Validation commands appear only in test-map.yaml; relationships.yaml points via test_map_target (Stages 5–6).
[ ] No secrets appear in any artifact.
Repository validation

[ ] Safe repository-native checks were run where relevant (tests, linters, type checks, build checks, architecture checks); commands and results recorded in the manifest.
[ ] No command contacted production, mutated external systems, modified dependencies, exposed secret values, or was destructive.
Completion Criteria
The analysis is successful when a fresh AI coding agent can use .ai-context/ to answer the following substantially faster than by repository rediscovery alone:

Where should I work? Which files/components/domains are relevant to the requested change?
What do I need to understand? Which architecture, workflows, dependencies, conventions, and decisions apply?
What else could this affect? Which consumers, dependencies, interfaces, data stores, workflows, configuration, and tests are connected?
How should I implement it? Which existing repository patterns and conventions should the change follow?
How do I validate it? Which tests, static checks, integration checks, or build commands are appropriate?
Do not optimize for documentation volume. Optimize for minimum rediscovery with high-confidence navigation.

Required Final Response
Return, in this order:

Coding-Agent Readiness
Lead with whether the generated context adequately supports: navigation, architecture understanding, change-impact analysis, convention following, test selection.

Rate each: Strong / Partial / Weak, with one line of justification per rating.

Executive Summary
5–10 lines: repository architecture discovered, context coverage achieved this session, major context gaps, overall confidence.

Pass Plan Outcome
What the Stage 0 plan committed to, what was completed, what was deferred, and where the manifest points the next session.

Context Layer Created or Updated
List the .ai-context/ artifacts created or modified, in publication order.

Highest-Value Unknowns
The most important unresolved questions that could cause a coding agent to make an incorrect change, and the cheapest verification for each.

Commands Run
Safe inspection and validation commands and their results.

Context Delta
What knowledge was added, changed, invalidated, contradicted, reverified.

Recommended Next Actions
The next one to three context-improvement actions only. Do not turn the final response into a generalized technical-debt report.

Final Principle
The generated repository context is not intended to replace source-code inspection. It is intended to make source-code inspection targeted.

A successful context layer lets an AI coding agent enter a fresh session, check staleness, identify the correct part of the system, understand its surrounding architecture, predict the impact of a modification, follow existing implementation patterns, and run appropriate validation — without repeatedly reconstructing the repository from scratch.
