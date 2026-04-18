# MetaGuard — AI Agent Guide

## Objective

Build the MetaGuard impact analyzer engine. Start from domain models. Work through to a tested CLI runner. External integration comes only after Phase 1 tests all pass.

***

## Agent Operating Rules

### Rule 1 — Determinism first
The core engine must be deterministic. Given the same inputs it must always produce the same outputs. No randomness, no LLM inference inside the engine.

### Rule 2 — Do not invent data
Never invent asset names, lineage edges, or severity scores not derivable from the input graph and RULES.md. If data is missing, degrade confidence — do not guess.

### Rule 3 — Follow the interface
`MetadataProvider` is a Protocol. The engine accepts a provider but must not know whether it is mock or real. Never call OpenMetadata APIs from `engine/`.

### Rule 4 — Test before integration
All engine logic must have unit and fixture tests before any adapter is implemented. If a test does not exist for a rule, write it before writing the rule.

### Rule 5 — One source of truth for rules
Severity and confidence scoring rules live only in `RULES.md` and `engine/rules.py`. Do not restate or reinterpret them anywhere else.

### Rule 6 — LLM is post-processing only
LLM may summarize the rendered markdown. LLM must not determine severity, confidence, asset identity, or path. Validate LLM output against report facts before using it.

### Rule 7 — Graceful degradation
If an entity cannot be resolved, return `confidence=LOW` with a clear reason. If lineage is empty, return zero impact records with a warning. Never raise unhandled exceptions in the engine.

***

## Build Order

Follow the exact order from SOP.md. Do not skip steps. Each step has a test gate — do not proceed until tests for the current step pass.

```
Step 1.1  Project scaffold              pytest runs clean
Step 1.2  Domain models                 model instantiation tests pass
Step 1.3  Provider interface            mock class satisfies protocol
Step 1.4  Fixture loader                all 5 fixtures load cleanly
Step 1.5  Mock provider                 resolves fixtures; raises on unknown
Step 1.6  Diff parser                   each SQL pattern → correct ChangeType
Step 1.7  Asset resolver                known resolves; unknown degrades
Step 1.8  Lineage traverser             BFS returns correct paths
Step 1.9  Impact rules engine           each rule → deterministic output
Step 1.10 Report builder                correct counts and severity
Step 1.11 PR markdown renderer          markdown matches expected fixture
Step 1.12 End-to-end tests              all 5 e2e tests pass → Phase 1 done
```

***

## Definition of Done for Phase 1

- [ ] All 5 fixture scenarios have passing end-to-end tests
- [ ] Unit tests exist for every rule condition in RULES.md
- [ ] Mock provider returns correct assets and lineage for all fixtures
- [ ] Renderer produces valid markdown for all 5 fixtures
- [ ] `main.py` CLI runs with `--mock` flag and prints PR comment to stdout
- [ ] No OpenMetadata, GitHub, or LLM code is called in any Phase 1 test
- [ ] All tests pass offline with `pytest`

***

## Required Test Fixtures

| ID | Change Type | Expected Severity | Expected Confidence | Notes |
|----|-------------|------------------|-------------------|-------|
| F1 | DROP_COLUMN (used downstream) | CRITICAL | HIGH | 3 tables + 1 dashboard + 1 pipeline affected |
| F2 | ADD_COLUMN (no consumers) | LOW | HIGH | Zero downstream impact |
| F3 | ALTER_TYPE incompatible | HIGH | HIGH | INT to STRING on directly referenced column |
| F4 | RENAME_COLUMN (alias available) | MEDIUM | HIGH | Alias lowers severity from CRITICAL |
| F5 | DROP_COLUMN (table-level lineage only) | HIGH | MEDIUM | No column map lowers confidence |

***

## Common Mistakes to Avoid

| Mistake | Correct behavior |
|---------|-----------------|
| Calling OM API in engine | Use provider interface |
| LLM computing severity | LLM post-processes only |
| Guessing asset name | Degrade confidence, label as unknown |
| Skipping fixture tests | Fixture tests are mandatory |
| Hardcoding entity names | Use provider and config |

***

## Output Contract

Every valid pipeline run must produce:
1. `ImpactReport` with: `records`, `highest_severity`, `total_affected`, `generated_at`
2. Markdown string with: severity badge, asset list, reason per asset, path per asset, recommended actions

***

## Error Handling Contract

| Error condition | Required behavior |
|-----------------|------------------|
| Entity not in provider | LOW confidence, reason = "asset not resolved" |
| Empty lineage graph | Zero records with warning |
| Unknown SQL pattern | UNKNOWN change type, skip impact for that change |
| LLM API failure | Fall back to deterministic renderer |
| Missing fixture file | Raise `FixtureNotFoundError` |

***

## Code Style

- Python type hints everywhere
- `dataclass` for domain models
- `Protocol` for interfaces
- `Enum` for all categorical values
- `pytest` with fixtures for tests
- `pathlib.Path` for all file paths
- Functions under 30 lines where possible
- Rule functions named: `rule_drop_column`, `rule_rename_column`, etc.