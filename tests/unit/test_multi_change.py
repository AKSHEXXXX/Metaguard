from __future__ import annotations

import os

from src.domain.enums import ChangeType
from src.parser.diff_parser import DiffParser


def test_multi_change_migration_parsing() -> None:
    """Phase 3: Verify the diff parser correctly handles a single migration file with multiple changes."""
    # Assuming tests are run from the project root
    sql_path = os.path.join(os.path.dirname(__file__), "..", "..", "migrations", "demo_schema_change.sql")
    
    with open(sql_path, "r") as f:
        content = f.read()

    changes = DiffParser.parse(content)
    
    # The demo migration has 4 changes: DROP, RENAME, ALTER TYPE, ADD
    assert len(changes) == 4
    
    # 1. DROP COLUMN legacy_id
    drop = next(c for c in changes if c.change_type == ChangeType.DROP_COLUMN)
    assert drop.entity == "fact_orders"
    assert drop.column == "legacy_id"
    
    # 2. RENAME COLUMN old_customer_ref TO customer_id
    rename = next(c for c in changes if c.change_type == ChangeType.RENAME_COLUMN)
    assert rename.entity == "fact_orders"
    assert rename.column == "old_customer_ref"
    assert rename.new_type == "customer_id"
    
    # 3. ALTER COLUMN amount TYPE VARCHAR(255)
    alter = next(c for c in changes if c.change_type == ChangeType.ALTER_TYPE)
    assert alter.entity == "fact_orders"
    assert alter.column == "amount"
    assert alter.new_type == "VARCHAR(255)"
    
    # 4. ADD COLUMN created_at TIMESTAMP
    add = next(c for c in changes if c.change_type == ChangeType.ADD_COLUMN)
    assert add.entity == "fact_orders"
    assert add.column == "created_at"
