from __future__ import annotations

import json
from typing import Any

import pytest

from src.adapters.github_adapter import GitHubAdapter


class _FakeHTTPResponse:
    def __init__(self, payload: Any) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


def _json_body(req) -> dict:  # noqa: ANN001
    if req.data is None:
        return {}
    return json.loads(req.data.decode("utf-8"))


def test_post_pr_comment_creates_when_no_existing_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    payloads: list[dict] = []

    def fake_urlopen(req, timeout=10):  # noqa: ANN001
        calls.append((req.get_method(), req.full_url))
        if req.full_url == "https://api.github.com/user":
            return _FakeHTTPResponse({"login": "metaguard-bot"})
        if req.full_url.endswith("/repos/acme/widgets/issues/12/comments?per_page=100"):
            return _FakeHTTPResponse([])
        if req.full_url.endswith("/repos/acme/widgets/issues/12/comments") and req.get_method() == "POST":
            payloads.append(_json_body(req))
            return _FakeHTTPResponse({"id": 999})
        raise AssertionError(f"Unexpected request: {req.get_method()} {req.full_url}")

    monkeypatch.setattr("src.adapters.github_adapter.urlopen", fake_urlopen)

    gh = GitHubAdapter(github_token="t", repo="acme/widgets")
    gh.post_pr_comment(pr_number=12, body="Hello world")

    assert calls == [
        ("GET", "https://api.github.com/user"),
        ("GET", "https://api.github.com/repos/acme/widgets/issues/12/comments?per_page=100"),
        ("POST", "https://api.github.com/repos/acme/widgets/issues/12/comments"),
    ]
    assert payloads and "body" in payloads[0]
    assert "Hello world" in payloads[0]["body"]
    assert GitHubAdapter.MARKER in payloads[0]["body"]


def test_post_pr_comment_updates_when_marker_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    payloads: list[dict] = []

    def fake_urlopen(req, timeout=10):  # noqa: ANN001
        calls.append((req.get_method(), req.full_url))
        if req.full_url == "https://api.github.com/user":
            return _FakeHTTPResponse({"login": "metaguard-bot"})
        if req.full_url.endswith("/repos/acme/widgets/issues/12/comments?per_page=100"):
            return _FakeHTTPResponse(
                [
                    {
                        "id": 123,
                        "body": f"Old text\n\n{GitHubAdapter.MARKER}\n",
                        "user": {"login": "metaguard-bot"},
                    }
                ]
            )
        if req.full_url.endswith("/repos/acme/widgets/issues/comments/123") and req.get_method() == "PATCH":
            payloads.append(_json_body(req))
            return _FakeHTTPResponse({"id": 123})
        raise AssertionError(f"Unexpected request: {req.get_method()} {req.full_url}")

    monkeypatch.setattr("src.adapters.github_adapter.urlopen", fake_urlopen)

    gh = GitHubAdapter(github_token="t", repo="acme/widgets")
    gh.post_pr_comment(pr_number=12, body="New text")

    assert calls == [
        ("GET", "https://api.github.com/user"),
        ("GET", "https://api.github.com/repos/acme/widgets/issues/12/comments?per_page=100"),
        ("PATCH", "https://api.github.com/repos/acme/widgets/issues/comments/123"),
    ]
    assert payloads and "body" in payloads[0]
    assert payloads[0]["body"].startswith("New text")
    assert GitHubAdapter.MARKER in payloads[0]["body"]


def test_get_changed_files(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout=10):  # noqa: ANN001
        if req.full_url.endswith("/repos/acme/widgets/pulls/12/files"):
            return _FakeHTTPResponse(
                [
                    {"filename": "migrations/001.sql"},
                    {"filename": "models/stg_orders.sql"},
                ]
            )
        raise AssertionError(f"Unexpected request: {req.get_method()} {req.full_url}")

    monkeypatch.setattr("src.adapters.github_adapter.urlopen", fake_urlopen)
    gh = GitHubAdapter(github_token="t", repo="acme/widgets")
    files = gh.get_changed_files(pr_number=12)
    assert files == ["migrations/001.sql", "models/stg_orders.sql"]

