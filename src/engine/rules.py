from __future__ import annotations

from dataclasses import dataclass

from src.domain.enums import AssetType, ChangeType, Confidence, Severity
from src.domain.models import Asset, ImpactRecord, SchemaChange


def _column_map_references(column_map: list[dict[str, str]] | None, column: str | None) -> bool:
    if not column_map or not column:
        return False
    for entry in column_map:
        if entry.get("from") == column or entry.get("to") == column:
            return True
    return False


def _column_map_has_alias(column_map: list[dict[str, str]] | None, old: str | None, new: str | None) -> bool:
    if not column_map or not old or not new:
        return False
    for entry in column_map:
        f = entry.get("from")
        t = entry.get("to")
        if (f == old and t == new) or (f == new and t == old):
            return True
    return False


def _normalize_type(t: str | None) -> str:
    return (t or "").strip().upper()


def _varchar_len(t: str) -> int | None:
    # VARCHAR(255) -> 255
    if not t.startswith("VARCHAR"):
        return None
    if "(" not in t or ")" not in t:
        return None
    inside = t.split("(", 1)[1].split(")", 1)[0].strip()
    try:
        return int(inside)
    except ValueError:
        return None


def _type_change_compatible(old_t: str | None, new_t: str | None) -> bool:
    old_n = _normalize_type(old_t)
    new_n = _normalize_type(new_t)

    if old_n == "INT" and new_n == "BIGINT":
        return True
    if old_n == "FLOAT" and new_n == "DOUBLE":
        return True

    old_v = _varchar_len(old_n)
    new_v = _varchar_len(new_n)
    if old_v is not None and new_v is not None and new_v > old_v:
        return True

    return False


def _type_change_incompatible(old_t: str | None, new_t: str | None) -> bool:
    old_n = _normalize_type(old_t)
    new_n = _normalize_type(new_t)

    if old_n.startswith("INT") and ("STRING" in new_n or "VARCHAR" in new_n):
        return True
    if ("STRING" in old_n or "VARCHAR" in old_n) and any(x in new_n for x in ("INT", "FLOAT", "BOOLEAN")):
        return True
    if old_n.startswith("DATE") and ("STRING" in new_n or "VARCHAR" in new_n):
        return True

    return False


def _compute_path(
    change: SchemaChange,
    path: list[str],
    asset: Asset,
    column_map: list[dict[str, str]] | None,
) -> list[str]:
    if not path:
        return []
    if not column_map or not change.column:
        return path

    upstream_col = change.column
    downstream_col = change.column
    if change.change_type is ChangeType.RENAME_COLUMN and change.new_type:
        downstream_col = change.new_type

    rendered: list[str] = []
    for i, name in enumerate(path):
        is_last = i == len(path) - 1
        if is_last and asset.type in {AssetType.DASHBOARD, AssetType.PIPELINE}:
            rendered.append(name)
        else:
            col = upstream_col if i == 0 else downstream_col
            rendered.append(f"{name}.{col}")
    return rendered


