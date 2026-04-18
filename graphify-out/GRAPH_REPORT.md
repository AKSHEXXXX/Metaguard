# Graph Report - .  (2026-04-17)

## Corpus Check
- Corpus is ~14,566 words - fits in a single context window. You may not need a graph.

## Summary
- 246 nodes · 569 edges · 27 communities detected
- Extraction: 52% EXTRACTED · 48% INFERRED · 0% AMBIGUOUS · INFERRED: 271 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Core Data Models & Base Interfaces|Core Data Models & Base Interfaces]]
- [[_COMMUNITY_OpenMetadata Integration|OpenMetadata Integration]]
- [[_COMMUNITY_GitHub Actions Integration|GitHub Actions Integration]]
- [[_COMMUNITY_CLI Entrypoint & Reporting|CLI Entrypoint & Reporting]]
- [[_COMMUNITY_Lineage & Asset Resolution|Lineage & Asset Resolution]]
- [[_COMMUNITY_Validation Rules & Tests|Validation Rules & Tests]]
- [[_COMMUNITY_Fixture Management|Fixture Management]]
- [[_COMMUNITY_Impact Evaluation Rules|Impact Evaluation Rules]]
- [[_COMMUNITY_AI-Assisted Summarization|AI-Assisted Summarization]]
- [[_COMMUNITY_SQL Diff Parsing|SQL Diff Parsing]]
- [[_COMMUNITY_Project Phase 1 Overview|Project Phase 1 Overview]]
- [[_COMMUNITY_Markdown Rendering|Markdown Rendering]]
- [[_COMMUNITY_Provider Interface Validation|Provider Interface Validation]]
- [[_COMMUNITY_Smoke Tests|Smoke Tests]]
- [[_COMMUNITY_Project Phase 2 Strategy|Project Phase 2 Strategy]]
- [[_COMMUNITY_Unit Test Scaffolding|Unit Test Scaffolding]]
- [[_COMMUNITY_Unit Test Setup (Common)|Unit Test Setup (Common)]]
- [[_COMMUNITY_Integration Test Setup (Common)|Integration Test Setup (Common)]]
- [[_COMMUNITY_Provider Setup (Common)|Provider Setup (Common)]]
- [[_COMMUNITY_Parser Setup (Common)|Parser Setup (Common)]]
- [[_COMMUNITY_Normalization Logic|Normalization Logic]]
- [[_COMMUNITY_Adapter Setup (Common)|Adapter Setup (Common)]]
- [[_COMMUNITY_Engine Setup (Common)|Engine Setup (Common)]]
- [[_COMMUNITY_Impact Scoring|Impact Scoring]]
- [[_COMMUNITY_Domain Setup (Common)|Domain Setup (Common)]]
- [[_COMMUNITY_Project Phase 3 Strategy|Project Phase 3 Strategy]]
- [[_COMMUNITY_Project Phase 4 Strategy|Project Phase 4 Strategy]]

## God Nodes (most connected - your core abstractions)
1. `SchemaChange` - 33 edges
2. `evaluate()` - 27 edges
3. `Asset` - 27 edges
4. `LineageGraph` - 24 edges
5. `AssetType` - 21 edges
6. `OpenMetadataProvider` - 19 edges
7. `_asset()` - 18 edges
8. `LineageEdge` - 18 edges
9. `Returns (fixture_id, file_paths).      - If `changed_files` is a fixture ID like` - 17 edges
10. `MockMetadataProvider` - 17 edges

## Surprising Connections (you probably didn't know these)
- `_schema_change_from_dict()` --calls--> `SchemaChange`  [INFERRED]
  main.py → src/domain/models.py
- `_schema_change_from_dict()` --calls--> `ChangeType`  [INFERRED]
  main.py → src/domain/enums.py
- `_collect_fixture_records()` --calls--> `default()`  [INFERRED]
  main.py → src/parser/fixture_loader.py
- `_collect_fixture_records()` --calls--> `MockMetadataProvider`  [INFERRED]
  main.py → src/providers/mock_provider.py
