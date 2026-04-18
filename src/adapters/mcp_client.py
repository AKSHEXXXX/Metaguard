from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from urllib.error import HTTPError
from typing import Callable, Iterable, Iterator, Optional

from src.domain.enums import AssetType
from src.domain.models import Asset, LineageEdge, LineageGraph


@dataclass(frozen=True)
class SSEEvent:
    event: str | None
    data: str
    id: str | None = None
    retry: int | None = None


class MCPTransportError(RuntimeError):
    pass


def iter_sse_events(byte_chunks: Iterable[bytes]) -> Iterator[SSEEvent]:
    """
    Minimal SSE parser.

    - Accepts arbitrary byte chunks (not necessarily line-aligned).
    - Emits an event when a blank line is encountered.
    - Supports 'event:', 'data:', 'id:', 'retry:' fields.
    - Ignores unknown fields and comment lines starting with ':'.
    """

    buf = b""

    event_name: str | None = None
    data_lines: list[str] = []
    event_id: str | None = None
    retry: int | None = None

    def emit_if_ready() -> Optional[SSEEvent]:
        nonlocal event_name, data_lines, event_id, retry
        if not data_lines and event_name is None and event_id is None and retry is None:
            return None
        data = "\n".join(data_lines)
        ev = SSEEvent(event=event_name, data=data, id=event_id, retry=retry)
        event_name = None
        data_lines = []
        event_id = None
        retry = None
        return ev

    for chunk in byte_chunks:
        if not chunk:
            continue
        buf += chunk
        while True:
            nl = buf.find(b"\n")
            if nl == -1:
                break
            raw_line = buf[:nl]
            buf = buf[nl + 1 :]

            # Strip CR from CRLF.
            if raw_line.endswith(b"\r"):
                raw_line = raw_line[:-1]

            line = raw_line.decode("utf-8", errors="replace")

            if line == "":
                ev = emit_if_ready()
                if ev is not None:
                    yield ev
                continue

            if line.startswith(":"):
                continue

            field, sep, value = line.partition(":")
            if sep == "":
                continue
            if value.startswith(" "):
                value = value[1:]

            if field == "event":
                event_name = value
            elif field == "data":
                data_lines.append(value)
            elif field == "id":
                event_id = value
            elif field == "retry":
                try:
                    retry = int(value)
                except ValueError:
                    retry = None

    # EOF flush: SSE spec doesn't require trailing blank line, but streams often end that way.
    if buf:
        # If the last chunk doesn't end with '\n', treat remaining bytes as a final line.
        raw_line = buf[:-1] if buf.endswith(b"\r") else buf
        line = raw_line.decode("utf-8", errors="replace")
        if line.startswith("data:"):
            data_lines.append(line.partition(":")[2].lstrip(" "))
        elif line.startswith("event:"):
            event_name = line.partition(":")[2].lstrip(" ")
        elif line.startswith("id:"):
            event_id = line.partition(":")[2].lstrip(" ")
        elif line.startswith("retry:"):
            try:
                retry = int(line.partition(":")[2].lstrip(" "))
            except ValueError:
                retry = None

    ev = emit_if_ready()
    if ev is not None:
        yield ev


def _lineage_graph_from_payload(payload: dict) -> LineageGraph:
    nodes: dict[str, Asset] = {}
    for node in payload.get("nodes", []):
        asset = Asset(
            id=node["id"],
            name=node["name"],
            type=AssetType(node["type"]),
            owner=node.get("owner"),
            criticality=node.get("criticality"),
            domain=node.get("domain"),
        )
        nodes[asset.id] = asset

    edges: list[LineageEdge] = []
    for edge in payload.get("edges", []):
        edges.append(
            LineageEdge(
                from_id=edge["from_id"],
                to_id=edge["to_id"],
                column_map=edge.get("column_map"),
            )
        )

    return LineageGraph(nodes=nodes, edges=edges)