def _format_reason(change: SchemaChange, asset: Asset, path: list[str], column_map: list[dict[str, str]] | None) -> str:
    # Reasons are deterministic and derived only from the change + lineage path.
    root = path[0] if path else change.entity

    if change.change_type is ChangeType.DROP_COLUMN:
        if not path or len(path) < 2:
            return "No consumers detected"
        if column_map is None:
            if asset.type is AssetType.PIPELINE:
                return f"Pipeline depends on {root} but column-level lineage not available"
            if len(path) == 2:
                return (
                    f"Column-level lineage missing; table-level dependency on {root} is confirmed, but column usage is unknown"
                )
            return (
                f"Column-level lineage missing; table-level dependency confirmed through {path[-2]}, but column usage is unknown"
            )

        if len(path) == 2:
            return f"Downstream asset directly uses dropped column {change.column} via column-level lineage"
        if asset.type is AssetType.DASHBOARD:
            return f"Dashboard depends on {path[-2]} which uses dropped column"
        return f"Downstream asset uses dropped column through {path[-2]}"

    if change.change_type is ChangeType.ALTER_TYPE:
        if column_map is not None and _type_change_incompatible(change.old_type, change.new_type):
            old_t = _normalize_type(change.old_type)
            new_t = _normalize_type(change.new_type)
            return (
                f"Downstream asset uses {change.column} via column-level lineage; {old_t} → {new_t} is an incompatible type change"
            )
        if column_map is None and path and len(path) >= 2:
            return "Type impact uncertain without column-level confirmation"
        return "Type mismatch likely breaks downstream computation" if column_map is not None else "No consumers detected"

    if change.change_type is ChangeType.RENAME_COLUMN:
        if not path or len(path) < 2:
            return "No consumers detected"
        if column_map is None:
            return "Column rename may break; cannot confirm without column map"
        if _column_map_has_alias(column_map, change.column, change.new_type):
            if asset.type is AssetType.DASHBOARD:
                return "Dashboard depends on downstream asset with alias-backed rename; column-level lineage confirms dependency"
            return "Downstream asset has column-level lineage with an alias entry in the column map; rename is partially backward-compatible"
        return "Rename breaks direct column reference"

    if change.change_type is ChangeType.ALTER_NULLABILITY:
        if column_map is None and path and len(path) >= 2:
            return "Cannot confirm impact without column-level lineage"
        return "Cannot confirm impact without column-level lineage"

    if change.change_type is ChangeType.ADD_COLUMN:
        strict_schema = (asset.criticality or "").strip().lower() == "strict_schema"
        if strict_schema:
            return "Heuristic only; possible strict schema consumer"
        return "Additive change; no breakage expected"

    return "Unknown change type"


@dataclass(frozen=True)
class RuleOutcome:
    severity: Severity
    confidence: Confidence
    reason: str


def rule_drop_column(change: SchemaChange, column_map: list[dict[str, str]] | None, has_downstream: bool) -> RuleOutcome:
    if not has_downstream:
        return RuleOutcome(Severity.LOW, Confidence.HIGH, "No consumers detected")

    if column_map is None:
        return RuleOutcome(Severity.HIGH, Confidence.MEDIUM, "Table dependency confirmed; column usage unknown")

    if _column_map_references(column_map, change.column):
        return RuleOutcome(Severity.CRITICAL, Confidence.HIGH, "Direct column dependency on dropped field")

    return RuleOutcome(Severity.LOW, Confidence.HIGH, "No consumers detected")


def rule_rename_column(change: SchemaChange, column_map: list[dict[str, str]] | None, has_downstream: bool) -> RuleOutcome:
    if not has_downstream:
        return RuleOutcome(Severity.LOW, Confidence.HIGH, "No consumers detected")

    if column_map is None:
        return RuleOutcome(Severity.HIGH, Confidence.MEDIUM, "Column rename may break; cannot confirm without column map")

    if _column_map_has_alias(column_map, change.column, change.new_type):
        return RuleOutcome(Severity.MEDIUM, Confidence.HIGH, "Alias provides backward compatibility but risk exists")

    return RuleOutcome(Severity.CRITICAL, Confidence.HIGH, "Rename breaks direct column reference")


def rule_alter_type(change: SchemaChange, column_map: list[dict[str, str]] | None, has_downstream: bool) -> RuleOutcome:
    if not has_downstream:
        return RuleOutcome(Severity.LOW, Confidence.HIGH, "No consumers detected")

    if column_map is None:
        return RuleOutcome(Severity.MEDIUM, Confidence.MEDIUM, "Type impact uncertain without column-level confirmation")

    if _type_change_incompatible(change.old_type, change.new_type):
        return RuleOutcome(Severity.HIGH, Confidence.HIGH, "Type mismatch likely breaks downstream computation")

    if _type_change_compatible(change.old_type, change.new_type):
        return RuleOutcome(Severity.LOW, Confidence.HIGH, "Widening type change unlikely to break")

    # Unknown compatibility: still column-level confirmed, default to HIGH risk per doc's focus on incompatibility.
    return RuleOutcome(Severity.HIGH, Confidence.HIGH, "Type mismatch likely breaks downstream computation")


