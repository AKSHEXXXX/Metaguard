# Graph Report - /Users/akshatsaxena/Desktop/metaguard  (2026-04-19)

## Corpus Check
- 58 files · ~30,561 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 335 nodes · 941 edges · 28 communities detected
- Extraction: 45% EXTRACTED · 55% INFERRED · 0% AMBIGUOUS · INFERRED: 516 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]

## God Nodes (most connected - your core abstractions)
1. `SchemaChange` - 51 edges
2. `Asset` - 43 edges
3. `AssetType` - 38 edges
4. `evaluate()` - 34 edges
5. `LineageGraph` - 34 edges
6. `LineageEdge` - 27 edges
7. `ChangeType` - 26 edges
8. `OpenMetadataProvider` - 25 edges
9. `Severity` - 24 edges
10. `ImpactRecord` - 24 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `SchemaChange`  [INFERRED]
  /Users/akshatsaxena/Desktop/metaguard/smoke_test.py → src/domain/models.py
- `main()` --calls--> `build()`  [INFERRED]
  /Users/akshatsaxena/Desktop/metaguard/smoke_test.py → src/engine/reporter.py
- `main()` --calls--> `LineageGraph`  [INFERRED]
  /Users/akshatsaxena/Desktop/metaguard/smoke_test_mcp.py → src/domain/models.py
- `main()` --calls--> `SchemaChange`  [INFERRED]
  /Users/akshatsaxena/Desktop/metaguard/smoke_test_mcp.py → src/domain/models.py
- `main()` --calls--> `build()`  [INFERRED]
  /Users/akshatsaxena/Desktop/metaguard/smoke_test_mcp.py → src/engine/reporter.py

## Hyperedges (group relationships)
- **Core Engine Components** — metaguard_diffparser, metaguard_lineagetraverser, metaguard_impactrulesengine [EXTRACTED 1.00]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (36): AssetNotFoundError, MetadataProvider, Resolve an asset reference (id or name) to an Asset., Return downstream lineage graph rooted at the given asset id., AssetType, LookupError, iter_sse_events(), _lineage_graph_from_payload() (+28 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (26): _default_stream_provider(), _asset_name(), _asset_type_from_om_entity(), _extract_column_map(), _extract_criticality(), _extract_domain(), _extract_owner(), _normalize_host() (+18 more)

### Community 2 - "Community 2"
Cohesion: 0.16
Nodes (38): SchemaChange, _adjust_for_depth(), _column_map_has_alias(), _column_map_references(), _compute_path(), evaluate(), _format_reason(), _lower_severity() (+30 more)

### Community 3 - "Community 3"
Cohesion: 0.2
Nodes (32): Enum, ChangeType, Confidence, Severity, Returns (fixture_id, file_paths).      - If `changed_files` is a fixture ID like, Returns (fixture_id, file_paths).      - If `changed_files` is a fixture ID like, ImpactRecord, ImpactReport (+24 more)

### Community 4 - "Community 4"
Cohesion: 0.16
Nodes (20): _asset_type_rank(), _collect_fixture_records(), _confidence_rank(), _effective_sandbox_depth(), main(), _parse_changed_files(), _record_to_dict(), render_fixture_markdown() (+12 more)

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (10): from_env(), GitHubAdapter, _GitHubComment, Minimal GitHub REST adapter (stdlib only).      Implements an idempotent PR comm, Create or update a single MetaGuard bot comment on a PR.          Identification, RuntimeError, _FakeHTTPResponse, test_get_changed_files() (+2 more)

### Community 6 - "Community 6"
Cohesion: 0.19
Nodes (9): FileNotFoundError, default(), FixtureLoader, FixtureNotFoundError, FixtureValidationError, test_e2e_all_fixtures_match_expected(), test_fixture_loader_invalid_schema_raises(), test_fixture_loader_loads_all_fixture_sets() (+1 more)

### Community 7 - "Community 7"
Cohesion: 0.18
Nodes (15): AppConfig, load_config(), _read_required(), _get_json(), main(), _read_required(), _search_tables_for_service(), main() (+7 more)

### Community 8 - "Community 8"
Cohesion: 0.22
Nodes (7): LLMSummarizer, Phase 4 summarizer wrapper.      Contract:     - Accepts full ImpactReport JSON, SummaryValidationError, test_llm_summarizer_calls_llm_with_prompt(), test_llm_summarizer_raises_without_client(), test_summarizer_appends_llm_summary_when_valid(), test_summarizer_falls_back_when_hallucinated_asset_is_mentioned()

### Community 9 - "Community 9"
Cohesion: 0.24
Nodes (9): DiffParser, parse(), _strip_quotes(), test_parse_add_column(), test_parse_alter_column_type(), test_parse_drop_column(), test_parse_rename_column(), Phase 3: Verify the diff parser correctly handles a single migration file with m (+1 more)

### Community 10 - "Community 10"
Cohesion: 0.39
Nodes (5): AuthConfigError, JWTAuthProvider, Raised when required auth configuration is missing or invalid., test_missing_env_var_raises(), test_present_env_var_returns_token()

### Community 11 - "Community 11"
Cohesion: 0.33
Nodes (4): resolve(), test_known_asset_resolves_with_high_confidence(), test_unknown_asset_returns_low_confidence(), test_cli_mock_changed_files_fixture_prints_markdown()

### Community 12 - "Community 12"
Cohesion: 1.0
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (2): Test Fixtures (F1-F5), Phase 1: Core Engine

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): Phase 2: OpenMetadata Integration

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Phase 3: GitHub Integration

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Phase 4: LLM Summarizer

## Knowledge Gaps
- **9 isolated node(s):** `Raised when required auth configuration is missing or invalid.`, `Minimal GitHub REST adapter (stdlib only).      Implements an idempotent PR comm`, `Create or update a single MetaGuard bot comment on a PR.          Identification`, `Phase 4 summarizer wrapper.      Contract:     - Accepts full ImpactReport JSON`, `Phase 1: Core Engine` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 12`** (2 nodes): `test_stub_satisfies_metadata_provider_protocol()`, `test_provider_interface.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 13`** (2 nodes): `test_pytest_runs()`, `test_smoke.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (2 nodes): `Test Fixtures (F1-F5)`, `Phase 1: Core Engine`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `normalizer.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `scorer.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `Phase 2: OpenMetadata Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Phase 3: GitHub Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `Phase 4: LLM Summarizer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `render_sandbox_markdown()` connect `Community 4` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 7`, `Community 8`, `Community 9`?**
  _High betweenness centrality (0.178) - this node is a cross-community bridge._
- **Why does `Returns (fixture_id, file_paths).      - If `changed_files` is a fixture ID like` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 4`, `Community 5`, `Community 6`, `Community 8`, `Community 9`, `Community 10`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Why does `SchemaChange` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 9`, `Community 11`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Are the 50 inferred relationships involving `SchemaChange` (e.g. with `Returns (fixture_id, file_paths).      - If `changed_files` is a fixture ID like` and `Phase 2: verify the concise title format.`) actually correct?**
  _`SchemaChange` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Are the 42 inferred relationships involving `Asset` (e.g. with `_FakeMCPClient` and `_FakeRESTProvider`) actually correct?**
  _`Asset` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `AssetType` (e.g. with `Phase 2: verify the concise title format.` and `Phase 2: verify 'Changes detected' section when changes are provided.`) actually correct?**
  _`AssetType` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `evaluate()` (e.g. with `main()` and `main()`) actually correct?**
  _`evaluate()` has 24 INFERRED edges - model-reasoned connections that need verification._