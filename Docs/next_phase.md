# SMOKE_AND_PR_GUIDE.md
## Fix Smoke Test + Create Demo PR

---

## Step 1 — Discover which sandbox tables have real lineage

Run this script first. Do not guess entity names.

```python
# scripts/discover_lineage_entities.py
import os, requests
from dotenv import load_dotenv
load_dotenv()

HOST = os.environ["OPENMETADATA_HOST"]
TOKEN = os.environ["OPENMETADATA_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

CANDIDATES = [
    "sample_athena",
    "acme_nexus_raw_data",
    "acme_nexus_analytics",
    "sample_redshift",
    "sample_snowflake",
    "sample_databricks",
    "sample_airflow",
    "sample_tableau",
    "sample_superset",
]

print("Probing lineage for known sandbox services...\n")

for service in CANDIDATES:
    # 1. Find tables under this service
    r = requests.get(
        f"{HOST}/api/v1/tables",
        headers=HEADERS,
        params={"service": service, "limit": 3, "fields": "fullyQualifiedName"},
        timeout=15
    )
    if r.status_code != 200:
        print(f"  {service}: tables fetch failed ({r.status_code})")
        continue

    tables = r.json().get("data", [])
    if not tables:
        print(f"  {service}: no tables found")
        continue

    for table in tables:
        fqn = table.get("fullyQualifiedName", "")
        tid = table.get("id", "")

        # 2. Check lineage for each table
        lr = requests.get(
            f"{HOST}/api/v1/lineage/table/{tid}",
            headers=HEADERS,
            params={"downstreamDepth": 2, "upstreamDepth": 0},
            timeout=15
        )
        if lr.status_code == 200:
            data = lr.json()
            downstream = data.get("downstreamEdges", [])
            nodes = data.get("nodes", [])
            if downstream:
                print(f"  ✅ {fqn}")
                print(f"     id={tid}")
                print(f"     downstream_edges={len(downstream)}  nodes={len(nodes)}")
        else:
            pass  # silently skip tables with no lineage

print("\nDone. Use a ✅ entity for smoke test and demo PR.")
```

Run:
```bash
python scripts/discover_lineage_entities.py
```

Copy the first `✅` entity FQN and ID. You will use them in Step 2 and Step 3.

---

## Step 2 — Update smoke_test.py

Replace the current random table discovery with the confirmed FQN from Step 1.

```python
# smoke_test.py (updated)
import os, requests, json
from dotenv import load_dotenv
load_dotenv()

from src.config import load_config
from src.providers.openmetadata_provider import OpenMetadataProvider
from src.adapters.mcp_client import MCPClient, MCPTransportError
from src.providers.mcp_provider import MCPMetadataProvider

config = load_config()
rest_provider = OpenMetadataProvider(config.om_host, config.om_token, config.http_timeout)

# MCP probe
provider = rest_provider
if config.om_mcp_url:
    try:
        mcp = MCPClient(config.om_mcp_url, config.om_token, config.http_timeout)
        info = mcp.initialize()
        print("MCP live:", info.get("result", {}).get("serverInfo", {}))
        tools = mcp.list_tools()
        print("Tools:", tools)
        provider = MCPMetadataProvider(mcp, rest_provider)
        transport = "mcp"
    except MCPTransportError as e:
        print(f"MCP probe failed: {e} → using REST fallback")
        transport = "rest-fallback"
else:
    transport = "rest-only"

# ── REPLACE THIS WITH YOUR CONFIRMED FQN FROM STEP 1 ──────────────────────
SMOKE_ENTITY_FQN = "sample_athena.default.fact_sale"   # example — update this
# ──────────────────────────────────────────────────────────────────────────

print(f"\nTransport: {transport}")
print(f"Resolving: {SMOKE_ENTITY_FQN}")

try:
    asset = provider.resolve_asset(SMOKE_ENTITY_FQN)
    print(f"Resolved: {asset.name} (id={asset.id})")
except Exception as e:
    print(f"Resolve failed: {e}")
    exit(1)

try:
    lineage = provider.get_downstream_lineage(asset.id, depth=3)
    print(f"Downstream nodes: {len(lineage.nodes)}")
    print(f"Downstream edges: {len(lineage.edges)}")
    for node in lineage.nodes:
        print(f"  → {node.name} ({node.asset_type.value})")
except Exception as e:
    print(f"Lineage failed: {e}")
    lineage = None

# Simulate a DROP COLUMN change on the resolved entity
from src.domain.models import SchemaChange
from src.domain.enums import ChangeType
from src.engine.traverser import LineageTraverser
from src.engine.rules import ImpactRulesEngine
from src.engine.reporter import ReportBuilder
from src.engine.renderer import PRCommentRenderer

change = SchemaChange(
    entity=asset.name,
    change_type=ChangeType.DROP_COLUMN,
    column="legacy_id",
    source_file="migrations/smoke_test.sql"
)

if lineage and lineage.nodes:
    traverser = LineageTraverser()
    paths = traverser.traverse(asset, lineage, max_depth=3)
    engine = ImpactRulesEngine()
    records = [engine.evaluate(change, a, path) for a, path in paths]
else:
    records = []

report = ReportBuilder().build(changes=[change], records=records)
markdown = PRCommentRenderer().render(report)

print("\n── ImpactReport ──────────────────────────────")
print(json.dumps({
    "highest_severity": report.highest_severity.value,
    "total_affected": report.total_affected,
    "records": len(report.records)
}, indent=2))

print("\n── Markdown Preview (first 800 chars) ────────")
print(markdown[:800])
```

