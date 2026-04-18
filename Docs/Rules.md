# MetaGuard — Impact Rules

## Purpose

This document is the single source of truth for how impact severity and confidence are computed. `engine/rules.py` must implement exactly these rules. No rule may exist in the engine that is not documented here. No rule documented here may be absent from the engine.

***

## Severity Scale

| Level | Meaning |
|-------|---------|
| CRITICAL | Very high probability of downstream breakage; immediate action required |
| HIGH | Significant risk; downstream consumers likely affected |
| MEDIUM | Noticeable risk; some consumers may be affected |
| LOW | Minimal risk; unlikely to cause downstream issues |

***

## Confidence Scale

| Level | Meaning |
|-------|---------|
| HIGH | Column-level lineage confirmed the dependency |
| MEDIUM | Table-level dependency confirmed but no column-level lineage |
| LOW | Heuristic or naming-based match only; uncertain |

***

## Rule: DROP_COLUMN

| Condition | Severity | Confidence | Reason |
|-----------|----------|------------|--------|
| Downstream has column-level lineage referencing dropped column | CRITICAL | HIGH | Direct column dependency on dropped field |
| Downstream has table-level lineage only (no column map) | HIGH | MEDIUM | Table dependency confirmed; column usage unknown |
| No downstream lineage found | LOW | HIGH | No consumers detected |

***

## Rule: RENAME_COLUMN

| Condition | Severity | Confidence | Reason |
|-----------|----------|------------|--------|
| Downstream has column-level lineage; no alias in column map | CRITICAL | HIGH | Rename breaks direct column reference |
| Downstream has column-level lineage; alias entry exists in column map | MEDIUM | HIGH | Alias provides backward compatibility but risk exists |
| Downstream has table-level lineage only | HIGH | MEDIUM | Column rename may break; cannot confirm without column map |
| No downstream lineage | LOW | HIGH | No consumers detected |

***

## Rule: ALTER_TYPE

| Condition | Severity | Confidence | Reason |
|-----------|----------|------------|--------|
| Incompatible type change with column-level lineage | HIGH | HIGH | Type mismatch likely breaks downstream computation |
| Compatible type change with column-level lineage | LOW | HIGH | Widening type change unlikely to break |
| Any type change with table-level lineage only | MEDIUM | MEDIUM | Type impact uncertain without column-level confirmation |
| No downstream lineage | LOW | HIGH | No consumers detected |

### Incompatible type pairs (non-exhaustive)
- INT → STRING or VARCHAR
- STRING → INT, FLOAT, BOOLEAN
- DATE → STRING
- BOOLEAN → INT (default MEDIUM)

### Compatible type pairs (non-exhaustive)
- INT → BIGINT
- VARCHAR(n) → VARCHAR(m) where m > n
- FLOAT → DOUBLE

***

## Rule: ALTER_NULLABILITY

| Condition | Severity | Confidence | Reason |
|-----------|----------|------------|--------|
| NOT NULL → NULL with column lineage | LOW | HIGH | Loosening constraint; unlikely to break consumers |
| NULL → NOT NULL with column lineage | HIGH | HIGH | Tightening constraint; may break inserts in dependent pipelines |
| Any nullability change with table-level lineage only | MEDIUM | MEDIUM | Cannot confirm impact without column-level lineage |
| No downstream lineage | LOW | HIGH | No consumers detected |

***

## Rule: ADD_COLUMN

| Condition | Severity | Confidence | Reason |
|-----------|----------|------------|--------|
| New column; no downstream consumers reference it | LOW | HIGH | Additive change; no breakage expected |
| Strict schema consumer detected via metadata tag | MEDIUM | LOW | Heuristic only; possible strict schema consumer |

***

## Confidence Modifiers

| Condition | Effect |
|-----------|--------|
| Column-level lineage confirmed | Keep or raise to HIGH |
| Only table-level lineage available | Cap at MEDIUM |
| Asset resolved via heuristic name match | Cap at LOW |
| Asset not resolvable | Severity keeps; Confidence = LOW; reason = "asset not resolved" |
| Lineage graph is empty | All records LOW severity, LOW confidence |

***

## Path Computation Rules

- Path is ordered from changed source to affected downstream asset
- Each element: `{entity_name}.{column_name}` if column known, else `{entity_name}`
- If column map is available, show column names in path
- If column map is absent, show entity names only
- Max traversal depth: configurable, default 5

***

## Recommended Actions by Severity

### CRITICAL
- Confirm downstream assets explicitly use the affected column before merging
- Add a compatibility alias or view layer
- Coordinate with downstream owners
- Consider staged deprecation

### HIGH
- Review downstream query definitions for the affected field
- Run integration tests covering affected assets
- Notify asset owners listed in metadata

### MEDIUM
- Check for strict schema consumers
- Run validation queries post-deploy

### LOW
- No immediate action required
- Monitor for unexpected errors after deploy

***

## Severity Aggregation

`ImpactReport.highest_severity` = maximum severity across all `ImpactRecord` entries.
If records is empty, `highest_severity` = LOW.