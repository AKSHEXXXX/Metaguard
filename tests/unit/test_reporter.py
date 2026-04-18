from __future__ import annotations

from datetime import datetime, timezone

from src.domain.enums import AssetType, ChangeType, Confidence, Severity
from src.domain.models import ImpactRecord, ImpactReport, SchemaChange
from src.engine.reporter import ReportBuilder


def test_report_builder_highest_severity_and_counts() -> None:
    changes = [SchemaChange(entity="t", change_type=ChangeType.DROP_COLUMN, column="c")]
    records = [
        ImpactRecord(
            asset_id="a1",
            asset_name="one",
            asset_type=AssetType.TABLE,
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            reason="x",
            path=["t"],
        ),
        ImpactRecord(
            asset_id="a2",
            asset_name="two",
            asset_type=AssetType.TABLE,
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            reason="x",
            path=["t"],
        ),
        ImpactRecord(
            asset_id="a3",
            asset_name="three",
            asset_type=AssetType.TABLE,
            severity=Severity.LOW,
            confidence=Confidence.HIGH,
            reason="x",
            path=["t"],
        ),
    ]

    report = ReportBuilder.build(report_id="X", changes=changes, records=records)
    assert isinstance(report, ImpactReport)
    assert report.highest_severity is Severity.CRITICAL
    assert report.total_affected == 3
    assert isinstance(report.generated_at, datetime)
    assert report.generated_at.tzinfo is timezone.utc
