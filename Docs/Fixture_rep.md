# MetaGuard — Fixture Specification

## Purpose

Fixtures are the source of truth for offline testing. Every fixture set contains three files: a diff input, a lineage graph, and an expected output. Tests pass only when engine output matches expected output exactly.

***

## Fixture Directory Layout

```
tests/fixtures/
├── diffs/
│   ├── F1_diff.json
│   ├── F2_diff.json
│   ├── F3_diff.json
│   ├── F4_diff.json
│   └── F5_diff.json
├── lineage/
│   ├── F1_lineage.json
│   ├── F2_lineage.json
│   ├── F3_lineage.json
│   ├── F4_lineage.json
│   └── F5_lineage.json
└── expected/
    ├── F1_expected.json
    ├── F2_expected.json
    ├── F3_expected.json
    ├── F4_expected.json
    └── F5_expected.json
```

***

## Diff Fixture Schema

```json
{
  "id": "F1",
  "description": "Drop customer_id from analytics.customers",
  "input_type": "normalized_change",
  "changes": [
    {
      "entity": "analytics.customers",
      "change_type": "DROP_COLUMN",
      "column": "customer_id",
      "old_type": null,
      "new_type": null,
      "source_file": "migrations/20260417_drop_customer_id.sql"
    }
  ]
}
```

***

## Lineage Fixture Schema

```json
{
  "id": "F1",
  "nodes": [
    {"id": "t1", "name": "analytics.customers", "type": "TABLE", "owner": "data_eng", "criticality": "high"},
    {"id": "t2", "name": "stg_customers", "type": "TABLE", "owner": "analytics_eng", "criticality": "medium"},
    {"id": "t3", "name": "mart_customer_360", "type": "TABLE", "owner": "analytics_eng", "criticality": "high"},
    {"id": "d1", "name": "Revenue by Customer", "type": "DASHBOARD", "owner": "bi_team", "criticality": "high"},
    {"id": "p1", "name": "nightly_customer_rollup", "type": "PIPELINE", "owner": "data_eng", "criticality": "high"}
  ],
  "edges": [
    {"from_id": "t1", "to_id": "t2", "column_map": [{"from": "customer_id", "to": "customer_id"}]},
    {"from_id": "t2", "to_id": "t3", "column_map": [{"from": "customer_id", "to": "customer_id"}]},
    {"from_id": "t3", "to_id": "d1", "column_map": [{"from": "customer_id", "to": "customer_id"}]},
    {"from_id": "t1", "to_id": "p1", "column_map": null}
  ]
}
```

***

## Expected Output Fixture Schema

```json
{
  "id": "F1",
  "highest_severity": "CRITICAL",
  "total_affected": 4,
  "records": [
    {
      "asset_id": "t2",
      "asset_name": "stg_customers",
      "asset_type": "TABLE",
      "severity": "CRITICAL",
      "confidence": "HIGH",
      "reason": "Downstream asset directly uses dropped column customer_id via column-level lineage",
      "path": ["analytics.customers.customer_id", "stg_customers.customer_id"]
    },
    {
      "asset_id": "t3",
      "asset_name": "mart_customer_360",
      "asset_type": "TABLE",
      "severity": "CRITICAL",
      "confidence": "HIGH",
      "reason": "Downstream asset uses dropped column through stg_customers",
      "path": ["analytics.customers.customer_id", "stg_customers.customer_id", "mart_customer_360.customer_id"]
    },
    {
      "asset_id": "d1",
      "asset_name": "Revenue by Customer",
      "asset_type": "DASHBOARD",
      "severity": "CRITICAL",
      "confidence": "HIGH",
      "reason": "Dashboard depends on mart_customer_360 which uses dropped column",
      "path": ["analytics.customers.customer_id", "stg_customers.customer_id", "mart_customer_360.customer_id", "Revenue by Customer"]
    },
    {
      "asset_id": "p1",
      "asset_name": "nightly_customer_rollup",
      "asset_type": "PIPELINE",
      "severity": "HIGH",
      "confidence": "MEDIUM",
      "reason": "Pipeline depends on analytics.customers but column-level lineage not available",
      "path": ["analytics.customers", "nightly_customer_rollup"]
    }
  ]
}
```

***

## All 5 Fixture Scenarios

### F1 — DROP_COLUMN used by 3 tables, 1 dashboard, 1 pipeline
- Expected: CRITICAL severity, HIGH confidence for column-mapped assets
- Expected: HIGH severity, MEDIUM confidence for pipeline (no column map)
- Total affected: 4

### F2 — ADD_COLUMN with no downstream consumers
- Lineage has no downstream of the changed entity
- Expected: 0 impact records
- Highest severity: LOW
- Total affected: 0

### F3 — ALTER_TYPE incompatible (INT to STRING on order_amount)
- Column lineage to 2 downstream tables
- Expected: HIGH severity, HIGH confidence for both
- Total affected: 2

### F4 — RENAME_COLUMN with backward-compatible alias in column_map
- Column map contains alias entry
- Expected: MEDIUM severity (not CRITICAL), HIGH confidence
- Total affected: 2

### F5 — DROP_COLUMN with table-level lineage only (no column_map)
- No column-level lineage exists
- Expected: HIGH severity, MEDIUM confidence
- Reason must mention: column-level lineage missing, table-level dependency confirmed
- Total affected: 2

***

## Fixture Loader Utility

```python
import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent

def load_diff(fixture_id: str) -> dict:
    path = FIXTURE_DIR / "diffs" / f"{fixture_id}_diff.json"
    if not path.exists():
        raise FileNotFoundError(f"Diff fixture {fixture_id} not found at {path}")
    return json.loads(path.read_text())

def load_lineage(fixture_id: str) -> dict:
    path = FIXTURE_DIR / "lineage" / f"{fixture_id}_lineage.json"
    if not path.exists():
        raise FileNotFoundError(f"Lineage fixture {fixture_id} not found at {path}")
    return json.loads(path.read_text())

def load_expected(fixture_id: str) -> dict:
    path = FIXTURE_DIR / "expected" / f"{fixture_id}_expected.json"
    if not path.exists():
        raise FileNotFoundError(f"Expected fixture {fixture_id} not found at {path}")
    return json.loads(path.read_text())
```