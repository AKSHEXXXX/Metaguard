from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import urlencode, urljoin
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from src.adapters.mcp_client import MCPClient, MCPTransportError
from src.config import load_config
from src.domain.enums import ChangeType
from src.domain.models import ImpactRecord, LineageGraph, SchemaChange
from src.engine.reporter import ReportBuilder
from src.engine.rules import ImpactRulesEngine
from src.engine.traverser import LineageTraverser
from src.providers.mcp_provider import MCPMetadataProvider
from src.providers.openmetadata_provider import OpenMetadataProvider


def _discover_table_fqns(host: str, token: str, limit: int = 25) -> list[str]:
    params = urlencode({"limit": str(limit)})
    url = urljoin(host.rstrip("/") + "/", f"api/v1/tables?{params}")
    req = Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, method="GET")
    with urlopen(req, timeout=30) as resp:  # nosec - smoke script only
        payload = json.loads(resp.read().decode("utf-8"))
    tables = payload.get("data", [])
    if not tables:
        raise RuntimeError("No tables found in sandbox.")
    out: list[str] = []
    for table in tables:
        if isinstance(table, dict):
            fqn = table.get("fullyQualifiedName")
            if isinstance(fqn, str) and fqn:
                out.append(fqn)
    if not out:
        raise RuntimeError("Unable to read fullyQualifiedName values from sandbox response.")
    return out


def _serialize_report(report_id: str, report) -> str:  # noqa: ANN001
    def _record(r: ImpactRecord) -> dict:
        return {
            "asset_id": r.asset_id,
            "asset_name": r.asset_name,
            "asset_type": r.asset_type.value,
            "owner": r.owner,
            "severity": r.severity.value,
            "confidence": r.confidence.value,
            "reason": r.reason,
            "path": r.path,
        }

    payload = {
        "id": report_id,
        "highest_severity": report.highest_severity.value,
        "total_affected": report.total_affected,
        "generated_at": report.generated_at.isoformat() if isinstance(report.generated_at, datetime) else str(report.generated_at),
        "records": [_record(r) for r in report.records],
    }
    return json.dumps(payload, indent=2)


def _probe_mcp(url: str, token: str) -> tuple[bool, str]:
    req = Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "text/event-stream"}, method="GET")
    try:
        with urlopen(req, timeout=5) as resp:  # nosec - smoke probe only
            code = getattr(resp, "status", 200)
        return code in (200, 101), f"status={code}"
    except HTTPError as exc:
        return False, f"status={exc.code}"
    except Exception as exc:  # pragma: no cover
        return False, str(exc)


def main() -> None:
    load_dotenv()
    cfg = load_config()

    mcp_client = MCPClient(mcp_url=cfg.om_mcp_url, jwt_token=cfg.om_token)
    rest_provider = OpenMetadataProvider(host=cfg.om_host, jwt_token=cfg.om_token)
    provider = MCPMetadataProvider(mcp_client=mcp_client, rest_fallback=rest_provider, depth=cfg.lineage_max_depth)
    transport_used = "mcp"

    mcp_ok, reason = _probe_mcp(cfg.om_mcp_url, cfg.om_token)
    if mcp_ok:
        print("MCP probe success:", reason)
    else:
        print("MCP probe failed:", reason)
        print("Falling back to REST provider")
        transport_used = "rest-fallback"
        provider = rest_provider

    try:
        candidate_fqns = _discover_table_fqns(cfg.om_host, cfg.om_token, limit=5)
        picked_ref = candidate_fqns[0]
        asset = provider.resolve_asset(picked_ref)
        print("Discovered table:", picked_ref)
        print("Resolved:", asset.name)
        try:
            lineage = provider.get_downstream_lineage(asset.id)
        except Exception as lineage_exc:
            print("Lineage fetch failed, continuing with empty lineage:", lineage_exc)
            lineage = LineageGraph(nodes={asset.id: asset}, edges=[])

        print("Downstream nodes:", len(lineage.nodes))
        print("Downstream edges:", len(lineage.edges))

        change = SchemaChange(entity=asset.name, change_type=ChangeType.DROP_COLUMN, column="id")
        downstream = LineageTraverser.traverse(root_id=asset.id, graph=lineage, depth=cfg.lineage_max_depth)
        name_to_id = {a.name: a.id for a in lineage.nodes.values()}
        edge_map = {(e.from_id, e.to_id): e for e in lineage.edges}

        records: list[ImpactRecord] = []
        for affected_asset, path_names in downstream:
            if len(path_names) < 2:
                continue
            prev_id = name_to_id.get(path_names[-2])
            column_map = edge_map.get((prev_id, affected_asset.id)).column_map if prev_id and edge_map.get((prev_id, affected_asset.id)) else None
            records.append(
                ImpactRulesEngine.evaluate(
                    change=change,
                    asset=affected_asset,
                    path=path_names,
                    column_map=column_map,
                )
            )

        report = ReportBuilder.build(report_id="LIVE_SMOKE", changes=[change], records=records)
        print("Transport used:", transport_used)
        print("ImpactReport JSON:")
        print(_serialize_report("LIVE_SMOKE", report))
    except Exception as exc:  # pragma: no cover - smoke script runtime path
        print("Error:", exc)


if __name__ == "__main__":
    main()
