You are implementing MetaGuard — a schema change impact analyzer. A complete planning pack is in the docs/ folder. Implement exactly as specified, in the exact order specified, with no deviations.

***

## Step 0 — Read Before Coding

Before writing a single line of code, read these files in this exact order:

1. docs/PRD.md — scope, success criteria, what is out of scope
2. docs/ARCHITECTURE.md — folder structure, domain models, dependency rules between modules
3. docs/RULES.md — severity and confidence rules; implement them exactly as written, no additions
4. docs/FIXTURE_SPEC.md — 5 test fixtures with exact expected outputs
5. docs/AGENT_GUIDE.md — your operating rules and definition of done
6. docs/SOP.md — your step-by-step build order with a test gate at every step

Do not write a single line of code until all 6 files are read and understood.

***

## Operating Rules (Non-Negotiable)

1. Core engine must be deterministic — same input always produces same output, every time
2. Never invent asset names, lineage edges, severity, or confidence not present in the input graph and docs/RULES.md — if data is missing, degrade confidence, do not guess
3. MetadataProvider is a Protocol — the engine never knows if the provider is mock or real; never call OpenMetadata, MCP, or any HTTP API from inside engine/
4. Test gate before proceeding — do not move to the next SOP step until the current step's tests pass; fix the implementation, do not skip the gate
5. docs/RULES.md is the only source of truth for scoring — add no rules, infer no rules, restate no rules anywhere else
6. LLM is Phase 4 only — no LLM calls in Phases 1, 2, or 3 for any reasoning, scoring, or path computation
7. Graceful degradation — unknown entity returns LOW confidence record, empty lineage returns zero records with a warning, never raise an unhandled exception from engine/

***

## Build Order

### Phase 1 — Offline, no external systems (start now)
### Phase 2 — OpenMetadata integration (only after all Phase 1 tests pass, requires VM)
### Phase 3 — GitHub Action + PR comment (after Phase 2)
### Phase 4 — LLM summarizer (after Phase 3)

Do not touch Phase 2, 3, or 4 until Phase 1 is fully complete.

***

## Parallelization — Spawn Subagents After Step 1.2

Step 1.1 (scaffold) and Step 1.2 (domain models) are sequential and done by the main agent.
After Step 1.2 tests pass, domain models are FROZEN. Immediately spawn two subagents in parallel:

### Phase 1 — Track A (Core Engine Subagent)

Execute in order:
- Step 1.3 — Provider interface (MetadataProvider Protocol)
- Step 1.5 — Mock metadata provider
- Step 1.6 — Diff parser
- Step 1.7 — Asset resolver
- Step 1.8 — Lineage traverser (BFS)
- Step 1.9 — Impact rules engine

Each step has a test gate. Do not proceed past a step until its tests pass.
Track A is complete when Step 1.9 tests pass.

### Phase 1 — Track B (Test Infrastructure Subagent)

Execute in order:
- Step 1.4 — Fixture loader utility
- Create all 15 fixture JSON files: F1_diff.json through F5_diff.json, F1_lineage.json through F5_lineage.json, F1_expected.json through F5_expected.json as specified in docs/FIXTURE_SPEC.md
- Write unit test skeletons for every Track A module (test files with correct imports and placeholder test functions)

Track B is complete when all 15 fixture files exist and all 5 fixture IDs load without error.

### Sync Point After Tracks A and B

Main agent resumes only after BOTH Track A and Track B are complete.
Then execute sequentially:
- Step 1.10 — Report builder
- Step 1.11 — PR markdown renderer
- Step 1.12 — End-to-end integration tests (all 5 fixtures must pass)

***

## Phase 2 Parallelization

After all Phase 1 tests pass, spawn 3 subagents simultaneously:

- Subagent 1 — OpenMetadataProvider: implement REST API calls for resolve_asset and get_downstream_lineage; unit test with mocked HTTP responses
- Subagent 2 — MCP client: implement MCPClient with query_lineage method; unit test with mocked SSE response
- Subagent 3 — JWT auth utility: implement JWTAuthProvider reading OM_JWT_TOKEN from env; unit test env var handling

Sync point: all 3 subagent unit tests pass → main agent wires them together in main.py → live smoke test on VM.

***

## Phase 3 Parallelization

After Phase 2 smoke test passes, spawn 3 subagents simultaneously:

