from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class FixtureNotFoundError(FileNotFoundError):
    def __init__(self, fixture_id: str, fixture_kind: str, path: Path) -> None:
        super().__init__(f"{fixture_kind} fixture {fixture_id} not found at {path}")
        self.fixture_id = fixture_id
        self.fixture_kind = fixture_kind
        self.path = path


class FixtureValidationError(ValueError):
    def __init__(self, fixture_id: str, fixture_kind: str, message: str) -> None:
        super().__init__(f"Invalid {fixture_kind} fixture {fixture_id}: {message}")
        self.fixture_id = fixture_id
        self.fixture_kind = fixture_kind


@dataclass(frozen=True)
class FixtureLoader:
    base_dir: Path

    @classmethod
    def default(cls) -> FixtureLoader:
        repo_root = Path(__file__).resolve().parents[2]
        return cls(base_dir=repo_root / "tests" / "fixtures")

    def load_diff(self, fixture_id: str) -> dict[str, Any]:
        return self._load_json("diffs", f"{fixture_id}_diff.json", fixture_id)

    def load_lineage(self, fixture_id: str) -> dict[str, Any]:
        return self._load_json("lineage", f"{fixture_id}_lineage.json", fixture_id)

    def load_expected(self, fixture_id: str) -> dict[str, Any]:
        return self._load_json("expected", f"{fixture_id}_expected.json", fixture_id)

    def load_all(self, fixture_id: str) -> dict[str, dict[str, Any]]:
        return {
            "diff": self.load_diff(fixture_id),
            "lineage": self.load_lineage(fixture_id),
            "expected": self.load_expected(fixture_id),
        }

    def _load_json(self, subdir: str, filename: str, fixture_id: str) -> dict[str, Any]:
        path = self.base_dir / subdir / filename
        if not path.exists():
            raise FixtureNotFoundError(fixture_id=fixture_id, fixture_kind=subdir, path=path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        self._validate_payload(subdir=subdir, fixture_id=fixture_id, payload=payload)
        return payload

    def _validate_payload(self, subdir: str, fixture_id: str, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise FixtureValidationError(fixture_id, subdir, "root must be a JSON object")

        if subdir == "diffs":
            required = {"id", "changes"}
            missing = sorted(required - set(payload.keys()))
            if missing:
                raise FixtureValidationError(fixture_id, subdir, f"missing keys: {', '.join(missing)}")
            if not isinstance(payload.get("changes"), list):
                raise FixtureValidationError(fixture_id, subdir, "'changes' must be a list")
            return

        if subdir == "lineage":
            required = {"id", "nodes", "edges"}
            missing = sorted(required - set(payload.keys()))
            if missing:
                raise FixtureValidationError(fixture_id, subdir, f"missing keys: {', '.join(missing)}")
            if not isinstance(payload.get("nodes"), list) or not isinstance(payload.get("edges"), list):
                raise FixtureValidationError(fixture_id, subdir, "'nodes' and 'edges' must be lists")
            return

        if subdir == "expected":
            required = {"id", "highest_severity", "total_affected", "records"}
            missing = sorted(required - set(payload.keys()))
            if missing:
                raise FixtureValidationError(fixture_id, subdir, f"missing keys: {', '.join(missing)}")
            if not isinstance(payload.get("records"), list):
                raise FixtureValidationError(fixture_id, subdir, "'records' must be a list")
