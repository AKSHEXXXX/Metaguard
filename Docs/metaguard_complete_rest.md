# METAGUARD_COMPLETE_REST.md
## MetaGuard — Complete Build Guide (REST Path)

This is the single source of truth for building MetaGuard end-to-end using OpenMetadata REST API.
No Docker. No localhost. Sandbox is the live OM instance.

---

## Stack

- Language: Python
- OpenMetadata: REST API at `https://sandbox.open-metadata.org`
- Auth: PAT via `Authorization: Bearer $OPENMETADATA_TOKEN`
- GitHub: PR events via GitHub Actions + GitHub REST API
- LLM: OpenAI `gpt-4o-mini` via `OPENAI_API_KEY`

---

## Environment Variables

```env
OPENMETADATA_HOST=https://sandbox.open-metadata.org
OPENMETADATA_TOKEN=your_pat_here
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini
GITHUB_TOKEN=your_github_token_here
APP_ENV=dev
LOG_LEVEL=INFO
LINEAGE_MAX_DEPTH=5
HTTP_TIMEOUT_SECONDS=30
ENABLE_LLM_SUMMARY=true
ENABLE_GITHUB_COMMENT=true
```

Never hardcode any of these. Never commit `.env`. Add `.env` to `.gitignore`.

---

## Project Folder Structure

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
│   │   ├── reporter.py
│   │   └── renderer.py
│   ├── adapters/
│   │   └── github_adapter.py
│   └── llm/
│       ├── summarizer.py
│       └── validator.py
├── tests/
│   ├── fixtures/
│   │   ├── diffs/
│   │   ├── lineage/
│   │   └── expected/
│   ├── unit/
│   └── integration/
├── .github/
│   └── workflows/
│       └── metaguard.yml
├── smoke_test.py
├── main.py
├── .env
└── requirements.txt
```

---

## PHASE 1 — Core Engine (Offline, Fixture-Driven)

### Goal
A fully working deterministic analyzer with no external dependencies.

### Step 1.1 — Scaffold
- Create folder structure above
- Create virtual environment
- `requirements.txt`: `pytest`, `click`, `requests`, `python-dotenv`, `openai`
- Add `.gitignore` with `.env`, `__pycache__`, `.pytest_cache`

**Test gate:** `pytest` runs clean with zero tests.

---

### Step 1.2 — Domain models
File: `src/domain/enums.py`
```python
from enum import Enum

class ChangeType(Enum):
    ADD_COLUMN = "ADD_COLUMN"
    DROP_COLUMN = "DROP_COLUMN"
    RENAME_COLUMN = "RENAME_COLUMN"
    ALTER_TYPE = "ALTER_TYPE"
    ALTER_NULLABILITY = "ALTER_NULLABILITY"
    UNKNOWN = "UNKNOWN"

