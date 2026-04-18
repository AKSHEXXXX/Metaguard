# MetaGuard — Pre-Docker Checklist

## Core Engine (Must Pass)

- [ ] `src/domain/` exists with typed models for `SchemaChange`, `Asset`, `LineageEdge`, `LineageGraph`, `ImpactRecord`, `ImpactReport`
- [ ] `src/providers/base.py` defines `MetadataProvider` Protocol cleanly
- [ ] `src/providers/mock_provider.py` returns typed lineage data from fixtures
- [ ] `src/parser/diff_parser.py` parses add/drop/rename/type-change events
- [ ] `src/engine/traverser.py` performs downstream traversal with path retention and loop protection
- [ ] `src/engine/rules.py` implements ONLY the rules from `docs/RULES.md`
- [ ] `src/engine/reporter.py` builds structured `ImpactReport`
- [ ] `src/engine/renderer.py` renders deterministic PR-ready markdown report

## Tests (Must Pass)

- [ ] `pytest tests/unit/` passes with zero failures
- [ ] `pytest tests/integration/test_e2e_fixtures.py` passes all 5 scenarios
- [ ] Every rule branch in `RULES.md` has at least one unit test
- [ ] Renderer is snapshot-tested or exact-string-tested
- [ ] Traverser tested for branching paths and cycle prevention
- [ ] Unknown entity and empty-lineage cases explicitly tested
- [ ] CLI runs in mock mode and prints valid markdown report

## Fixtures (Must Exist)

- [ ] All 15 fixture JSON files exist: F1-F5 × diffs/lineage/expected
- [ ] Fixture graphs include tables, dashboards, pipelines
- [ ] Fixture graphs include column-level mappings where relevant
- [ ] Fixture graphs include owners/criticality/domain-like metadata
- [ ] Fixture loader validates JSON schema and raises on missing files

## Provider Swap (Must Work)

- [ ] Engine imports nothing OpenMetadata-specific
- [ ] Engine imports no HTTP libraries
- [ ] Engine accepts only the provider interface
- [ ] Replacing MockMetadataProvider with OpenMetadataProvider requires only config/main.py changes
- [ ] No fixture assumptions hardcoded into engine logic

## Governance Readiness (Must Exist)

- [ ] Asset model includes `owner`, `criticality`, `domain` fields
- [ ] Severity modifiers can reference asset criticality
- [ ] Report rendering surfaces owners where helpful
- [ ] Engine does not crash on missing governance fields

## OpenMetadata Integration Surface (Must Exist)

- [ ] `src/providers/openmetadata_provider.py` file exists (even if stubbed)
- [ ] `src/adapters/mcp_client.py` exists if MCP planned
- [ ] Config keys defined for OM_HOST, OM_JWT_TOKEN, traversal depth
- [ ] Environment variable names fixed (OM_HOST, OM_JWT_TOKEN)
- [ ] Logging present for failed asset resolution and empty lineage
- [ ] Smoke-test script or CLI mode planned for one known asset

## CLI (Must Work)

- [ ] `python main.py --mock --fixture F1` prints valid markdown
- [ ] `--help` shows all flags
- [ ] Handles missing fixtures gracefully
- [ ] Logs input/output clearly

## Hard Rejections (Stop Here If Any True)

- [ ] ❌ Engine only has scripts/notebooks, no module boundaries
- [ ] ❌ Tests weak or only happy path
- [ ] ❌ Mock and real provider tightly coupled
- [ ] ❌ No governance fields in asset model
- [ ] ❌ Engine has OpenMetadata-specific assumptions
- [ ] ❌ CLI cannot run in mock mode
- [ ] ❌ No logging/error handling for unresolved assets
- [ ] ❌ Fixture coverage incomplete (less than 5 scenarios)
- [ ] ❌ Rules partially implemented or untested

## Ready for Docker When All Green

When this checklist is 100% green, you have a proven analyzer ready to test against OpenMetadata.
The Docker step will only validate provider integration, not rescue core logic issues.