- `_collect_fixture_records()` --calls--> `resolve()`  [INFERRED]
  main.py → src/providers/resolver.py

## Hyperedges (group relationships)
- **Core Engine Components** — metaguard_diffparser, metaguard_lineagetraverser, metaguard_impactrulesengine [EXTRACTED 1.00]

## Communities

### Community 0 - "Core Data Models & Base Interfaces"
Cohesion: 0.14
Nodes (32): MetadataProvider, Resolve an asset reference (id or name) to an Asset., Return downstream lineage graph rooted at the given asset id., Enum, AssetType, ChangeType, Confidence, Severity (+24 more)

### Community 1 - "OpenMetadata Integration"
Cohesion: 0.12
Nodes (17): smoke_openmetadata(), _asset_name(), _asset_type_from_om_entity(), _extract_column_map(), _extract_criticality(), _extract_domain(), _extract_owner(), _normalize_host() (+9 more)

### Community 2 - "GitHub Actions Integration"
Cohesion: 0.14
Nodes (10): from_env(), GitHubAdapter, _GitHubComment, Minimal GitHub REST adapter (stdlib only).      Implements an idempotent PR comm, Create or update a single MetaGuard bot comment on a PR.          Identification, _default_stream_provider(), RuntimeError, _FakeHTTPResponse (+2 more)

### Community 3 - "CLI Entrypoint & Reporting"
Cohesion: 0.14
Nodes (19): AuthConfigError, JWTAuthProvider, Raised when required auth configuration is missing or invalid., _asset_type_rank(), _collect_fixture_records(), _confidence_rank(), main(), _parse_changed_files() (+11 more)

### Community 4 - "Lineage & Asset Resolution"
Cohesion: 0.12
Nodes (11): AssetNotFoundError, LookupError, MetadataProvider, MockMetadataProvider, resolve(), test_known_asset_resolves_with_high_confidence(), test_unknown_asset_returns_low_confidence(), test_cli_mock_changed_files_fixture_prints_markdown() (+3 more)

### Community 5 - "Validation Rules & Tests"
Cohesion: 0.34
Nodes (19): SchemaChange, evaluate(), _asset(), test_add_column_default_is_low_high(), test_add_column_strict_schema_consumer_is_medium_low(), test_alter_nullability_not_null_to_null_is_low_high(), test_alter_nullability_null_to_not_null_is_high_high(), test_alter_nullability_table_level_only_is_medium_medium() (+11 more)

### Community 6 - "Fixture Management"
Cohesion: 0.19
Nodes (9): FileNotFoundError, default(), FixtureLoader, FixtureNotFoundError, FixtureValidationError, test_e2e_all_fixtures_match_expected(), test_fixture_loader_invalid_schema_raises(), test_fixture_loader_loads_all_fixture_sets() (+1 more)

### Community 7 - "Impact Evaluation Rules"
Cohesion: 0.29
Nodes (14): _column_map_has_alias(), _column_map_references(), _compute_path(), _format_reason(), _normalize_type(), rule_add_column(), rule_alter_nullability(), rule_alter_type() (+6 more)

### Community 8 - "AI-Assisted Summarization"
Cohesion: 0.33
Nodes (5): LLMSummarizer, Phase 4 summarizer wrapper.      Contract:     - Accepts full ImpactReport JSON, SummaryValidationError, test_summarizer_appends_llm_summary_when_valid(), test_summarizer_falls_back_when_hallucinated_asset_is_mentioned()

### Community 9 - "SQL Diff Parsing"
Cohesion: 0.33
Nodes (7): DiffParser, parse(), _strip_quotes(), test_parse_add_column(), test_parse_alter_column_type(), test_parse_drop_column(), test_parse_rename_column()

### Community 10 - "Project Phase 1 Overview"
Cohesion: 0.4
Nodes (5): Diff Parser, Test Fixtures (F1-F5), Impact Rules Engine, Lineage Traverser, Phase 1: Core Engine

