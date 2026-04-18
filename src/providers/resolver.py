from __future__ import annotations

from src.domain.enums import Confidence
from src.domain.models import Asset, SchemaChange
from src.providers.base import AssetNotFoundError, MetadataProvider


class AssetResolver:
    @staticmethod
    def resolve(change: SchemaChange, provider: MetadataProvider) -> tuple[Asset | None, Confidence]:
        try:
            asset = provider.resolve_asset(change.entity)
            return asset, Confidence.HIGH
        except AssetNotFoundError:
            return None, Confidence.LOW
