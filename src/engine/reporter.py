from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from src.domain.enums import Severity
from src.domain.models import ImpactRecord, ImpactReport, SchemaChange


@dataclass(frozen=True)
class ReportBuilder:
    @staticmethod
    def build(report_id: str, changes: list[SchemaChange], records: list[ImpactRecord]) -> ImpactReport:
        highest = Severity.LOW
        if records:
            # Severity is ordered LOW < MEDIUM < HIGH < CRITICAL.
            order = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.CRITICAL: 3}
            highest = max((r.severity for r in records), key=lambda s: order[s])

        return ImpactReport(
            id=report_id,
            highest_severity=highest,
            total_affected=len(records),
            records=records,
            # Keep deterministic-ish by pinning timezone; tests should not assert exact timestamp.
            generated_at=datetime.now(timezone.utc),
        )
