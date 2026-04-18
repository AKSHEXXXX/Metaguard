from __future__ import annotations

import json
import pytest

from src.parser.fixture_loader import FixtureLoader, FixtureNotFoundError, FixtureValidationError


@pytest.mark.parametrize("fixture_id", ["F1", "F2", "F3", "F4", "F5"])
def test_fixture_loader_loads_all_fixture_sets(fixture_id: str) -> None:
    loader = FixtureLoader.default()

    diff = loader.load_diff(fixture_id)
    lineage = loader.load_lineage(fixture_id)
    expected = loader.load_expected(fixture_id)

    assert diff["id"] == fixture_id
    assert lineage["id"] == fixture_id
    assert expected["id"] == fixture_id


def test_fixture_loader_missing_fixture_raises() -> None:
    loader = FixtureLoader.default()

    with pytest.raises(FixtureNotFoundError):
        loader.load_diff("F404")


def test_fixture_loader_invalid_schema_raises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    base = tmp_path / "fixtures"
    (base / "diffs").mkdir(parents=True)
    (base / "lineage").mkdir(parents=True)
    (base / "expected").mkdir(parents=True)

    # Invalid diff fixture: missing "changes"
    (base / "diffs" / "F1_diff.json").write_text(json.dumps({"id": "F1"}), encoding="utf-8")
    (base / "lineage" / "F1_lineage.json").write_text(json.dumps({"id": "F1", "nodes": [], "edges": []}), encoding="utf-8")
    (base / "expected" / "F1_expected.json").write_text(
        json.dumps({"id": "F1", "highest_severity": "LOW", "total_affected": 0, "records": []}),
        encoding="utf-8",
    )

    loader = FixtureLoader(base_dir=base)
    with pytest.raises(FixtureValidationError):
        loader.load_diff("F1")