### Community 11 - "Markdown Rendering"
Cohesion: 0.83
Nodes (3): _recommended_actions(), render(), _severity_badge()

### Community 12 - "Provider Interface Validation"
Cohesion: 1.0
Nodes (0): 

### Community 13 - "Smoke Tests"
Cohesion: 1.0
Nodes (0): 

### Community 14 - "Project Phase 2 Strategy"
Cohesion: 1.0
Nodes (2): MetadataProvider Protocol, Phase 2: OpenMetadata Integration

### Community 15 - "Unit Test Scaffolding"
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Unit Test Setup (Common)"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Integration Test Setup (Common)"
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Provider Setup (Common)"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Parser Setup (Common)"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Normalization Logic"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Adapter Setup (Common)"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Engine Setup (Common)"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Impact Scoring"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Domain Setup (Common)"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Project Phase 3 Strategy"
Cohesion: 1.0
Nodes (1): Phase 3: GitHub Integration

### Community 26 - "Project Phase 4 Strategy"
Cohesion: 1.0
Nodes (1): Phase 4: LLM Summarizer

## Knowledge Gaps
- **12 isolated node(s):** `Raised when required auth configuration is missing or invalid.`, `Minimal GitHub REST adapter (stdlib only).      Implements an idempotent PR comm`, `Create or update a single MetaGuard bot comment on a PR.          Identification`, `Phase 4 summarizer wrapper.      Contract:     - Accepts full ImpactReport JSON`, `Phase 2: OpenMetadata Integration` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Provider Interface Validation`** (2 nodes): `test_stub_satisfies_metadata_provider_protocol()`, `test_provider_interface.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Smoke Tests`** (2 nodes): `test_pytest_runs()`, `test_smoke.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Project Phase 2 Strategy`** (2 nodes): `MetadataProvider Protocol`, `Phase 2: OpenMetadata Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Unit Test Scaffolding`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Unit Test Setup (Common)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Integration Test Setup (Common)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Provider Setup (Common)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Parser Setup (Common)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Normalization Logic`** (1 nodes): `normalizer.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Adapter Setup (Common)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Engine Setup (Common)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Impact Scoring`** (1 nodes): `scorer.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Domain Setup (Common)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Project Phase 3 Strategy`** (1 nodes): `Phase 3: GitHub Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Project Phase 4 Strategy`** (1 nodes): `Phase 4: LLM Summarizer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Returns (fixture_id, file_paths).      - If `changed_files` is a fixture ID like` connect `Core Data Models & Base Interfaces` to `OpenMetadata Integration`, `GitHub Actions Integration`, `CLI Entrypoint & Reporting`, `Lineage & Asset Resolution`, `Validation Rules & Tests`, `Fixture Management`?**
  _High betweenness centrality (0.281) - this node is a cross-community bridge._
- **Why does `SchemaChange` connect `Validation Rules & Tests` to `Core Data Models & Base Interfaces`, `CLI Entrypoint & Reporting`, `Lineage & Asset Resolution`, `Impact Evaluation Rules`, `SQL Diff Parsing`?**
  _High betweenness centrality (0.154) - this node is a cross-community bridge._
- **Why does `GitHubAdapter` connect `GitHub Actions Integration` to `Core Data Models & Base Interfaces`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `SchemaChange` (e.g. with `Returns (fixture_id, file_paths).      - If `changed_files` is a fixture ID like` and `AssetResolver`) actually correct?**
  _`SchemaChange` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `evaluate()` (e.g. with `_collect_fixture_records()` and `test_drop_column_with_column_lineage_is_critical_high()`) actually correct?**
  _`evaluate()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `Asset` (e.g. with `MockMetadataProvider` and `AssetResolver`) actually correct?**
  _`Asset` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `LineageGraph` (e.g. with `MockMetadataProvider` and `MetadataProvider`) actually correct?**
  _`LineageGraph` has 23 INFERRED edges - model-reasoned connections that need verification._