- Subagent 1 — GitHub Action YAML: .github/workflows/metaguard.yml with correct triggers and path filters
- Subagent 2 — GitHubAdapter: post_pr_comment that creates or updates a single bot comment per PR; unit test with mocked GitHub API
- Subagent 3 — CLI main.py: wiring with flags --mock, --om-host, --om-token, --pr-number, --changed-files

Sync point: all 3 unit tests pass → integration test with mock PR number and --mock flag.

***

## Coordination Rules for All Subagents

1. src/domain/models.py is frozen after Step 1.2. Any proposed change to domain models requires ALL active subagents to stop, the change to be reviewed and approved, and every subagent to re-run its tests before continuing.
2. Subagents communicate only through domain model interfaces and fixture JSON files. Never share mutable state between subagents.
3. If two subagents produce conflicting implementations of the same interface, the one that satisfies more fixture test assertions wins.
4. Each subagent runs pytest on its own module before declaring done. Never rely on another subagent's test run to validate your own code.
5. Each subagent must report: module implemented, tests written, test gate status (pass/fail), and any domain model change requests before merging its work.

***

## Folder Structure

Create this exact structure before writing any logic:

```
metaguard/
├── src/
│   ├── domain/
│   │   ├── models.py
│   │   └── enums.py
│   ├── providers/
│   │   ├── base.py
│   │   ├── mock_provider.py
│   │   └── openmetadata_provider.py
│   ├── parser/
│   │   ├── diff_parser.py
│   │   └── normalizer.py
│   ├── engine/
│   │   ├── traverser.py
│   │   ├── rules.py
│   │   ├── scorer.py
│   │   ├── reporter.py
│   │   └── renderer.py
│   └── adapters/
│       ├── github_adapter.py
│       └── mcp_client.py
├── tests/
│   ├── fixtures/
│   │   ├── diffs/
│   │   ├── lineage/
│   │   └── expected/
│   ├── unit/
│   └── integration/
├── docs/
├── main.py
└── requirements.txt
```

***

## Phase 1 Definition of Done

Do not declare Phase 1 complete until ALL of the following are true:

- [ ] pytest tests/unit/ passes with zero failures
- [ ] pytest tests/integration/test_e2e_fixtures.py passes all 5 fixture scenarios (F1-F5)
- [ ] python main.py --mock --fixture F1 prints valid markdown PR comment to stdout
- [ ] engine/ contains zero imports from providers/, adapters/, requests, httpx, or any HTTP library
- [ ] Every rule condition in docs/RULES.md has at least one unit test in tests/unit/test_rules.py
- [ ] No test file imports or calls OpenMetadata, GitHub API, or any LLM API
- [ ] All 15 fixture files exist and are valid JSON

***

## Forbidden Actions

- HTTP calls (requests/httpx/aiohttp) inside engine/ — use provider interface
- Non-deterministic functions (random/uuid/time-dependent) inside engine/
- Severity or confidence rules not documented in docs/RULES.md
- Skipping a test gate to move faster
- Importing openmetadata_provider.py before Phase 2
- Modifying domain/models.py after Step 1.2 without stopping all subagents
- Using print() for debugging — use Python logging module
- Hallucinating lineage paths not present in the fixture graph

***

## Expected Output Example

Given input:
  ALTER TABLE analytics.customers DROP COLUMN customer_id;

Expected PR comment output:

  ## 🔴 MetaGuard — CRITICAL Impact Detected

  1 schema change · 4 downstream assets affected

  | Asset | Type | Severity | Confidence | Reason |
  |-------|------|----------|------------|--------|
  | stg_customers | TABLE | CRITICAL | HIGH | Directly uses dropped column customer_id |
  | mart_customer_360 | TABLE | CRITICAL | HIGH | Uses customer_id through stg_customers |
  | Revenue by Customer | DASHBOARD | CRITICAL | HIGH | Depends on mart_customer_360.customer_id |
  | nightly_customer_rollup | PIPELINE | HIGH | MEDIUM | Table dependency; column usage unconfirmed |

  Dependency path:
  analytics.customers.customer_id → stg_customers.customer_id → mart_customer_360.customer_id → Revenue by Customer

  Recommended actions:
  - Add compatibility alias before removing the column
  - Coordinate with owners: analytics_eng, bi_team, data_eng
  - Consider staged deprecation

***

Begin now. Execute Step 1.1 from docs/SOP.md, then Step 1.2, then spawn Track A and Track B subagents simultaneously.