from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest
from src.adapters.mcp_client import MCPClient, MCPTransportError
from src.domain.enums import AssetType
from src.domain.models import Asset, LineageEdge, LineageGraph


def test_query_lineage_parses_sse_stream_into_lineage_graph() -> None:
    payload = {
        "nodes": [
            {"id": "A", "name": "db.schema.A", "type": "TABLE"},
            {"id": "B", "name": "db.schema.B", "type": "VIEW"},
        ],
        "edges": [
            {"from_id": "A", "to_id": "B"},
        ],
    }

    sse_text = (
        "event: lineage\n"
        f"data: {json.dumps(payload)}\n"
        "\n"
        "event: done\n"
        "data: [DONE]\n"
        "\n"
    )

    chunks = [
        sse_text[:10].encode("utf-8"),
        sse_text[10:27].encode("utf-8"),
        sse_text[27:63].encode("utf-8"),
        sse_text[63:].encode("utf-8"),
    ]

    def fake_stream_provider(url: str, headers: dict[str, str], params: dict[str, str]):
        assert url.startswith("http://mcp.test/lineage?")
        assert headers["Accept"] == "text/event-stream"
        assert params == {"asset_id": "A", "depth": "2"}
        yield from chunks

    client = MCPClient("http://mcp.test", jwt_token="token", stream_provider=fake_stream_provider)
    graph = client.query_lineage(asset_id="A", depth=2)

    expected = LineageGraph(
        nodes={
            "A": Asset(id="A", name="db.schema.A", type=AssetType.TABLE),
            "B": Asset(id="B", name="db.schema.B", type=AssetType.VIEW),
        },
        edges=[LineageEdge(from_id="A", to_id="B", column_map=None)],
    )

    assert graph == expected


def test_call_tool_builds_expected_rpc_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _Resp:
        def __init__(self) -> None:
            self._chunks = [
                b'event: message\n',
                b'data: {"result": {"ok": true}}\n\n',
            ]
            self._idx = 0

        def read(self, _n: int) -> bytes:
            if self._idx >= len(self._chunks):
                return b""
            chunk = self._chunks[self._idx]
            self._idx += 1
            return chunk

        def __enter__(self) -> "_Resp":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    def fake_urlopen(req, timeout=None):  # noqa: ANN001,ARG001
        captured["url"] = req.full_url
        captured["method"] = req.method
        captured["body"] = json.loads(req.data.decode("utf-8")) if req.data else {}
        captured["auth"] = req.headers.get("Authorization")
        return _Resp()

    monkeypatch.setattr("src.adapters.mcp_client.urllib.request.urlopen", fake_urlopen)

    client = MCPClient("https://sandbox.open-metadata.org/mcp", jwt_token="token")
    result = client.call_tool("get_entity", {"fqn": "db.schema.table"})

    assert captured["url"] == "https://sandbox.open-metadata.org/mcp"
    assert captured["method"] == "POST"
    assert captured["auth"] == "Bearer token"
    assert captured["body"] == {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": "get_entity", "arguments": {"fqn": "db.schema.table"}},
        "id": 1,
    }
    assert result == {"result": {"ok": True}}


def test_call_tool_raises_transport_error_on_405(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout=None):  # noqa: ANN001,ARG001
        raise HTTPError(url=req.full_url, code=405, msg="Method Not Allowed", hdrs=None, fp=None)

    monkeypatch.setattr("src.adapters.mcp_client.urllib.request.urlopen", fake_urlopen)

    client = MCPClient("https://sandbox.open-metadata.org/mcp", jwt_token="token")
    with pytest.raises(MCPTransportError) as exc_info:
        client.call_tool("get_lineage", {"fqn": "x"})
    assert "405" in str(exc_info.value)

