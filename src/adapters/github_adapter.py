from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class _GitHubComment:
    id: int
    body: str
    user_login: str | None


class GitHubAdapter:
    """
    Minimal GitHub REST adapter (stdlib only).

    Implements an idempotent PR comment: create a single bot comment per PR,
    and update it on subsequent runs.
    """

    MARKER = "<!-- metaguard-bot-comment -->"

    def __init__(self, *, github_token: str, repo: str, api_base: str = "https://api.github.com") -> None:
        self.github_token = github_token
        self.repo = repo  # owner/name
        self.api_base = api_base.rstrip("/")
        self._cached_login: str | None = None

    @classmethod
    def from_env(cls) -> "GitHubAdapter":
        repo = os.environ.get("GITHUB_REPOSITORY")
        token = os.environ.get("GITHUB_TOKEN")
        api_base = os.environ.get("GITHUB_API_URL") or "https://api.github.com"
        if not repo:
            raise RuntimeError("Missing GITHUB_REPOSITORY.")
        if not token:
            raise RuntimeError("Missing GITHUB_TOKEN.")
        return cls(github_token=token, repo=repo, api_base=api_base)

    def post_pr_comment(self, pr_number: int, body: str) -> None:
        """
        Create or update a single MetaGuard bot comment on a PR.

        Identification:
        - Hidden HTML marker `<!-- metaguard-bot-comment -->`
        """

        final_body = self._ensure_marker(body)
        existing = self._find_existing_comment(pr_number=pr_number)

        if existing is None:
            self._create_comment(pr_number=pr_number, body=final_body)
            return

        self._update_comment(comment_id=existing.id, body=final_body)

    def post_or_update_comment(self, pr_number: int, body: str) -> None:
        self.post_pr_comment(pr_number=pr_number, body=body)

    def get_changed_files(self, pr_number: int) -> list[str]:
        payload = self._request_json(
            "GET",
            f"/repos/{self.repo}/pulls/{pr_number}/files",
        )
        if not isinstance(payload, list):
            return []
        out: list[str] = []
        for item in payload:
            if isinstance(item, dict):
                name = item.get("filename")
                if isinstance(name, str):
                    out.append(name)
        return out

    def _ensure_marker(self, body: str) -> str:
        if self.MARKER in body:
            return body
        body = body.rstrip()
        if body:
            return f"{body}\n\n{self.MARKER}\n"
        return f"{self.MARKER}\n"


    def _find_existing_comment(self, *, pr_number: int) -> _GitHubComment | None:
        # For PR review comments you’d use /pulls/{pr}/comments; for issue-style PR comments use /issues/{pr}/comments.
        comments = self._request_json(
            "GET",
            f"/repos/{self.repo}/issues/{pr_number}/comments?per_page=100",
        )
        if not isinstance(comments, list):
            raise RuntimeError("GitHub API returned unexpected comments payload")

        for c in comments:
            if not isinstance(c, dict):
                continue
            body = c.get("body")
            if not isinstance(body, str) or self.MARKER not in body:
                continue

            cid = c.get("id")
            if isinstance(cid, int):
                user = c.get("user") or {}
                login = user.get("login") if isinstance(user, dict) else None
                return _GitHubComment(id=cid, body=body, user_login=login)
        return None

    def _create_comment(self, *, pr_number: int, body: str) -> None:
        self._request_json(
            "POST",
            f"/repos/{self.repo}/issues/{pr_number}/comments",
            data={"body": body},
        )

    def _update_comment(self, *, comment_id: int, body: str) -> None:
        self._request_json(
            "PATCH",
            f"/repos/{self.repo}/issues/comments/{comment_id}",
            data={"body": body},
        )

    def _request_json(self, method: str, path_or_url: str, data: Optional[dict[str, Any]] = None) -> Any:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        else:
            url = f"{self.api_base}{path_or_url}"

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.github_token}",
            "User-Agent": "metaguard",
        }

        raw_data: bytes | None = None
        if data is not None:
            raw_data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = Request(url, data=raw_data, headers=headers, method=method)
        with urlopen(req, timeout=10) as resp:  # nosec - exercised via unit tests, used only in runtime wiring
            raw = resp.read()
        if not raw:
            return None
        return json.loads(raw.decode("utf-8"))
