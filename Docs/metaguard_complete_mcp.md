# METAGUARD_COMPLETE_MCP.md
## MetaGuard — Complete Build Guide (MCP Path)

This guide is identical to the REST path for Phases 1, 3, and 4.
Phase 2 is where this path diverges: instead of calling OpenMetadata REST endpoints directly,
the analyzer uses the OpenMetadata MCP server as the metadata interface.

Use this guide only if:
- `https://sandbox.open-metadata.org/mcp` responds with 200 (not 405)
- You have confirmed the MCP endpoint accepts SSE connections with Bearer auth
- If you get a 405 on the MCP endpoint, switch to METAGUARD_COMPLETE_REST.md immediately

---

## Stack

- Language: Python
- OpenMetadata: MCP server at `https://sandbox.open-metadata.org/mcp`
- Auth: PAT via `Authorization: Bearer $OPENMETADATA_TOKEN`
- GitHub: PR events via GitHub Actions + GitHub REST API
- LLM: OpenAI `gpt-4o-mini` + MCP tool calls for metadata context

---

## Environment Variables

```env
OPENMETADATA_HOST=https://sandbox.open-metadata.org
OPENMETADATA_TOKEN=your_pat_here
OPENMETADATA_MCP_URL=https://sandbox.open-metadata.org/mcp
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini
GITHUB_TOKEN=your_github_token_here
APP_ENV=dev
LOG_LEVEL=INFO
LINEAGE_MAX_DEPTH=5
HTTP_TIMEOUT_SECONDS=30
ENABLE_LLM_SUMMARY=true
ENABLE_GITHUB_COMMENT=true
MCP_ENABLED=true
```

---

## How MCP Fits Into This Project

OpenMetadata embeds an MCP server that exposes metadata as AI-callable tools.
Instead of calling `GET /api/v1/tables` directly, the MCP client sends a tool-call JSON payload
over SSE to the MCP endpoint, and the server returns structured metadata.

In MetaGuard, MCP is used only in Phase 2 as the provider transport.
The core engine still receives the same `Asset` and `LineageGraph` domain models.
The MCP path does not change `engine/traverser.py`, `engine/rules.py`, or `engine/reporter.py`.

---

## Phases 1, 3, 4

These are identical to METAGUARD_COMPLETE_REST.md.
Follow the same steps for:
- Phase 1: Core engine, fixtures, mock provider, traversal, rules, reporter, renderer
- Phase 3: GitHub Action, GitHubAdapter, CLI
- Phase 4: LLM summarizer, validator, fallback

This file only documents the Phase 2 difference.

---

## PHASE 2 — OpenMetadata MCP Integration

### Goal
Build `MCPMetadataProvider` that calls the OpenMetadata MCP server via SSE tool calls.
The provider must satisfy the same `MetadataProvider` interface as `MockMetadataProvider`.
The engine stays completely unchanged.

---

### Step 2.0 — Verify MCP endpoint is live

Before writing any code, run this:

```bash
curl -v -H "Authorization: Bearer $OPENMETADATA_TOKEN" \
     -H "Accept: text/event-stream" \
     "$OPENMETADATA_MCP_URL"
```

Expected: an SSE connection opens and does not return 405 or 404.
If 405 is returned: stop and use METAGUARD_COMPLETE_REST.md.
If 200/101 is returned: continue.

---

### Step 2.1 — MCP client
File: `src/adapters/mcp_client.py`

The OpenMetadata MCP server exposes tool calls over SSE.
The client must:
- Open SSE connection to `$OPENMETADATA_MCP_URL`
- Send JWT bearer token in headers
- Send JSON-RPC-style tool call payloads
- Parse SSE events for tool responses

```python
import json
import requests
from sseclient import SSEClient

class MCPClient:
    def __init__(self, mcp_url: str, token: str, timeout: int = 30):
        self.mcp_url = mcp_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        self.timeout = timeout

    def call_tool(self, tool_name: str, params: dict) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": params},
            "id": 1,
        }
        resp = requests.post(self.mcp_url, headers=self.headers,
                             json=payload, stream=True, timeout=self.timeout)
        if resp.status_code == 405:
            raise MCPTransportError("MCP returned 405 — use REST fallback")
        resp.raise_for_status()
        for event in SSEClient(resp).events():
            if event.data:
                return json.loads(event.data)
        raise MCPTransportError("No response from MCP server")

class MCPTransportError(Exception):
    pass
```