class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Confidence(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AssetType(Enum):
    TABLE = "TABLE"
    VIEW = "VIEW"
    DASHBOARD = "DASHBOARD"
    PIPELINE = "PIPELINE"
    MODEL = "MODEL"
    FEATURE_STORE = "FEATURE_STORE"
```

File: `src/domain/models.py`
```python
from dataclasses import dataclass, field
from .enums import ChangeType, Severity, Confidence, AssetType

@dataclass
class SchemaChange:
    entity: str
    change_type: ChangeType
    column: str | None = None
    old_type: str | None = None
    new_type: str | None = None
    source_file: str | None = None

@dataclass
class Asset:
    id: str
    name: str
    asset_type: AssetType
    owner: str | None = None
    criticality: str | None = None
    domain: str | None = None

@dataclass
class LineageEdge:
    from_id: str
    to_id: str
    column_map: list[dict] | None = None

@dataclass
class LineageGraph:
    nodes: list[Asset] = field(default_factory=list)
    edges: list[LineageEdge] = field(default_factory=list)

@dataclass
class ImpactRecord:
    asset_id: str
    asset_name: str
    asset_type: AssetType
    severity: Severity
    confidence: Confidence
    reason: str
    path: list[str] = field(default_factory=list)

@dataclass
class ImpactReport:
    changes: list[SchemaChange] = field(default_factory=list)
    records: list[ImpactRecord] = field(default_factory=list)
    highest_severity: Severity = Severity.LOW
    total_affected: int = 0
    generated_at: str = ""
    engine_version: str = "1.0.0"
```

**Test gate:** All models instantiate with correct field types.

---

### Step 1.3 — Provider interface
File: `src/providers/base.py`
```python
from typing import Protocol
from src.domain.models import Asset, LineageGraph

class MetadataProvider(Protocol):
    def resolve_asset(self, entity_ref: str) -> Asset: ...
    def get_downstream_lineage(self, asset_id: str, depth: int) -> LineageGraph: ...
```

---

### Step 1.4 — Fixture loader
Folder: `tests/fixtures/`
- `diffs/F1_diff.json` through `F5_diff.json`
- `lineage/F1_lineage.json` through `F5_lineage.json`
- `expected/F1_expected.json` through `F5_expected.json`

See `docs/FIXTURE_SPEC.md` for exact JSON schemas.

File: `tests/fixtures/loader.py`
```python
import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent

def load_diff(fixture_id: str) -> dict:
    path = FIXTURE_DIR / "diffs" / f"{fixture_id}_diff.json"
    if not path.exists():
        raise FileNotFoundError(f"Diff fixture {fixture_id} not found")
    return json.loads(path.read_text())

def load_lineage(fixture_id: str) -> dict:
    path = FIXTURE_DIR / "lineage" / f"{fixture_id}_lineage.json"
    if not path.exists():
        raise FileNotFoundError(f"Lineage fixture {fixture_id} not found")
    return json.loads(path.read_text())

def load_expected(fixture_id: str) -> dict:
    path = FIXTURE_DIR / "expected" / f"{fixture_id}_expected.json"
    if not path.exists():
        raise FileNotFoundError(f"Expected fixture {fixture_id} not found")
    return json.loads(path.read_text())
```

**Test gate:** All 5 fixture IDs load without error.

---

### Step 1.5 — Mock provider
File: `src/providers/mock_provider.py`
- Reads lineage from fixture JSON
- `resolve_asset` returns `Asset` from fixture nodes
- Raises `AssetNotFoundError` for unknown refs

**Test gate:** F1 loads; unknown ref raises.

---

### Step 1.6 — Diff parser
File: `src/parser/diff_parser.py`
- Parses raw SQL strings
- Detects: `DROP COLUMN`, `ADD COLUMN`, `RENAME COLUMN`, `ALTER COLUMN TYPE`
- Returns list of `SchemaChange`

**Test gate:** One test per SQL pattern, correct `ChangeType` returned.

---

### Step 1.7 — Asset resolver
File: `src/parser/normalizer.py`
- Maps `SchemaChange.entity` to a provider `Asset`
- Degrades to `confidence=LOW` if unresolved

**Test gate:** Known entity resolves; unknown returns LOW confidence.

---

### Step 1.8 — Lineage traverser
File: `src/engine/traverser.py`
- BFS from root asset ID
- Returns `list[tuple[Asset, list[str]]]` — (asset, path)
- Max depth configurable; cycle-safe

**Test gate:** F1 graph returns 4 downstream assets with correct paths.

---

### Step 1.9 — Rules engine
File: `src/engine/rules.py`
- `rule_drop_column`, `rule_rename_column`, `rule_alter_type`, `rule_alter_nullability`, `rule_add_column`
- Each returns `ImpactRecord`
- Rules match `docs/RULES.md` exactly

**Test gate:** Minimum 12 tests, one per rule branch.

---

### Step 1.10 — Report builder
File: `src/engine/reporter.py`
- Aggregates `ImpactRecord` list into `ImpactReport`
- Sets `highest_severity`, `total_affected`, `generated_at`

**Test gate:** 3 records → correct highest severity and count.

---

### Step 1.11 — Markdown renderer
File: `src/engine/renderer.py`
- Converts `ImpactReport` into PR-ready markdown
- Must include: severity badge, asset table, path, owners, recommended actions
- Does not invent facts; only formats report data

**Test gate:** F1 report renders markdown containing `stg_customers`, `CRITICAL`.

---

### Step 1.12 — End-to-end fixture tests
File: `tests/integration/test_e2e_fixtures.py`
- Wire all Phase 1 components
- Run F1–F5

**Test gate:** All 5 pass. Phase 1 complete.

---

## PHASE 2 — OpenMetadata REST Integration

### Goal
Replace `MockMetadataProvider` with `OpenMetadataProvider` reading from sandbox.
Core engine untouched.

### Step 2.1 — Config reader
File: `src/config.py`
```python
import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    om_host: str
    om_token: str
    lineage_max_depth: int = 5
    http_timeout: int = 30

def load_config() -> AppConfig:
    host = os.getenv("OPENMETADATA_HOST")
    token = os.getenv("OPENMETADATA_TOKEN")
    if not host or not token:
        raise ValueError("OPENMETADATA_HOST and OPENMETADATA_TOKEN must be set")
    return AppConfig(
        om_host=host,
        om_token=token,
        lineage_max_depth=int(os.getenv("LINEAGE_MAX_DEPTH", 5)),
        http_timeout=int(os.getenv("HTTP_TIMEOUT_SECONDS", 30)),
    )
```

**Test gate:** Missing env vars raise `ValueError`.

---

### Step 2.2 — OpenMetadataProvider
File: `src/providers/openmetadata_provider.py`

```python
import requests
from src.domain.models import Asset, LineageGraph, LineageEdge
from src.domain.enums import AssetType

class OpenMetadataProvider:
    def __init__(self, host: str, token: str, timeout: int = 30):
        self.base = host.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        self.timeout = timeout

    def resolve_asset(self, entity_ref: str) -> Asset:
        url = f"{self.base}/api/v1/tables"
        resp = requests.get(url, headers=self.headers,
                           params={"fields": "owner,tags,tier", "name": entity_ref},
                           timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        item = data["data"][0] if data.get("data") else None
        if not item:
            raise AssetNotFoundError(entity_ref)
        return Asset(
            id=item["fullyQualifiedName"],
            name=item["name"],
            asset_type=AssetType.TABLE,
            owner=item.get("owner", {}).get("name"),
            criticality=self._extract_tier(item.get("tags", [])),
        )

    def get_downstream_lineage(self, asset_id: str, depth: int) -> LineageGraph:
        url = f"{self.base}/api/v1/lineage/table/{asset_id}"
        resp = requests.get(url, headers=self.headers,
                           params={"upstreamDepth": 0, "downstreamDepth": depth},
                           timeout=self.timeout)
        if resp.status_code == 404:
            return LineageGraph()
        resp.raise_for_status()
        return self._map_lineage(resp.json())

    def _extract_tier(self, tags: list) -> str | None:
        for tag in tags:
            if tag.get("tagFQN", "").startswith("Tier"):
                return tag["tagFQN"]
        return None

    def _map_lineage(self, data: dict) -> LineageGraph:
        nodes, edges = [], []
        for node in data.get("nodes", []):
            nodes.append(Asset(
                id=node.get("fullyQualifiedName", node["id"]),
                name=node.get("name", ""),
                asset_type=self._map_type(node.get("type", "table")),
            ))
        for edge in data.get("downstreamEdges", []):
            edges.append(LineageEdge(
                from_id=edge["fromEntity"],
                to_id=edge["toEntity"],
                column_map=edge.get("columns"),
            ))
        return LineageGraph(nodes=nodes, edges=edges)

    def _map_type(self, t: str) -> AssetType:
        mapping = {"table": AssetType.TABLE, "dashboard": AssetType.DASHBOARD,
                   "pipeline": AssetType.PIPELINE, "mlmodel": AssetType.MODEL}
        return mapping.get(t.lower(), AssetType.TABLE)
```

**Test gate:** Unit test with mocked HTTP. Assert correct `Asset` and `LineageGraph` mapping.

---

### Step 2.3 — Smoke test
File: `smoke_test.py`
```python
from dotenv import load_dotenv
load_dotenv()
from src.config import load_config
from src.providers.openmetadata_provider import OpenMetadataProvider

config = load_config()
provider = OpenMetadataProvider(config.om_host, config.om_token, config.http_timeout)

import requests
resp = requests.get(f"{config.om_host}/api/v1/tables",
                    headers={"Authorization": f"Bearer {config.om_token}"},
                    params={"limit": 1}, timeout=config.http_timeout)
print("Status:", resp.status_code)
tables = resp.json().get("data", [])
if tables:
    table = tables[0]
    print("First table:", table["fullyQualifiedName"])
    lineage = provider.get_downstream_lineage(table["fullyQualifiedName"], depth=3)
    print("Downstream nodes:", len(lineage.nodes))
else:
    print("No tables found in sandbox.")
```

Run:
```bash
python smoke_test.py
```

**Pass criteria:** `200`, at least one table name printed, lineage call succeeds without crash.

---

## PHASE 3 — GitHub PR Automation

### Goal
Trigger analysis from real PRs. Fetch changed files, run analyzer, post markdown comment.

### Step 3.1 — GitHubAdapter
File: `src/adapters/github_adapter.py`

```python
import os
import requests

GITHUB_API = "https://api.github.com"
BOT_TAG = "<!-- metaguard-report -->"

class GitHubAdapter:
    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.headers = {"Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json"}

    def get_changed_files(self, pr_number: int) -> list[str]:
        url = f"{GITHUB_API}/repos/{self.repo}/pulls/{pr_number}/files"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return [f["filename"] for f in resp.json()]

    def post_or_update_comment(self, pr_number: int, body: str):
        body_with_tag = f"{BOT_TAG}\n{body}"
        existing = self._find_bot_comment(pr_number)
        if existing:
            url = f"{GITHUB_API}/repos/{self.repo}/issues/comments/{existing}"
            requests.patch(url, headers=self.headers, json={"body": body_with_tag})
        else:
            url = f"{GITHUB_API}/repos/{self.repo}/issues/{pr_number}/comments"
            requests.post(url, headers=self.headers, json={"body": body_with_tag})

    def _find_bot_comment(self, pr_number: int) -> int | None:
        url = f"{GITHUB_API}/repos/{self.repo}/issues/{pr_number}/comments"
        resp = requests.get(url, headers=self.headers)
        for c in resp.json():
            if BOT_TAG in c.get("body", ""):
                return c["id"]
        return None
```

**Test gate:** Mock HTTP; assert update used when comment exists; assert create used when not.

---

### Step 3.2 — GitHub Action YAML
File: `.github/workflows/metaguard.yml`

```yaml
name: MetaGuard Schema Impact Analysis

on:
  pull_request:
    types: [opened, synchronize, reopened]
    paths:
      - 'migrations/**'
      - 'dbt/models/**'
      - 'schemas/**'
      - '**/*.sql'
      - '**/*.yaml'
      - '**/*.avsc'
      - '**/*.proto'

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run MetaGuard
        env:
          OPENMETADATA_HOST: ${{ secrets.OPENMETADATA_HOST }}
          OPENMETADATA_TOKEN: ${{ secrets.OPENMETADATA_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ENABLE_LLM_SUMMARY: "true"
          ENABLE_GITHUB_COMMENT: "true"
        run: |
          python main.py \
            --mode sandbox \
            --pr-number ${{ github.event.pull_request.number }} \
            --repo ${{ github.repository }} \
            --output github
```

**Test gate:** YAML parses correctly. Path filter blocks non-schema PRs.

---

### Step 3.3 — CLI main.py

```python
import click
from dotenv import load_dotenv
load_dotenv()

@click.command()
@click.option('--mode', default='mock', type=click.Choice(['mock', 'sandbox']))
@click.option('--fixture', default=None)
@click.option('--changed-files', default=None)
@click.option('--pr-number', default=None, type=int)
@click.option('--repo', default=None)
@click.option('--output', default='stdout', type=click.Choice(['stdout', 'github']))
def main(mode, fixture, changed_files, pr_number, repo, output):
    from src.config import load_config
    from src.engine.reporter import ReportBuilder
    from src.engine.renderer import PRCommentRenderer

    if mode == 'mock':
        from src.providers.mock_provider import MockMetadataProvider
        from tests.fixtures.loader import load_diff, load_lineage
        provider = MockMetadataProvider(fixture)
        # run engine with fixture data
    else:
        from src.providers.openmetadata_provider import OpenMetadataProvider
        config = load_config()
        provider = OpenMetadataProvider(config.om_host, config.om_token)
        # parse changed files, resolve, traverse, score

    # build report and render
    renderer = PRCommentRenderer()
    markdown = renderer.render(report)

    if output == 'github' and pr_number and repo:
        import os
        from src.adapters.github_adapter import GitHubAdapter
        gh = GitHubAdapter(repo, os.getenv("GITHUB_TOKEN"))
        gh.post_or_update_comment(pr_number, markdown)
    else:
        print(markdown)

if __name__ == '__main__':
    main()
```

**Test gate:** `python main.py --mode mock --fixture F1` prints markdown.

---

## PHASE 4 — LLM Summarizer

### Goal
Use OpenAI to improve PR comment readability. LLM must not change facts.

### Step 4.1 — LLMSummarizer
File: `src/llm/summarizer.py`

```python
import os
from openai import OpenAI
from src.domain.models import ImpactReport

SYSTEM_PROMPT = """You are a technical writer summarizing a schema impact report.
Rewrite ONLY the prose explanation sections to be more readable.
DO NOT change: asset names, severity labels, confidence values, impact counts, dependency paths, or recommended actions.
Return only improved markdown. Do not add new facts."""

class LLMSummarizer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def summarize(self, report: ImpactReport, markdown: str) -> str:
        prompt = f"IMPACT REPORT JSON:\n{report}\n\nCURRENT MARKDOWN:\n{markdown}"
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return resp.choices[0].message.content
```

---

### Step 4.2 — Validator + fallback
File: `src/llm/validator.py`

```python
from src.domain.models import ImpactReport

class SummaryValidator:
    def validate(self, report: ImpactReport, summary: str) -> bool:
        for record in report.records:
            if record.asset_name not in summary:
                return False
            if record.severity.value not in summary:
                return False
        return True
```

Usage in main.py:
```python
if os.getenv("ENABLE_LLM_SUMMARY") == "true":
    try:
        raw = LLMSummarizer().summarize(report, markdown)
        if SummaryValidator().validate(report, raw):
            markdown = raw
        else:
            logging.warning("LLM summary failed validation, using deterministic renderer")
    except Exception as e:
        logging.warning(f"LLM summarizer failed: {e}, using deterministic renderer")
```

**Test gate:** Invalid LLM output triggers fallback. OpenAI failure triggers fallback.

---

## Full End-to-End Flow Summary

```
GitHub PR opened/updated
      ↓
GitHub Action triggers (schema file path filter)
      ↓
main.py --mode sandbox --pr-number X --repo owner/repo --output github
      ↓
Fetch changed files from GitHub API
      ↓
DiffParser.parse(changed_files) → list[SchemaChange]
      ↓
For each SchemaChange:
  OpenMetadataProvider.resolve_asset(entity) → Asset
  OpenMetadataProvider.get_downstream_lineage(asset_id, depth) → LineageGraph
      ↓
LineageTraverser.traverse(root, graph, depth) → [(Asset, path)]
      ↓
ImpactRulesEngine.evaluate(change, asset, path, column_map) → ImpactRecord
      ↓
ReportBuilder.build(changes, records) → ImpactReport
      ↓
PRCommentRenderer.render(report) → markdown
      ↓
[Optional] LLMSummarizer.summarize(report, markdown) → improved markdown
SummaryValidator.validate(report, summary) → fallback if invalid
      ↓
GitHubAdapter.post_or_update_comment(pr_number, markdown)
      ↓
PR comment created or updated
```

---

## Phase-by-Phase Definition of Done

| Phase | Done when |
|-------|-----------|
| Phase 1 | All 5 fixture e2e tests pass; CLI runs with `--mode mock` |
| Phase 2 | Sandbox smoke test returns 200; entity resolves; engine runs with live provider |
| Phase 3 | PR comment posted to a real PR; action triggers correctly on schema file changes |
| Phase 4 | LLM improves markdown; fallback works on failure or invalid output |

---

## Hard Rules

- Never call OpenMetadata APIs from inside `engine/`
- Never hardcode credentials
- Never commit `.env`
- LLM never decides severity, confidence, or asset identity
- MCP is not used in this path — REST is the only transport
- If sandbox is unavailable, fall back to `--mode mock` for testing
