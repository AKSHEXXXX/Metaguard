# Graph Report - /Users/akshatsaxena/Desktop/metaguard/src  (2026-04-19)

## Corpus Check
- 27 files · ~6,542 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 166 nodes · 388 edges · 18 communities detected
- Extraction: 59% EXTRACTED · 41% INFERRED · 0% AMBIGUOUS · INFERRED: 158 edges (avg confidence: 0.57)
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

## God Nodes (most connected - your core abstractions)
1. `Asset` - 30 edges
2. `LineageGraph` - 26 edges
3. `AssetType` - 25 edges
4. `LineageEdge` - 20 edges
5. `MCPMetadataProvider` - 14 edges
6. `OpenMetadataProvider` - 14 edges
7. `RuleOutcome` - 14 edges
8. `MCPClient` - 13 edges
9. `Severity` - 13 edges
10. `MetadataProvider` - 12 edges

## Surprising Connections (you probably didn't know these)
- `MockMetadataProvider` --uses--> `AssetType`  [INFERRED]
  /Users/akshatsaxena/Desktop/metaguard/src/providers/mock_provider.py → /Users/akshatsaxena/Desktop/metaguard/src/domain/enums.py
- `MockMetadataProvider` --uses--> `Asset`  [INFERRED]
  /Users/akshatsaxena/Desktop/metaguard/src/providers/mock_provider.py → /Users/akshatsaxena/Desktop/metaguard/src/domain/models.py
- `MockMetadataProvider` --uses--> `LineageEdge`  [INFERRED]
  /Users/akshatsaxena/Desktop/metaguard/src/providers/mock_provider.py → /Users/akshatsaxena/Desktop/metaguard/src/domain/models.py
- `MockMetadataProvider` --uses--> `LineageGraph`  [INFERRED]
  /Users/akshatsaxena/Desktop/metaguard/src/providers/mock_provider.py → /Users/akshatsaxena/Desktop/metaguard/src/domain/models.py
- `_load_lineage_fixture()` --calls--> `resolve()`  [INFERRED]
  /Users/akshatsaxena/Desktop/metaguard/src/providers/mock_provider.py → /Users/akshatsaxena/Desktop/metaguard/src/providers/resolver.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.16
Nodes (22): Resolve an asset reference (id or name) to an Asset., Return downstream lineage graph rooted at the given asset id., AssetType, iter_sse_events(), _lineage_graph_from_payload(), MCPClient, MCPTransportError, Query MCP for downstream lineage rooted at `asset_id` up to `depth`.          As (+14 more)

### Community 1 - "Community 1"
Cohesion: 0.25
Nodes (15): DiffParser, parse(), _strip_quotes(), Enum, ChangeType, Confidence, Severity, ImpactRecord (+7 more)

### Community 2 - "Community 2"
Cohesion: 0.15
Nodes (7): AssetNotFoundError, MetadataProvider, LookupError, MetadataProvider, MockMetadataProvider, Protocol, AssetResolver

### Community 3 - "Community 3"
Cohesion: 0.33
Nodes (15): _column_map_has_alias(), _column_map_references(), _compute_path(), evaluate(), _format_reason(), _normalize_type(), rule_add_column(), rule_alter_nullability() (+7 more)

### Community 4 - "Community 4"
Cohesion: 0.17
Nodes (7): AuthConfigError, JWTAuthProvider, Raised when required auth configuration is missing or invalid., RuntimeError, LLMSummarizer, Phase 4 summarizer wrapper.      Contract:     - Accepts full ImpactReport JSON, SummaryValidationError

### Community 5 - "Community 5"
Cohesion: 0.23
Nodes (6): FileNotFoundError, default(), FixtureLoader, FixtureNotFoundError, FixtureValidationError, resolve()

### Community 6 - "Community 6"
Cohesion: 0.23
Nodes (5): from_env(), GitHubAdapter, _GitHubComment, Minimal GitHub REST adapter (stdlib only).      Implements an idempotent PR comm, Create or update a single MetaGuard bot comment on a PR.          Identification

### Community 7 - "Community 7"
Cohesion: 0.27
Nodes (9): _asset_name(), _asset_type_from_om_entity(), _extract_column_map(), _extract_criticality(), _extract_domain(), _extract_owner(), _normalize_host(), _om_entity_from_asset_type() (+1 more)

### Community 8 - "Community 8"
Cohesion: 0.7
Nodes (4): AppConfig, load_config(), _read_required(), ValueError

### Community 9 - "Community 9"
Cohesion: 0.83
Nodes (3): _recommended_actions(), render(), _severity_badge()

### Community 10 - "Community 10"
Cohesion: 0.67
Nodes (1): SummaryValidator

### Community 11 - "Community 11"
Cohesion: 1.0
Nodes (0): 

### Community 12 - "Community 12"
Cohesion: 1.0
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **4 isolated node(s):** `Raised when required auth configuration is missing or invalid.`, `Minimal GitHub REST adapter (stdlib only).      Implements an idempotent PR comm`, `Create or update a single MetaGuard bot comment on a PR.          Identification`, `Phase 4 summarizer wrapper.      Contract:     - Accepts full ImpactReport JSON`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 11`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 12`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 13`** (1 nodes): `normalizer.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `scorer.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MCPTransportError` connect `Community 0` to `Community 4`?**
  _High betweenness centrality (0.261) - this node is a cross-community bridge._
- **Why does `Asset` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 7`?**
  _High betweenness centrality (0.236) - this node is a cross-community bridge._
- **Why does `AssetType` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 7`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Are the 29 inferred relationships involving `Asset` (e.g. with `MockMetadataProvider` and `MCPMetadataProvider`) actually correct?**
  _`Asset` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `LineageGraph` (e.g. with `MockMetadataProvider` and `MCPMetadataProvider`) actually correct?**
  _`LineageGraph` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `AssetType` (e.g. with `MockMetadataProvider` and `MCPMetadataProvider`) actually correct?**
  _`AssetType` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `LineageEdge` (e.g. with `MockMetadataProvider` and `MCPMetadataProvider`) actually correct?**
  _`LineageEdge` has 19 INFERRED edges - model-reasoned connections that need verification._