Requirements addition:
```
sseclient-py
```

**Test gate:**
- Mock SSE stream; assert tool call payload is correctly formed
- Assert `MCPTransportError` raised on 405

---

### Step 2.2 — Discover available MCP tools

Once the SSE connection works, list available tools:

```python
def list_tools(self) -> list[str]:
    payload = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}
    resp = requests.post(self.mcp_url, headers=self.headers,
                         json=payload, stream=True, timeout=self.timeout)
    resp.raise_for_status()
    for event in SSEClient(resp).events():
        if event.data:
            data = json.loads(event.data)
            return [t["name"] for t in data.get("result", {}).get("tools", [])]
    return []
```

Run `list_tools()` once in smoke test to confirm what the sandbox MCP server exposes.
Common expected tool names: `search_entities`, `get_lineage`, `get_entity`, `list_tables`.

**Test gate:** Print tool list during smoke test; confirm at least one metadata tool exists.

---

### Step 2.3 — MCPMetadataProvider
File: `src/providers/mcp_provider.py`

```python
from src.adapters.mcp_client import MCPClient, MCPTransportError
from src.providers.openmetadata_provider import OpenMetadataProvider
from src.domain.models import Asset, LineageGraph
from src.domain.enums import AssetType

class MCPMetadataProvider:
    """
    Uses MCP for asset resolution and lineage fetching.
    Falls back to OpenMetadataProvider (REST) if MCP returns transport error.
    """
    def __init__(self, mcp_client: MCPClient, rest_fallback: OpenMetadataProvider):
        self.mcp = mcp_client
        self.fallback = rest_fallback

    def resolve_asset(self, entity_ref: str) -> Asset:
        try:
            result = self.mcp.call_tool("get_entity", {"fqn": entity_ref, "type": "table"})
            return self._map_asset(result.get("result", {}))
        except MCPTransportError:
            return self.fallback.resolve_asset(entity_ref)

    def get_downstream_lineage(self, asset_id: str, depth: int) -> LineageGraph:
        try:
            result = self.mcp.call_tool("get_lineage", {
                "fqn": asset_id,
                "type": "table",
                "upstreamDepth": 0,
                "downstreamDepth": depth,
            })
            return self._map_lineage(result.get("result", {}))
        except MCPTransportError:
            return self.fallback.get_downstream_lineage(asset_id, depth)

    def _map_asset(self, data: dict) -> Asset:
        return Asset(
            id=data.get("fullyQualifiedName", ""),
            name=data.get("name", ""),
            asset_type=AssetType.TABLE,
            owner=data.get("owner", {}).get("name") if data.get("owner") else None,
        )

    def _map_lineage(self, data: dict) -> LineageGraph:
        from src.providers.openmetadata_provider import OpenMetadataProvider
        provider = self.fallback
        return provider._map_lineage(data)
```

Key design decision: `MCPMetadataProvider` always has a REST fallback.
If MCP fails for any reason, it does not crash the pipeline.

**Test gate:**
- Mock MCP call succeeds → `Asset` returned from MCP result
- Mock MCP raises `MCPTransportError` → fallback `resolve_asset` called
- Lineage: same fallback pattern

---

### Step 2.4 — Smoke test (MCP)
File: `smoke_test_mcp.py`

```python
from dotenv import load_dotenv
load_dotenv()
import os
from src.adapters.mcp_client import MCPClient, MCPTransportError
from src.providers.openmetadata_provider import OpenMetadataProvider
from src.providers.mcp_provider import MCPMetadataProvider
from src.config import load_config

config = load_config()
mcp_url = os.getenv("OPENMETADATA_MCP_URL")

mcp_client = MCPClient(mcp_url=mcp_url, token=config.om_token, timeout=config.http_timeout)
rest_provider = OpenMetadataProvider(config.om_host, config.om_token, config.http_timeout)
provider = MCPMetadataProvider(mcp_client, rest_provider)

# Step 1: list tools
try:
    tools = mcp_client.list_tools()
    print("MCP tools available:", tools)
except MCPTransportError as e:
    print("MCP not available:", e)
    print("Falling back to REST provider")
    provider = rest_provider

# Step 2: resolve one entity
try:
    asset = provider.resolve_asset("sample_table_fqn")
    print("Resolved:", asset.name)
    lineage = provider.get_downstream_lineage(asset.id, depth=3)
    print("Downstream nodes:", len(lineage.nodes))
except Exception as e:
    print("Error:", e)
```