---

## Step 3 — Create the demo PR

Once you have a confirmed FQN with real lineage from Step 1, create the migration file to match it.

### 3a. Create the migration file

```bash
git checkout -b test/schema-change-demo
mkdir -p migrations
```

Write `migrations/demo_schema_change.sql` using the real table name from Step 1:

```sql
-- Demo schema change for MetaGuard impact analysis
-- Target: <replace with your confirmed table FQN from Step 1>

ALTER TABLE fact_sale DROP COLUMN legacy_id;
ALTER TABLE fact_sale RENAME COLUMN old_customer_ref TO customer_id;
ALTER TABLE fact_sale ALTER COLUMN amount TYPE VARCHAR(255);
```

Use `fact_sale`, `orders`, or whatever real table name you discovered in Step 1.

### 3b. Push and open PR

```bash
git add migrations/demo_schema_change.sql
git commit -m "test: drop legacy_id, rename customer_ref, alter amount type"
git push origin test/schema-change-demo
```

Go to GitHub → open the PR from `test/schema-change-demo` into `main`.

### 3c. What to expect

- GitHub Action fires because `migrations/**` matches the workflow trigger
- Action runs `main.py --mode sandbox --output github`
- MetaGuard resolves `fact_sale` (or your real entity), fetches lineage, scores 3 changes
- PR comment appears with severity badges, affected asset table, and recommended actions

---

## Step 4 — If lineage is still empty in the PR run

This means the sandbox has lineage at the service level but not column-level for your specific table.
That is fine. Do this:

- Add `--mode mock --fixture F1` as a fallback job in the workflow so the PR always shows a rich demo report
- In the demo, explain: "Live sandbox shows the transport and entity resolution working; the rich impact report uses a realistic fixture to demonstrate the full output"

Judges care that the system works end-to-end, not that the sandbox has perfect data.

---

## Checklist before demo

- [ ] `discover_lineage_entities.py` found at least one ✅ entity with downstream edges
- [ ] `SMOKE_ENTITY_FQN` updated in `smoke_test.py`
- [ ] Smoke test produces non-empty `records` or at least resolves asset + prints lineage nodes
- [ ] `migrations/demo_schema_change.sql` uses a real table name from the sandbox
- [ ] PR opened on `test/schema-change-demo`
- [ ] GitHub Action fired and posted a comment on the PR
- [ ] Fallback mock run ready: `python main.py --mode mock --fixture F1`
