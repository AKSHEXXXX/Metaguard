from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv


DEFAULT_TIMEOUT_SECONDS = 15
CANDIDATE_SERVICES = [
    "sample_athena",
    "acme_nexus_raw_data",
    "acme_nexus_analytics",
    "sample_redshift",
    "sample_snowflake",
    "sample_databricks",
    "sample_airflow",
    "sample_tableau",
    "sample_superset",
]
SEARCH_RESULT_LIMIT = 5


def _read_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} must be set")
    return value


def _get_json(host: str, token: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    query = f"?{urlencode(params)}" if params else ""
    url = f"{host.rstrip('/')}{path}{query}"
    req = Request(
        url=url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="GET",
    )
    with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:  # nosec - operator-supplied host/token
        payload = json.loads(resp.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object from {url}")
    return payload


def _search_tables_for_service(host: str, token: str, service: str) -> list[dict[str, Any]]:
    payload = _get_json(
        host,
        token,
        "/api/v1/search/query",
        {"q": service, "index": "table_search_index", "from": 0, "size": SEARCH_RESULT_LIMIT},
    )
    hits = payload.get("hits", {}).get("hits", [])
    if not isinstance(hits, list):
        return []

    tables: list[dict[str, Any]] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        source = hit.get("_source", {})
        if not isinstance(source, dict):
            continue
        fqn = source.get("fullyQualifiedName")
        table_id = source.get("id")
        if isinstance(fqn, str) and isinstance(table_id, str) and fqn.lower().startswith(f"{service.lower()}."):
            tables.append({"fullyQualifiedName": fqn, "id": table_id})
    return tables


def main() -> None:
    load_dotenv()
    host = _read_required("OPENMETADATA_HOST")
    token = _read_required("OPENMETADATA_TOKEN")

    print("Probing lineage for known sandbox services...\n")

    for service in CANDIDATE_SERVICES:
        try:
            tables = _search_tables_for_service(host, token, service)
        except Exception as exc:
            print(f"  {service}: search failed ({exc})")
            continue

        if not isinstance(tables, list) or not tables:
            print(f"  {service}: no tables found")
            continue

        found = False
        for table in tables:
            if not isinstance(table, dict):
                continue
            table_id = table.get("id")
            fqn = table.get("fullyQualifiedName")
            if not isinstance(table_id, str) or not isinstance(fqn, str) or not fqn:
                continue

            try:
                lineage_payload = _get_json(
                    host,
                    token,
                    f"/api/v1/lineage/table/{table_id}",
                    {"downstreamDepth": 2, "upstreamDepth": 0},
                )
            except Exception:
                continue

            downstream = lineage_payload.get("downstreamEdges", [])
            nodes = lineage_payload.get("nodes", [])
            if isinstance(downstream, list) and downstream:
                found = True
                print(f"  ✅ {fqn}")
                print(f"     id={table_id}")
                print(f"     downstream_edges={len(downstream)}  nodes={len(nodes) if isinstance(nodes, list) else 0}")

        if not found:
            print(f"  {service}: sampled tables had no downstream lineage")

    print("\nDone. Use a ✅ entity for smoke test and demo PR.")


if __name__ == "__main__":
    main()
