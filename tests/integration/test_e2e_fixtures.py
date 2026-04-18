from __future__ import annotations

from main import run_fixture
from src.parser.fixture_loader import FixtureLoader


def test_e2e_all_fixtures_match_expected() -> None:
    loader = FixtureLoader.default()
    for fixture_id in ["F1", "F2", "F3", "F4", "F5"]:
        expected = loader.load_expected(fixture_id)
        actual = run_fixture(fixture_id)
        assert actual == expected
