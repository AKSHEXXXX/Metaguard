# MetaGuard — Standard Operating Procedure

## Purpose

This SOP gives an AI coding agent and human developers the exact sequence of work to build MetaGuard from scratch. It enforces a deterministic-first, integration-later philosophy.

## Prime Directive

> Build the deterministic core engine first. Do not connect to OpenMetadata, MCP, GitHub APIs, or any external system until Phase 1 is complete and all fixture tests pass.

***

## Phase 1 — Core Engine (Offline, Fixture-Driven)

**Goal:** A fully working, tested analyzer that runs locally with zero external dependencies.

### Step 1.1 — Project scaffold
- Create project directory structure as defined in `ARCHITECTURE.md`
- Set up virtual environment
- Add `requirements.txt`: `pytest`, dataclasses, `click` for CLI
- Add `.gitignore`

**Test gate:** `pytest` discovers zero tests and exits cleanly.

***

### Step 1.2 — Domain models
- `ChangeType` enum: `ADD_COLUMN`, `DROP_COLUMN`, `RENAME_COLUMN`, `ALTER_TYPE`, `ALTER_NULLABILITY`, `UNKNOWN`
- `Severity` enum: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `Confidence` enum: `LOW`, `MEDIUM`, `HIGH`
- `AssetType` enum: `TABLE`, `VIEW`, `DASHBOARD`, `PIPELINE`, `MODEL`, `FEATURE_STORE`
- `SchemaChange`, `Asset`, `LineageEdge`, `LineageGraph`, `ImpactRecord`, `ImpactReport` dataclasses

**Test gate:** `tests/unit/test_models.py` — instantiate every model, assert field types, assert enum values. Minimum 8 assertions.

***

### Step 1.3 — Provider interface
- `MetadataProvider` Protocol in `providers/base.py`
- Two methods: `resolve_asset` and `get_downstream_lineage`

**Test gate:** `tests/unit/test_provider_interface.py` — verify a stub class satisfies the Protocol without error.

***

### Step 1.4 — Fixture loader
- `FixtureLoader` utility that loads diffs, lineage, and expected from `tests/fixtures/`
- Raises `FixtureNotFoundError` for missing files

**Test gate:** `tests/unit/test_fixture_loader.py` — all 5 fixture IDs (F1–F5) load. Missing ID raises correctly.

***

### Step 1.5 — Mock metadata provider
- `MockMetadataProvider(fixture_id: str)` reads lineage fixture and returns typed domain objects
- Raises `AssetNotFoundError` for unknown refs

**Test gate:** `tests/unit/test_mock_provider.py` — F1 lineage loads, root asset resolves, unknown ref raises.

***

### Step 1.6 — Diff parser
- `DiffParser.parse(raw_sql: str) -> list[SchemaChange]`
- Patterns to support: `DROP COLUMN`, `ADD COLUMN`, `RENAME COLUMN`, `ALTER COLUMN TYPE`

**Test gate:** `tests/unit/test_diff_parser.py` — one test per SQL pattern; verify correct `ChangeType` and `column` field.

***

### Step 1.7 — Asset resolver
- `AssetResolver.resolve(change, provider) -> Asset`
- Degrades to `confidence=LOW` if unresolved

**Test gate:** `tests/unit/test_asset_resolver.py` — known resolves correctly; unknown returns LOW confidence.

***

### Step 1.8 — Lineage traverser
- `LineageTraverser.traverse(root_id, graph, depth) -> list[tuple[Asset, list[str]]]`
- Returns list of (asset, path) tuples via BFS; avoids cycles

**Test gate:** `tests/unit/test_traverser.py` — F1 graph returns 4 downstream assets with correct paths.

***

### Step 1.9 — Impact rules engine
- `ImpactRulesEngine.evaluate(change, asset, path, column_map) -> ImpactRecord`
- Rule functions: `rule_drop_column`, `rule_rename_column`, `rule_alter_type`, `rule_alter_nullability`, `rule_add_column`

**Test gate:** `tests/unit/test_rules.py` — one test per rule per major condition branch from `RULES.md`. Minimum 12 tests.

***

### Step 1.10 — Report builder
- `ReportBuilder.build(changes, records) -> ImpactReport`
- Computes `highest_severity`, `total_affected`, `generated_at`

**Test gate:** `tests/unit/test_reporter.py` — report with 3 records of CRITICAL/HIGH/LOW returns CRITICAL as highest, count=3.

***

### Step 1.11 — PR markdown renderer
- `PRCommentRenderer.render(report: ImpactReport) -> str`
- Must include: severity badge, affected asset table, path per asset, recommended actions

**Test gate:** `tests/unit/test_renderer.py` — rendered markdown from F1 report contains asset names and severity `CRITICAL`.

***

### Step 1.12 — End-to-end integration tests
- Wire all Phase 1 components
- Run against F1–F5 fixtures

**Test gate:** `tests/integration/test_e2e_fixtures.py` — all 5 pass. This is the Phase 1 completion gate.

***

## Phase 2 — OpenMetadata Integration (Requires VM)

**Goal:** Replace mock provider with real OpenMetadata without changing engine.

### Step 2.1 — OpenMetadataProvider
- `OpenMetadataProvider(host, jwt_token)` implements `MetadataProvider` Protocol
- Calls OpenMetadata lineage and asset REST APIs

**Test gate:** `tests/unit/test_openmetadata_provider.py` — mock HTTP responses, verify correct model construction.

### Step 2.2 — MCP client
- `MCPClient(mcp_url, jwt_token)` with `query_lineage(asset_id, depth) -> LineageGraph`

**Test gate:** Unit test with mocked SSE response.

### Step 2.3 — JWT auth utility
- `JWTAuthProvider` reads `OM_JWT_TOKEN` from env

**Test gate:** Missing env var raises `AuthConfigError`.

### Step 2.4 — Live smoke test (requires Oracle VM)
- Run full pipeline against one known asset on OpenMetadata
- Assert non-empty lineage response

***

## Phase 3 — GitHub Action Integration

### Step 3.1 — GitHub Action YAML
- `.github/workflows/metaguard.yml`
- Trigger: `pull_request` on `opened`, `synchronize`, `reopened`
- Path filter: schema files only

### Step 3.2 — GitHub adapter
- `GitHubAdapter.post_pr_comment(pr_number, body)` creates or updates one bot comment per PR

**Test gate:** Mock HTTP test for create and update behavior.

### Step 3.3 — CLI wiring
- `main.py` with flags: `--mock`, `--om-host`, `--om-token`, `--pr-number`, `--changed-files`

**Test gate:** CLI with `--mock --changed-files F1` prints markdown to stdout.

***

## Phase 4 — LLM Summarizer

### Step 4.1 — Summarizer wrapper
- Accepts full `ImpactReport` JSON
- Returns improved prose section only
- Validates output does not introduce new asset names, counts, or severity changes

### Step 4.2 — Fallback
- If LLM output fails validation, use `PRCommentRenderer` output directly

**Test gate:** Unit test that bad LLM output (e.g., hallucinated asset name) triggers fallback.

***

## Invariants (Must Hold at Every Phase)

1. Core engine is always deterministic
2. LLM never decides impact facts
3. Mock and real providers are interchangeable via interface
4. All Phase 1 tests pass in offline environment
5. Confidence degrades gracefully; never guesses