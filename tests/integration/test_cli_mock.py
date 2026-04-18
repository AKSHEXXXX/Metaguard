from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_mock_changed_files_fixture_prints_markdown() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "main.py", "--mock", "--changed-files", "F1"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "MetaGuard" in out
    assert "Impact Detected" in out
    assert (
        "| Asset | Type | Severity | Confidence | Reason |" in out
        or "| Asset | Owner | Type | Severity | Confidence | Reason |" in out
    )
