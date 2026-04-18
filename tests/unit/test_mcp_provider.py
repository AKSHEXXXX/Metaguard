from __future__ import annotations

from src.adapters.mcp_client import MCPTransportError
from src.domain.enums import AssetType
from src.domain.models import Asset, LineageEdge, LineageGraph
from src.providers.mcp_provider import MCPMetadataProvider


class _FakeMCPClient:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.calls: list[tuple[str, dict[str, object]]] = []

    def call_tool(self, name: str, params: dict[str, object]) -> dict[str, object]:
        self.calls.append((name, params))
        if self.mode == "transport_error":
            raise MCPTransportError("MCP returned 405 — use REST fallback")
        if name == "get_entity":
            return {"result": {"id": "t1", "name": "orders", "owner": {"name": "data_eng"}}}
        return {
            "result": {
                "nodes": [
                    {"id": "t1", "name": "orders", "type": "TABLE"},
                    {"id": "d1", "name": "Orders Dashboard", "type": "DASHBOARD"},
                ],
                "edges": [{"from_id": "t1", "to_id": "d1", "column_map": None}],
            }
        }


class _FakeRESTProvider:
    def resolve_asset(self, ref: str) -> Asset:
        return Asset(id="rest-id", name=ref, type=AssetType.TABLE, owner="rest_owner")

    def get_downstream_lineage(self, root_asset_id: str, depth: int = 5) -> LineageGraph:
        return LineageGraph(
            nodes={"rest-id": Asset(id="rest-id", name=root_asset_id, type=AssetType.TABLE)},
            edges=[LineageEdge(from_id="rest-id", to_id="x1", column_map=None)],
        )


def test_mcp_provider_uses_mcp_when_available() -> None:
    provider = MCPMetadataProvider(_FakeMCPClient("ok"), _FakeRESTProvider())
    asset = provider.resolve_asset("svc.db.orders")
    lineage = provider.get_downstream_lineage(asset.id)

    assert asset.id == "t1"
    assert asset.owner == "data_eng"
    assert "d1" in lineage.nodes
    assert lineage.edges[0].from_id == "t1"


def test_mcp_provider_falls_back_to_rest_on_transport_error() -> None:
    provider = MCPMetadataProvider(_FakeMCPClient("transport_error"), _FakeRESTProvider())

    asset = provider.resolve_asset("svc.db.orders")
    lineage = provider.get_downstream_lineage("svc.db.orders")

    assert asset.id == "rest-id"
    assert lineage.edges[0].from_id == "rest-id"
