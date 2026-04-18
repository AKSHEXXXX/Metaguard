from __future__ import annotations

import json
from pathlib import Path

from src.domain.enums import AssetType
from src.domain.models import Asset, LineageEdge, LineageGraph
from src.providers.base import AssetNotFoundError, MetadataProvider


class MockMetadataProvider(MetadataProvider):
    def __init__(self, fixture_id: str) -> None:
        self.fixture_id = fixture_id
        self._graph = self._load_lineage_fixture(fixture_id)

    def resolve_asset(self, ref: str) -> Asset:
        if ref in self._graph.nodes:
            return self._graph.nodes[ref]
        for asset in self._graph.nodes.values():
            if asset.name == ref:
                return asset
        raise AssetNotFoundError(ref)

    def get_downstream_lineage(self, root_asset_id: str) -> LineageGraph:
        # For Phase 1 fixtures, the lineage file already encodes the full downstream graph.
        # Engine components can choose to traverse starting from `root_asset_id`.
        return self._graph

    @staticmethod
    def _load_lineage_fixture(fixture_id: str) -> LineageGraph:
        fixture_path = (
            Path(__file__).resolve().parents[2]
            / "tests"
            / "fixtures"
            / "lineage"
            / f"{fixture_id}_lineage.json"
        )
        payload = json.loads(fixture_path.read_text())

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
