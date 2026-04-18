from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.models import Asset, LineageGraph


@runtime_checkable
class MetadataProvider(Protocol):
    def resolve_asset(self, ref: str) -> Asset:
        """Resolve an asset reference (id or name) to an Asset."""

    def get_downstream_lineage(self, root_asset_id: str) -> LineageGraph:
        """Return downstream lineage graph rooted at the given asset id."""


class AssetNotFoundError(LookupError):
    def __init__(self, ref: str) -> None:
        super().__init__(f"Asset not found: {ref}")
        self.ref = ref
