from __future__ import annotations

from src.domain.enums import AssetType
from src.domain.models import Asset, LineageGraph
from src.providers.base import MetadataProvider


def test_stub_satisfies_metadata_provider_protocol() -> None:
    class StubProvider:
        def resolve_asset(self, ref: str) -> Asset:
            return Asset(id=ref, name=ref, type=AssetType.TABLE)

        def get_downstream_lineage(self, root_asset_id: str) -> LineageGraph:
            asset = Asset(id=root_asset_id, name=root_asset_id, type=AssetType.TABLE)
            return LineageGraph(nodes={root_asset_id: asset}, edges=[])

    stub = StubProvider()
    assert isinstance(stub, MetadataProvider)
