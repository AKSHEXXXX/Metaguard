from __future__ import annotations

from src.domain.enums import AssetType, ChangeType, Confidence, Severity
from src.domain.models import Asset, SchemaChange
from src.engine.rules import ImpactRulesEngine


def _asset(asset_id: str = "a1", name: str = "downstream", t: AssetType = AssetType.TABLE, criticality: str | None = None) -> Asset:
    return Asset(id=asset_id, name=name, type=t, owner=None, criticality=criticality)


def test_drop_column_with_column_lineage_is_critical_high() -> None:
    change = SchemaChange(entity="analytics.customers", change_type=ChangeType.DROP_COLUMN, column="customer_id")
    record = ImpactRulesEngine.evaluate(
        change=change,
        asset=_asset(),
        path=["analytics.customers", "stg_customers"],
        column_map=[{"from": "customer_id", "to": "customer_id"}],
    )
    assert record.severity is Severity.CRITICAL
    assert record.confidence is Confidence.HIGH


def test_drop_column_table_level_only_is_high_medium() -> None:
    change = SchemaChange(entity="analytics.customers", change_type=ChangeType.DROP_COLUMN, column="customer_id")
    record = ImpactRulesEngine.evaluate(change, _asset(), ["analytics.customers", "nightly_customer_rollup"], None)
    assert record.severity is Severity.HIGH
    assert record.confidence is Confidence.MEDIUM


def test_drop_column_no_downstream_is_low_high() -> None:
    change = SchemaChange(entity="analytics.customers", change_type=ChangeType.DROP_COLUMN, column="customer_id")
    record = ImpactRulesEngine.evaluate(change, _asset(), ["analytics.customers"], [{"from": "x", "to": "y"}])
    assert record.severity is Severity.LOW
    assert record.confidence is Confidence.HIGH


def test_rename_column_no_alias_is_critical_high() -> None:
    change = SchemaChange(entity="t", change_type=ChangeType.RENAME_COLUMN, column="old_col", new_type="new_col")
    record = ImpactRulesEngine.evaluate(change, _asset(), ["t", "ds"], [{"from": "old_col", "to": "old_col"}])
    assert record.severity is Severity.CRITICAL
    assert record.confidence is Confidence.HIGH


def test_rename_column_with_alias_is_medium_high() -> None:
    change = SchemaChange(entity="t", change_type=ChangeType.RENAME_COLUMN, column="old_col", new_type="new_col")
    record = ImpactRulesEngine.evaluate(
        change,
        _asset(),
        ["t", "ds"],
        [{"from": "old_col", "to": "old_col"}, {"from": "old_col", "to": "new_col"}],
    )
    assert record.severity is Severity.MEDIUM
    assert record.confidence is Confidence.HIGH


def test_rename_column_table_level_only_is_high_medium() -> None:
    change = SchemaChange(entity="t", change_type=ChangeType.RENAME_COLUMN, column="old_col", new_type="new_col")
    record = ImpactRulesEngine.evaluate(change, _asset(), ["t", "ds"], None)
    assert record.severity is Severity.HIGH
    assert record.confidence is Confidence.MEDIUM


def test_alter_type_incompatible_with_column_lineage_is_high_high() -> None:
    change = SchemaChange(
        entity="t", change_type=ChangeType.ALTER_TYPE, column="c", old_type="INT", new_type="VARCHAR(255)"
    )
    record = ImpactRulesEngine.evaluate(change, _asset(), ["t", "ds"], [{"from": "c", "to": "c"}])
    assert record.severity is Severity.HIGH
    assert record.confidence is Confidence.HIGH


def test_alter_type_compatible_with_column_lineage_is_low_high() -> None:
    change = SchemaChange(entity="t", change_type=ChangeType.ALTER_TYPE, column="c", old_type="INT", new_type="BIGINT")
    record = ImpactRulesEngine.evaluate(change, _asset(), ["t", "ds"], [{"from": "c", "to": "c"}])
    assert record.severity is Severity.LOW
    assert record.confidence is Confidence.HIGH


def test_alter_type_table_level_only_is_medium_medium() -> None:
    change = SchemaChange(entity="t", change_type=ChangeType.ALTER_TYPE, column="c", old_type="INT", new_type="BIGINT")
    record = ImpactRulesEngine.evaluate(change, _asset(), ["t", "ds"], None)
    assert record.severity is Severity.MEDIUM
    assert record.confidence is Confidence.MEDIUM


def test_alter_nullability_not_null_to_null_is_low_high() -> None:
    change = SchemaChange(
        entity="t", change_type=ChangeType.ALTER_NULLABILITY, column="c", old_type="NOT NULL", new_type="NULL"
    )
    record = ImpactRulesEngine.evaluate(change, _asset(), ["t", "ds"], [{"from": "c", "to": "c"}])
    assert record.severity is Severity.LOW
    assert record.confidence is Confidence.HIGH


def test_alter_nullability_null_to_not_null_is_high_high() -> None:
    change = SchemaChange(
        entity="t", change_type=ChangeType.ALTER_NULLABILITY, column="c", old_type="NULL", new_type="NOT NULL"
    )
    record = ImpactRulesEngine.evaluate(change, _asset(), ["t", "ds"], [{"from": "c", "to": "c"}])
    assert record.severity is Severity.HIGH
    assert record.confidence is Confidence.HIGH


def test_alter_nullability_table_level_only_is_medium_medium() -> None:
    change = SchemaChange(
        entity="t", change_type=ChangeType.ALTER_NULLABILITY, column="c", old_type="NULL", new_type="NOT NULL"
    )
    record = ImpactRulesEngine.evaluate(change, _asset(), ["t", "ds"], None)
    assert record.severity is Severity.MEDIUM
    assert record.confidence is Confidence.MEDIUM


def test_add_column_strict_schema_consumer_is_medium_low() -> None:
    change = SchemaChange(entity="t", change_type=ChangeType.ADD_COLUMN, column="new_col")
    record = ImpactRulesEngine.evaluate(change, _asset(criticality="strict_schema"), ["t", "ds"], None)
    assert record.severity is Severity.MEDIUM
    assert record.confidence is Confidence.LOW


def test_add_column_default_is_low_high() -> None:
    change = SchemaChange(entity="t", change_type=ChangeType.ADD_COLUMN, column="new_col")
    record = ImpactRulesEngine.evaluate(change, _asset(), ["t", "ds"], None)
    assert record.severity is Severity.LOW
    assert record.confidence is Confidence.HIGH


def test_path_computation_appends_column_except_for_dashboard_leaf() -> None:
    change = SchemaChange(entity="analytics.customers", change_type=ChangeType.DROP_COLUMN, column="customer_id")
    dashboard = _asset(asset_id="d1", name="Revenue by Customer", t=AssetType.DASHBOARD)
    record = ImpactRulesEngine.evaluate(
        change,
        dashboard,
        ["analytics.customers", "stg_customers", "Revenue by Customer"],
        [{"from": "customer_id", "to": "customer_id"}],
    )
    assert record.path == ["analytics.customers.customer_id", "stg_customers.customer_id", "Revenue by Customer"]


def test_empty_lineage_graph_returns_low_low() -> None:
    change = SchemaChange(entity="t", change_type=ChangeType.DROP_COLUMN, column="c")
    record = ImpactRulesEngine.evaluate(change, _asset(), [], None)
    assert record.severity is Severity.LOW
    assert record.confidence is Confidence.LOW
