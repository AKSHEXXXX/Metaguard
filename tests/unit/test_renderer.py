from __future__ import annotations

from datetime import datetime, timezone

from src.domain.enums import AssetType, ChangeType, Confidence, Severity
from src.domain.models import ImpactRecord, ImpactReport, SchemaChange
from src.engine.renderer import PRCommentRenderer


def test_renderer_contains_asset_names_and_critical() -> None:
    report = ImpactReport(
        id="F1",
        highest_severity=Severity.CRITICAL,
        total_affected=1,
        records=[
            ImpactRecord(
                asset_id="t2",
                asset_name="stg_customers",
                asset_type=AssetType.TABLE,
                severity=Severity.CRITICAL,
                confidence=Confidence.HIGH,
                reason="x",
                path=["analytics.customers.customer_id", "stg_customers.customer_id"],
            )
        ],
        generated_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )

    md = PRCommentRenderer.render(report)
    assert "stg_customers" in md
    assert "CRITICAL" in md


def test_renderer_polished_title_format() -> None:
    """Phase 2: verify the concise title format."""
    report = ImpactReport(
        id="test",
        highest_severity=Severity.HIGH,
        total_affected=2,
        records=[
            ImpactRecord(
                asset_id="a1", asset_name="asset_one", asset_type=AssetType.TABLE,
                severity=Severity.HIGH, confidence=Confidence.MEDIUM,
                reason="x", path=["root", "asset_one"],
            ),
            ImpactRecord(
                asset_id="a2", asset_name="asset_two", asset_type=AssetType.VIEW,
                severity=Severity.MEDIUM, confidence=Confidence.HIGH,
                reason="y", path=["root", "mid", "asset_two"],
            ),
        ],
        generated_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )
    md = PRCommentRenderer.render(report)
    assert "**MetaGuard**" in md
    assert "high-impact" in md
    assert "**2** downstream assets" in md
    assert "Suggested follow-up" in md
    assert "Why this changed" in md


def test_renderer_change_details_section() -> None:
    """Phase 2: verify 'Changes detected' section when changes are provided."""
    report = ImpactReport(
        id="test",
        highest_severity=Severity.HIGH,
        total_affected=1,
        records=[
            ImpactRecord(
                asset_id="a1", asset_name="downstream_tbl", asset_type=AssetType.TABLE,
                severity=Severity.HIGH, confidence=Confidence.MEDIUM,
                reason="x", path=["fact_orders", "downstream_tbl"],
            ),
        ],
        generated_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )
    changes = [
        SchemaChange(entity="fact_orders", change_type=ChangeType.DROP_COLUMN, column="legacy_id"),
        SchemaChange(entity="fact_orders", change_type=ChangeType.ADD_COLUMN, column="created_at"),
    ]
    md = PRCommentRenderer.render(report, changes=changes)
    assert "Changes detected" in md
    assert "dropped column" in md
    assert "added column" in md
    assert "`legacy_id`" in md
    assert "`created_at`" in md


def test_renderer_no_owner_column_when_absent() -> None:
    """The Owner column should only appear when at least one record has an owner."""
    report = ImpactReport(
        id="test",
        highest_severity=Severity.LOW,
        total_affected=1,
        records=[
            ImpactRecord(
                asset_id="a1", asset_name="tbl", asset_type=AssetType.TABLE,
                severity=Severity.LOW, confidence=Confidence.HIGH,
                reason="safe", path=["root", "tbl"],
            ),
        ],
        generated_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )
    md = PRCommentRenderer.render(report)
    assert "Owner" not in md


def test_renderer_owner_column_when_present() -> None:
    """The Owner column should appear when a record has an owner."""
    report = ImpactReport(
        id="test",
        highest_severity=Severity.HIGH,
        total_affected=1,
        records=[
            ImpactRecord(
                asset_id="a1", asset_name="tbl", asset_type=AssetType.TABLE,
                severity=Severity.HIGH, confidence=Confidence.HIGH,
                reason="x", path=["root", "tbl"], owner="alice",
            ),
        ],
        generated_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )
    md = PRCommentRenderer.render(report)
    assert "Owner" in md
    assert "alice" in md
