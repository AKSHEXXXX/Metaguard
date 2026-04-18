from __future__ import annotations

from typing import Any

from src.adapters.mcp_client import MCPClient, MCPTransportError
from src.domain.enums import AssetType
from src.domain.models import Asset, LineageEdge, LineageGraph
from src.providers.base import MetadataProvider
from src.providers.openmetadata_provider import OpenMetadataProvider


class MCPMetadataProvider(MetadataProvider):
    """
    MCP-first provider.
    Any MCP transport failure => silent REST fallback.
    """

    def __init__(self, mcp_client: MCPClient, rest_fallback: OpenMetadataProvider, depth: int = 5) -> None:
        self.mcp = mcp_client
        self.fallback = rest_fallback
        self.depth = depth

    def resolve_asset(self, ref: str) -> Asset:
        try:
            response = self.mcp.call_tool("get_entity", {"fqn": ref, "type": "table"})
            payload = self._extract_result(response)
            return self._map_asset(payload, default_ref=ref)
        except MCPTransportError:
            return self.fallback.resolve_asset(ref)

    def get_downstream_lineage(self, root_asset_id: str) -> LineageGraph:
        try:
            response = self.mcp.call_tool(
                "get_lineage",
                {"fqn": root_asset_id, "type": "table", "upstreamDepth": 0, "downstreamDepth": self.depth},
            )
            payload = self._extract_result(response)
            return self._map_lineage(payload)
        except MCPTransportError:
            return self.fallback.get_downstream_lineage(root_asset_id, depth=self.depth)

    @staticmethod
    def _extract_result(response: dict[str, object]) -> dict[str, Any]:
        result = response.get("result", {})
        if isinstance(result, dict):
            return result
        return {}

    @staticmethod
    def _map_asset(data: dict[str, Any], default_ref: str) -> Asset:
        owner = data.get("owner")
        owner_name = owner.get("name") if isinstance(owner, dict) else None
        return Asset(
            id=str(data.get("id") or data.get("fullyQualifiedName") or default_ref),
            name=str(data.get("name") or data.get("fullyQualifiedName") or default_ref),
            type=AssetType.TABLE,
            owner=owner_name,
            criticality=str(data.get("criticality")) if data.get("criticality") else None,
            domain=str(data.get("domain")) if data.get("domain") else None,
        )

    @staticmethod
    def _map_lineage(data: dict[str, Any]) -> LineageGraph:
        nodes: dict[str, Asset] = {}
        for node in data.get("nodes", []):
            if not isinstance(node, dict):
                continue
            node_id = node.get("id") or node.get("fullyQualifiedName")
            if not isinstance(node_id, str):
                continue
            nodes[node_id] = Asset(
                id=node_id,
                name=str(node.get("name") or node.get("fullyQualifiedName") or node_id),
                type=AssetType(str(node.get("type", "TABLE")).upper())
                if str(node.get("type", "TABLE")).upper() in {t.value for t in AssetType}
                else AssetType.TABLE,
                owner=None,
                criticality=None,
                domain=None,
            )

        edges: list[LineageEdge] = []
        raw_edges = data.get("edges", []) or data.get("downstreamEdges", [])
        for edge in raw_edges:
            if not isinstance(edge, dict):
                continue
            from_id = edge.get("from_id") or edge.get("fromEntity")
            to_id = edge.get("to_id") or edge.get("toEntity")
            if isinstance(from_id, dict):
                from_id = from_id.get("id")
            if isinstance(to_id, dict):
                to_id = to_id.get("id")
            if isinstance(from_id, str) and isinstance(to_id, str):
                edges.append(LineageEdge(from_id=from_id, to_id=to_id, column_map=edge.get("column_map")))

        return LineageGraph(nodes=nodes, edges=edges)