class MCPClient:
    def __init__(
        self,
        mcp_url: str,
        jwt_token: str | None = None,
        *,
        stream_provider: Callable[[str, dict[str, str], dict[str, str]], Iterable[bytes]] | None = None,
    ) -> None:
        self.mcp_url = mcp_url.rstrip("/")
        self.jwt_token = jwt_token
        self.timeout = 30
        self._stream_provider = stream_provider or self._default_stream_provider

    def call_tool(self, tool_name: str, params: dict[str, object]) -> dict[str, object]:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": params},
            "id": 1,
        }
        for ev in iter_sse_events(self._post_sse(payload)):
            if not ev.data.strip():
                continue
            try:
                parsed = json.loads(ev.data)
            except json.JSONDecodeError as exc:
                raise MCPTransportError("Invalid JSON in MCP SSE response") from exc
            if isinstance(parsed, dict):
                return parsed
            raise MCPTransportError("Unexpected MCP response shape")
        raise MCPTransportError("No response from MCP server")

    def list_tools(self) -> list[str]:
        payload = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}
        response = self.call_rpc(payload)
        result = response.get("result", {})
        if not isinstance(result, dict):
            return []
        tools = result.get("tools", [])
        if not isinstance(tools, list):
            return []
        names: list[str] = []
        for t in tools:
            if isinstance(t, dict):
                name = t.get("name")
                if isinstance(name, str):
                    names.append(name)
        return names

    def call_rpc(self, payload: dict[str, object]) -> dict[str, object]:
        for ev in iter_sse_events(self._post_sse(payload)):
            if not ev.data.strip():
                continue
            try:
                parsed = json.loads(ev.data)
            except json.JSONDecodeError as exc:
                raise MCPTransportError("Invalid JSON in MCP SSE response") from exc
            if isinstance(parsed, dict):
                return parsed
        raise MCPTransportError("No response from MCP server")

    def query_lineage(self, asset_id: str, depth: int) -> LineageGraph:
        """
        Query MCP for downstream lineage rooted at `asset_id` up to `depth`.

        Assumes MCP responds as Server-Sent Events (SSE) where one or more events
        contain JSON payloads with shape:
          { "nodes": [...], "edges": [...] }
        """
        params = {"asset_id": asset_id, "depth": str(depth)}
        url = f"{self.mcp_url}/lineage?{urllib.parse.urlencode(params)}"

        headers: dict[str, str] = {"Accept": "text/event-stream"}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        all_nodes: dict[str, Asset] = {}
        all_edges: list[LineageEdge] = []

        for ev in iter_sse_events(self._stream_provider(url, headers, params)):
            if ev.data.strip() in ("[DONE]", "") and (ev.event in ("done", "end") or ev.data.strip() == "[DONE]"):
                break

            try:
                payload = json.loads(ev.data)
            except json.JSONDecodeError:
                # Ignore non-JSON events (e.g., keepalives) in this minimal client.
                continue

            graph = _lineage_graph_from_payload(payload)
            all_nodes.update(graph.nodes)
            all_edges.extend(graph.edges)

        return LineageGraph(nodes=all_nodes, edges=all_edges)

    def _post_sse(self, payload: dict[str, object]) -> Iterable[bytes]:
        headers: dict[str, str] = {"Accept": "text/event-stream", "Content-Type": "application/json"}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.mcp_url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # nosec - runtime integration call
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    yield chunk
        except HTTPError as exc:
            if exc.code == 405:
                raise MCPTransportError("MCP returned 405 — use REST fallback") from exc
            raise MCPTransportError(f"MCP transport failed with status {exc.code}") from exc
        except Exception as exc:  # pragma: no cover - runtime transport guard
            raise MCPTransportError(f"MCP transport failed: {exc}") from exc

    @staticmethod
    def _default_stream_provider(url: str, headers: dict[str, str], _params: dict[str, str]) -> Iterable[bytes]:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:  # nosec - used only in non-test runtime wiring
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                yield chunk