def rule_alter_nullability(change: SchemaChange, column_map: list[dict[str, str]] | None, has_downstream: bool) -> RuleOutcome:
    if not has_downstream:
        return RuleOutcome(Severity.LOW, Confidence.HIGH, "No consumers detected")

    if column_map is None:
        return RuleOutcome(Severity.MEDIUM, Confidence.MEDIUM, "Cannot confirm impact without column-level lineage")

    old_n = _normalize_type(change.old_type)
    new_n = _normalize_type(change.new_type)

    if old_n == "NOT NULL" and new_n == "NULL":
        return RuleOutcome(Severity.LOW, Confidence.HIGH, "Loosening constraint; unlikely to break consumers")
    if old_n == "NULL" and new_n == "NOT NULL":
        return RuleOutcome(Severity.HIGH, Confidence.HIGH, "Tightening constraint; may break inserts in dependent pipelines")

    return RuleOutcome(Severity.MEDIUM, Confidence.HIGH, "Cannot confirm impact without column-level lineage")


def rule_add_column(asset: Asset, has_downstream: bool) -> RuleOutcome:
    # For additive changes, downstream "reference" is mostly absent in lineage graphs;
    # this rule relies on a heuristic strict-schema tag carried in metadata.
    strict_schema = (asset.criticality or "").strip().lower() == "strict_schema"
    if strict_schema:
        return RuleOutcome(Severity.MEDIUM, Confidence.LOW, "Heuristic only; possible strict schema consumer")
    return RuleOutcome(Severity.LOW, Confidence.HIGH, "Additive change; no breakage expected")


class ImpactRulesEngine:
    @staticmethod
    def evaluate(
        change: SchemaChange,
        asset: Asset | None,
        path: list[str],
        column_map: list[dict[str, str]] | None,
    ) -> ImpactRecord:
        if not path:
            return ImpactRecord(
                asset_id=change.entity,
                asset_name=change.entity,
                asset_type=AssetType.TABLE,
                severity=Severity.LOW,
                confidence=Confidence.LOW,
                reason="Lineage graph is empty",
                path=[],
            )

        has_downstream = len(path) >= 2

        if asset is None:
            # Keep a conservative severity default, but do not claim high confidence.
            outcome = RuleOutcome(Severity.LOW, Confidence.LOW, "asset not resolved")
            return ImpactRecord(
                asset_id=change.entity,
                asset_name=change.entity,
                asset_type=AssetType.TABLE,
                severity=outcome.severity,
                confidence=outcome.confidence,
                reason=outcome.reason,
                path=path,
            )

        if change.change_type is ChangeType.DROP_COLUMN:
            outcome = rule_drop_column(change, column_map, has_downstream)
        elif change.change_type is ChangeType.RENAME_COLUMN:
            outcome = rule_rename_column(change, column_map, has_downstream)
        elif change.change_type is ChangeType.ALTER_TYPE:
            outcome = rule_alter_type(change, column_map, has_downstream)
        elif change.change_type is ChangeType.ALTER_NULLABILITY:
            outcome = rule_alter_nullability(change, column_map, has_downstream)
        elif change.change_type is ChangeType.ADD_COLUMN:
            outcome = rule_add_column(asset, has_downstream)
        else:
            outcome = RuleOutcome(Severity.LOW, Confidence.LOW, "Unknown change type")

        computed_path = _compute_path(change, path, asset, column_map)
        return ImpactRecord(
            asset_id=asset.id,
            asset_name=asset.name,
            asset_type=asset.type,
            owner=asset.owner,
            severity=outcome.severity,
            confidence=outcome.confidence,
            reason=_format_reason(change, asset, path, column_map),
            path=computed_path,
        )
