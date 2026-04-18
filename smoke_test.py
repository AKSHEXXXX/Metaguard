from __future__ import annotations

import json
import os

from dotenv import load_dotenv

from src.adapters.mcp_client import MCPClient, MCPTransportError
from src.config import load_config
from src.domain.enums import ChangeType
from src.domain.models import SchemaChange
from src.engine.renderer import PRCommentRenderer
from src.engine.reporter import ReportBuilder
from src.engine.rules import ImpactRulesEngine
from src.engine.traverser import LineageTraverser
from src.providers.mcp_provider import MCPMetadataProvider
from src.providers.openmetadata_provider import OpenMetadataProvider


SMOKE_ENTITY_FQN = "acme_nexus_analytics.ANALYTICS.MARTS.fact_orders"


def _column_map_for_path(path_ids: list[str], edge_map: dict[tuple[str, str], object]) -> list[dict[str, str]] | None:
    if len(path_ids) < 2:
        return None
    edge = edge_map.get((path_ids[-2], path_ids[-1]))
    if edge is None:
        return None
    return getattr(edge, "column_map", None)


def main() -> int:
    load_dotenv()
    config = load_config()
    force_rest = os.getenv("SMOKE_FORCE_REST", "").strip().lower() in {"1", "true", "yes"}
    depth = min(config.lineage_max_depth, 3)

    rest_provider = OpenMetadataProvider(config.om_host, config.om_token)
    provider = rest_provider
    transport = "rest-only" if force_rest else "rest-only"

    if config.om_mcp_url and not force_rest:
        try:
            mcp = MCPClient(config.om_mcp_url, config.om_token)
            rpc_info = mcp.call_rpc({"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1})
            print("MCP live:", rpc_info.get("result", {}).get("serverInfo", {}))
            print("Tools:", mcp.list_tools())
            provider = MCPMetadataProvider(mcp, rest_provider, depth=depth)
            transport = "mcp"
        except MCPTransportError as exc:
            print(f"MCP probe failed: {exc} -> using REST fallback")
            transport = "rest-fallback"
    elif force_rest:
        print("Skipping MCP probe: SMOKE_FORCE_REST enabled")

    smoke_entity_fqn = os.getenv("SMOKE_ENTITY_FQN", SMOKE_ENTITY_FQN).strip()
    if not smoke_entity_fqn:
        print("SMOKE_ENTITY_FQN must be set to a confirmed FQN from scripts/discover_lineage_entities.py")
        return 1

    print(f"\nTransport: {transport}")
    print(f"Resolving: {smoke_entity_fqn}")

    try:
        asset = provider.resolve_asset(smoke_entity_fqn)
        print(f"Resolved: {asset.name} (id={asset.id})")
    except Exception as exc:
        print(f"Resolve failed: {exc}")
        return 1

    lineage = None
    try:
        if isinstance(provider, MCPMetadataProvider):
            lineage = provider.get_downstream_lineage(asset.id)
        else:
            lineage = provider.get_downstream_lineage(asset.id, depth=depth)
        print(f"Downstream nodes: {len(lineage.nodes)}")
        print(f"Downstream edges: {len(lineage.edges)}")
        for node in lineage.nodes.values():
            print(f"  -> {node.name} ({node.type.value})")
    except Exception as exc:
        print(f"Lineage failed: {exc}")

    change = SchemaChange(
        entity=asset.name,
        change_type=ChangeType.DROP_COLUMN,
        column="legacy_id",
        source_file="migrations/smoke_test.sql",
    )

    records = []
    if lineage and lineage.nodes:
        traversed = LineageTraverser.traverse(asset.id, lineage, depth=depth)
        edge_map = {(edge.from_id, edge.to_id): edge for edge in lineage.edges}
        name_to_id = {node.name: node.id for node in lineage.nodes.values()}
        for downstream_asset, path_names in traversed:
            path_ids = [name_to_id[name] for name in path_names if name in name_to_id]
            column_map = _column_map_for_path(path_ids, edge_map)
            records.append(
                ImpactRulesEngine.evaluate(
                    change=change,
                    asset=downstream_asset,
                    path=path_names,
                    column_map=column_map,
                )
            )

    report = ReportBuilder.build(report_id="smoke-test", changes=[change], records=records)
    markdown = PRCommentRenderer.render(report)

    print("\n-- ImpactReport ------------------------------")
    print(
        json.dumps(
            {
                "highest_severity": report.highest_severity.value,
                "total_affected": report.total_affected,
                "records": len(report.records),
            },
            indent=2,
        )
    )

    print("\n-- Markdown Preview (first 800 chars) --------")
    print(markdown[:800])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
