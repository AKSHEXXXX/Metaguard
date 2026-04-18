from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from dotenv import load_dotenv


UPSTREAM_FQN = "sample_snowflake.ANALYTICS_DB.prod.order_summary"
DOWNSTREAM_FQN = "sample_redshift.staging_db.integration.dim_customer"
UPSTREAM_COLUMN = "sample_snowflake.ANALYTICS_DB.prod.order_summary.customer_name"
DOWNSTREAM_COLUMN = "sample_redshift.staging_db.integration.dim_customer.customer_name"


def _read_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} must be set")
    return value


def _request_json(host: str, token: str, path: str, *, method: str = "GET", body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    url = f"{host.rstrip('/')}{path}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(body).encode("utf-8")

    req = Request(url, headers=headers, data=payload, method=method)
    try:
        with urlopen(req, timeout=30) as resp:  # nosec - operator-provided OpenMetadata endpoint
            raw = resp.read().decode("utf-8")
            return getattr(resp, "status", 200), json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return exc.code, parsed


def _resolve_table(host: str, token: str, fqn: str) -> dict[str, Any]:
    status, payload = _request_json(host, token, f"/api/v1/tables/name/{quote(fqn, safe='')}")
    if status >= 400:
        raise RuntimeError(f"resolve failed for {fqn}: {status} {json.dumps(payload)}")
    return payload


def main() -> int:
    load_dotenv()
    host = _read_required("OPENMETADATA_HOST")
    token = _read_required("OPENMETADATA_TOKEN")

    upstream = _resolve_table(host, token, UPSTREAM_FQN)
    downstream = _resolve_table(host, token, DOWNSTREAM_FQN)

    payloads = [
        {
            "edge": {
                "fromEntity": {"id": upstream["id"], "type": "table"},
                "toEntity": {"id": downstream["id"], "type": "table"},
                "lineageDetails": {
                    "columnsLineage": [
                        {
                            "fromColumns": [UPSTREAM_COLUMN],
                            "toColumns": [DOWNSTREAM_COLUMN],
                        }
                    ]
                },
            }
        },
        {
            "fromEntity": {"id": upstream["id"], "type": "table"},
            "toEntity": {"id": downstream["id"], "type": "table"},
            "lineageDetails": {
                "columnsLineage": [
                    {
                        "fromColumns": [UPSTREAM_COLUMN],
                        "toColumns": [DOWNSTREAM_COLUMN],
                    }
                ]
            },
        },
        {
            "fromEntity": upstream["id"],
            "toEntity": downstream["id"],
            "lineageDetails": {
                "columnsLineage": [
                    {
                        "fromColumns": [UPSTREAM_COLUMN],
                        "toColumns": [DOWNSTREAM_COLUMN],
                    }
                ]
            },
        },
    ]

    for index, payload in enumerate(payloads, start=1):
        status, response = _request_json(host, token, "/api/v1/lineage", method="PUT", body=payload)
        print(f"Attempt {index}: PUT /api/v1/lineage -> {status}")
        print(json.dumps(response, indent=2)[:4000])
        if status in (200, 201):
            return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
