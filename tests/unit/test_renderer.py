from __future__ import annotations

from datetime import datetime, timezone

from src.domain.enums import AssetType, Confidence, Severity
from src.domain.models import ImpactRecord, ImpactReport
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
