from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.enums import AssetType, ChangeType, Confidence, Severity


@dataclass(frozen=True)
class SchemaChange:
    entity: str
    change_type: ChangeType
    column: str | None = None
    old_type: str | None = None
    new_type: str | None = None
    source_file: str | None = None


@dataclass(frozen=True)
class Asset:
    id: str
    name: str
    type: AssetType
    owner: str | None = None
    criticality: str | None = None
    domain: str | None = None


@dataclass(frozen=True)
class LineageEdge:
    from_id: str
    to_id: str
    # Column-level lineage map, if available.
    # Each entry maps upstream column name -> downstream column name.
    column_map: list[dict[str, str]] | None = None


@dataclass(frozen=True)
class LineageGraph:
    nodes: dict[str, Asset]
    edges: list[LineageEdge]


@dataclass(frozen=True)
class ImpactRecord:
    asset_id: str
    asset_name: str
    asset_type: AssetType
    severity: Severity
    confidence: Confidence
    reason: str
    path: list[str]
    owner: str | None = None


@dataclass(frozen=True)
class ImpactReport:
    id: str
    highest_severity: Severity
    total_affected: int
    records: list[ImpactRecord]
    generated_at: datetime
