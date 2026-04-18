from __future__ import annotations

from src.domain.enums import ChangeType, Confidence
from src.domain.models import SchemaChange
from src.providers.mock_provider import MockMetadataProvider
from src.providers.resolver import AssetResolver


def test_known_asset_resolves_with_high_confidence() -> None:
    provider = MockMetadataProvider("F1")
    change = SchemaChange(entity="analytics.customers", change_type=ChangeType.DROP_COLUMN, column="customer_id")
    asset, confidence = AssetResolver.resolve(change, provider)
    assert asset is not None
    assert asset.id == "t1"
    assert confidence is Confidence.HIGH


def test_unknown_asset_returns_low_confidence() -> None:
    provider = MockMetadataProvider("F1")
    change = SchemaChange(entity="unknown.table", change_type=ChangeType.DROP_COLUMN, column="x")
    asset, confidence = AssetResolver.resolve(change, provider)
    assert asset is None
    assert confidence is Confidence.LOW
