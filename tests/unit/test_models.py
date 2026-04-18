from __future__ import annotations

from datetime import datetime

from src.domain.enums import AssetType, ChangeType, Confidence, Severity
from src.domain.models import (
    Asset,
    ImpactRecord,
    ImpactReport,
    LineageEdge,
    LineageGraph,
    SchemaChange,
)


def test_enums_have_expected_values() -> None:
    assert ChangeType.DROP_COLUMN.value == "DROP_COLUMN"
    assert Severity.CRITICAL.value == "CRITICAL"
    assert Confidence.HIGH.value == "HIGH"
    assert AssetType.DASHBOARD.value == "DASHBOARD"


def test_models_instantiate_and_types_are_correct() -> None:
    change = SchemaChange(
        entity="analytics.customers",
        change_type=ChangeType.DROP_COLUMN,
        column="customer_id",
        source_file="migrations/x.sql",
    )
    assert isinstance(change.entity, str)
    assert change.change_type is ChangeType.DROP_COLUMN

    asset = Asset(id="t1", name="analytics.customers", type=AssetType.TABLE, owner="data_eng")
    assert asset.type is AssetType.TABLE

    edge = LineageEdge(from_id="t1", to_id="t2", column_map=[{"from": "customer_id", "to": "customer_id"}])
    graph = LineageGraph(nodes={"t1": asset}, edges=[edge])
    assert graph.edges[0].to_id == "t2"

    record = ImpactRecord(
        asset_id="t2",
        asset_name="stg_customers",
        asset_type=AssetType.TABLE,
        severity=Severity.CRITICAL,
        confidence=Confidence.HIGH,
        reason="x",
        path=["a", "b"],
    )
    report = ImpactReport(
        id="F1",
        highest_severity=Severity.CRITICAL,
        total_affected=1,
        records=[record],
        generated_at=datetime(2026, 4, 17, 0, 0, 0),
    )
    assert report.total_affected == 1
