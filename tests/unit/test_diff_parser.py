from __future__ import annotations

from src.domain.enums import ChangeType
from src.parser.diff_parser import DiffParser


def test_parse_drop_column() -> None:
    changes = DiffParser.parse('ALTER TABLE analytics.customers DROP COLUMN customer_id;')
    assert len(changes) == 1
    assert changes[0].change_type is ChangeType.DROP_COLUMN
    assert changes[0].column == "customer_id"


def test_parse_add_column() -> None:
    changes = DiffParser.parse("ALTER TABLE analytics.customers ADD COLUMN new_col INT;")
    assert len(changes) == 1
    assert changes[0].change_type is ChangeType.ADD_COLUMN
    assert changes[0].column == "new_col"


def test_parse_rename_column() -> None:
    changes = DiffParser.parse("ALTER TABLE analytics.customers RENAME COLUMN old_name TO new_name;")
    assert len(changes) == 1
    assert changes[0].change_type is ChangeType.RENAME_COLUMN
    assert changes[0].column == "old_name"


def test_parse_alter_column_type() -> None:
    changes = DiffParser.parse("ALTER TABLE analytics.customers ALTER COLUMN customer_id TYPE VARCHAR(255);")
    assert len(changes) == 1
    assert changes[0].change_type is ChangeType.ALTER_TYPE
    assert changes[0].column == "customer_id"