Run:
```bash
python smoke_test_mcp.py
```

**Pass criteria:**
- MCP tools list is non-empty, OR MCP returns 405 and REST fallback is used
- At least one entity resolves without crash
- Lineage graph returned

---

### Step 2.5 — Wire MCP into CLI
File: `main.py`

Add `--transport mcp` option:
```python
@click.option('--transport', default='rest', type=click.Choice(['rest', 'mcp']))
```

When `--transport mcp`:
```python
mcp_url = os.getenv("OPENMETADATA_MCP_URL")
if not mcp_url:
    raise ValueError("OPENMETADATA_MCP_URL required for MCP transport")
mcp_client = MCPClient(mcp_url, config.om_token)
rest_provider = OpenMetadataProvider(config.om_host, config.om_token)
provider = MCPMetadataProvider(mcp_client, rest_provider)
```

---

## LLM + MCP Together (Phase 4 Enhancement)

When MCP is working, you can use it to provide richer context to the LLM summarizer.
Instead of passing only the structured `ImpactReport`, you can optionally attach:
- Asset descriptions from MCP tool calls
- Owner information from MCP
- Domain/tier metadata from MCP

This makes the LLM summary more contextually rich without changing the deterministic impact facts.

Enhancement to LLM prompt when MCP context is available:
```python
if mcp_context:
    prompt += f"\nADDITIONAL ASSET CONTEXT FROM OPENMETADATA:\n{mcp_context}"
```

This is optional and does not affect the validation layer — the validator still checks
that no new facts are invented that are not in the `ImpactReport`.

---

## Full End-to-End Flow (MCP Path)

```
GitHub PR opened/updated
      ↓
GitHub Action triggers (schema file path filter)
      ↓
main.py --mode sandbox --transport mcp --pr-number X --repo owner/repo --output github
      ↓
Fetch changed files from GitHub API
      ↓
DiffParser.parse(changed_files) → list[SchemaChange]
      ↓
For each SchemaChange:
  MCPMetadataProvider.resolve_asset(entity)
    → tries MCP tool call "get_entity"
    → falls back to REST if 405
    → returns Asset
  MCPMetadataProvider.get_downstream_lineage(asset_id, depth)
    → tries MCP tool call "get_lineage"
    → falls back to REST if 405
    → returns LineageGraph
      ↓
LineageTraverser.traverse(root, graph, depth) → [(Asset, path)]
      ↓
ImpactRulesEngine.evaluate(change, asset, path, column_map) → ImpactRecord
      ↓
ReportBuilder.build(changes, records) → ImpactReport
      ↓
PRCommentRenderer.render(report) → markdown
      ↓
[Optional] LLMSummarizer.summarize(report, markdown, mcp_context) → improved markdown
SummaryValidator.validate(report, summary) → fallback if invalid
      ↓
GitHubAdapter.post_or_update_comment(pr_number, markdown)
      ↓
PR comment created or updated
```

---

## Phase 2 Definition of Done (MCP Path)

- [ ] `MCPClient` handles SSE tool calls and raises `MCPTransportError` on 405
- [ ] `MCPMetadataProvider` implements `MetadataProvider` interface
- [ ] Fallback to REST provider works automatically on `MCPTransportError`
- [ ] Smoke test prints available MCP tools OR graceful fallback message
- [ ] Entity resolves via MCP or REST
- [ ] Lineage graph returned via MCP or REST
- [ ] Zero changes to `engine/` code
- [ ] CLI accepts `--transport mcp` flag

---

## Hard Rules

- Never call OpenMetadata inside `engine/`
- Never hardcode credentials
- MCP fallback to REST must be automatic — do not crash on 405
- LLM never decides severity, confidence, or asset identity
- Engine is deterministic regardless of MCP or REST transport
