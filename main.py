from __future__ import annotations

import logging
import os
import re
from typing import Any

import click
from dotenv import load_dotenv

from src.adapters.github_adapter import GitHubAdapter
from src.adapters.mcp_client import MCPClient
from src.config import load_config
from src.domain.enums import ChangeType, Severity
from src.domain.models import ImpactRecord, SchemaChange
from src.engine.renderer import PRCommentRenderer
from src.engine.reporter import ReportBuilder
from src.engine.rules import ImpactRulesEngine
from src.engine.traverser import LineageTraverser
from src.llm.summarizer import LLMSummarizer
from src.llm.validator import SummaryValidator
from src.parser.fixture_loader import FixtureLoader, FixtureNotFoundError, FixtureValidationError
from src.providers.jwt_auth import JWTAuthProvider
from src.providers.mcp_provider import MCPMetadataProvider
from src.providers.mock_provider import MockMetadataProvider
from src.providers.openmetadata_provider import OpenMetadataProvider
from src.providers.resolver import AssetResolver

logger = logging.getLogger("metaguard")
load_dotenv()


def _effective_sandbox_depth(depth: int) -> int:
    # The current sandbox rejects downstreamDepth values above 3.
    return min(depth, 3)


def _schema_change_from_dict(payload: dict[str, Any]) -> SchemaChange:
    return SchemaChange(
        entity=payload["entity"],
        change_type=ChangeType(payload["change_type"]),
        column=payload.get("column"),
        old_type=payload.get("old_type"),
        new_type=payload.get("new_type"),
        source_file=payload.get("source_file"),
    )


def _severity_rank(sev: Severity) -> int:
    return {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.CRITICAL: 3}[sev]


def _confidence_rank(conf: str) -> int:
    # Confidence is an enum in records; compare via value ordering.
    return {"LOW": 0, "MEDIUM": 1, "HIGH": 2}.get(conf, 0)


def _asset_type_rank(asset_type: str) -> int:
    # Prefer tables/views/models first, dashboards next, pipelines last (matches fixture ordering).
    order = {
        "TABLE": 0,
        "VIEW": 1,
        "MODEL": 2,
        "FEATURE_STORE": 3,
        "DASHBOARD": 4,
        "PIPELINE": 5,
    }
    return order.get(asset_type, 99)


def _sort_records(records: list[ImpactRecord]) -> list[ImpactRecord]:
    return sorted(
        records,
        key=lambda r: (
            -_severity_rank(r.severity),
            -_confidence_rank(r.confidence.value),
            _asset_type_rank(r.asset_type.value),
            len(r.path),
            r.asset_id,
        ),
    )


def _record_to_dict(r: ImpactRecord) -> dict[str, Any]:
    return {
        "asset_id": r.asset_id,
        "asset_name": r.asset_name,
        "asset_type": r.asset_type.value,
        "severity": r.severity.value,
        "confidence": r.confidence.value,
        "reason": r.reason,
        "path": r.path,
    }


def report_to_fixture_dict(report_id: str, changes: list[SchemaChange], records: list[ImpactRecord]) -> dict[str, Any]:
    report = ReportBuilder.build(report_id=report_id, changes=changes, records=_sort_records(records))
    return {
        "id": report.id,
        "highest_severity": report.highest_severity.value,
        "total_affected": report.total_affected,
        "records": [_record_to_dict(r) for r in report.records],
    }


def _collect_fixture_records(fixture_id: str, depth: int = 5) -> tuple[list[SchemaChange], list[ImpactRecord]]:
    loader = FixtureLoader.default()
    diff_payload = loader.load_diff(fixture_id)
    changes = [_schema_change_from_dict(c) for c in diff_payload.get("changes", [])]

    provider = MockMetadataProvider(fixture_id)
    records: list[ImpactRecord] = []

    for change in changes:
        root_asset, _ = AssetResolver.resolve(change, provider)
        if root_asset is None:
            # Graceful degradation: no resolvable root means no downstream traversal.
            logger.warning("Unable to resolve changed entity '%s'; skipping downstream traversal", change.entity)
            continue

        graph = provider.get_downstream_lineage(root_asset.id)
        downstream = LineageTraverser.traverse(root_id=root_asset.id, graph=graph, depth=depth)
        if not downstream:
            logger.warning("Empty downstream lineage for root asset '%s' (%s)", root_asset.name, root_asset.id)
            continue

        name_to_id = {a.name: a.id for a in graph.nodes.values()}
        edge_map = {(e.from_id, e.to_id): e for e in graph.edges}

        for asset, path_names in downstream:
            if len(path_names) < 2:
                continue
            prev_name = path_names[-2]
            prev_id = name_to_id.get(prev_name)
            column_map = None
            if prev_id is not None:
                edge = edge_map.get((prev_id, asset.id))
                if edge is not None:
                    column_map = edge.column_map

            records.append(ImpactRulesEngine.evaluate(change=change, asset=asset, path=path_names, column_map=column_map))

    return changes, records


def run_fixture(fixture_id: str, depth: int = 5) -> dict[str, Any]:
    changes, records = _collect_fixture_records(fixture_id=fixture_id, depth=depth)
    return report_to_fixture_dict(report_id=fixture_id, changes=changes, records=records)


def render_fixture_markdown(fixture_id: str) -> str:
    changes, records = _collect_fixture_records(fixture_id=fixture_id)
    report = ReportBuilder.build(report_id=fixture_id, changes=changes, records=_sort_records(records))
    markdown = PRCommentRenderer.render(report)
    report_json = run_fixture(fixture_id)

    if str(os.getenv("ENABLE_LLM_SUMMARY", "false")).lower() == "true":
        try:
            summarizer = LLMSummarizer()
            improved = summarizer.summarize(report_json=report_json, markdown=markdown)
            if SummaryValidator().validate(report_json, improved):
                return improved
            logger.warning("LLM summary failed validation. Using deterministic markdown.")
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.warning("LLM summary failed: %s. Using deterministic markdown.", exc)
    return markdown


def smoke_openmetadata(host: str, token: str, asset_ref: str, depth: int) -> None:
    depth = _effective_sandbox_depth(depth)
    provider = OpenMetadataProvider(host=host, jwt_token=token)
    root = provider.resolve_asset(asset_ref)
    graph = provider.get_downstream_lineage(root.id, depth=depth)
    if len(graph.nodes) <= 1:
        raise SystemExit("Smoke test failed: downstream lineage is empty.")

    click.echo(f"Resolved root asset: {root.name} ({root.id}) [{root.type.value}]")
    click.echo(f"Downstream graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")


def render_sandbox_markdown(
    asset_ref: str, transport: str, depth: int, file_paths: list[str]
) -> str:
    depth = _effective_sandbox_depth(depth)
    cfg = load_config()
    rest_provider = OpenMetadataProvider(host=cfg.om_host, jwt_token=cfg.om_token)
    provider = rest_provider
    if transport == "mcp":
        mcp_client = MCPClient(mcp_url=cfg.om_mcp_url, jwt_token=cfg.om_token)
        provider = MCPMetadataProvider(mcp_client=mcp_client, rest_fallback=rest_provider, depth=depth)

    # 1. Resolve root asset
    logger.info("Resolving root asset: %s", asset_ref)
    asset = provider.resolve_asset(asset_ref)

    # 2. Get lineage
    logger.info("Fetching downstream lineage for asset: %s", asset.id)
    graph = provider.get_downstream_lineage(asset.id, depth=depth)

    # 3. Get changes
    from src.parser.diff_parser import DiffParser
    changes = []
    for path in file_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read()
                parsed = DiffParser.parse(content)
                logger.info("Parsed %d changes from %s", len(parsed), path)
                changes.extend(parsed)

    if not changes:
        # Fallback for demo: assume a DROP_COLUMN on the root asset
        logger.info("No SQL changes parsed from file_paths; using demo DROP_COLUMN on root asset")
        changes.append(
            SchemaChange(
                entity=asset.name,
                change_type=ChangeType.DROP_COLUMN,
                column="legacy_id",
                source_file="demo_migration.sql",
            )
        )

    # 4. Evaluate impact
    records = []
    if graph and graph.nodes:
        logger.info("Traversing lineage graph (nodes=%d, edges=%d)", len(graph.nodes), len(graph.edges))
        traversed = LineageTraverser.traverse(asset.id, graph, depth=depth)
        edge_map = {(edge.from_id, edge.to_id): edge for edge in graph.edges}
        name_to_id = {node.name: node.id for node in graph.nodes.values()}

        for downstream_asset, path_names in traversed:
            path_ids = [name_to_id[name] for name in path_names if name in name_to_id]
            column_map = None
            if len(path_ids) >= 2:
                edge = edge_map.get((path_ids[-2], path_ids[-1]))
                if edge:
                    column_map = edge.column_map

            for change in changes:
                records.append(
                    ImpactRulesEngine.evaluate(
                        change=change,
                        asset=downstream_asset,
                        path=path_names,
                        column_map=column_map,
                    )
                )

    # 5. Build report and render
    logger.info("Building impact report with %d records", len(records))
    report = ReportBuilder.build(report_id="sandbox-run", changes=changes, records=_sort_records(records))
    markdown = PRCommentRenderer.render(report)
    report_json = report_to_fixture_dict("sandbox-run", changes, records)

    # 6. Optional LLM Summary
    if str(os.getenv("ENABLE_LLM_SUMMARY", "false")).lower() == "true":
        try:
            summarizer = LLMSummarizer()
            improved = summarizer.summarize(report_json=report_json, markdown=markdown)
            if SummaryValidator().validate(report_json, improved):
                logger.info("Using LLM-improved summary")
                return improved
            logger.warning("LLM summary failed validation. Using deterministic markdown.")
        except Exception as exc:
            logger.warning("LLM summary failed: %s. Using deterministic markdown.", exc)

    return markdown


_FIXTURE_ID_RE = re.compile(r"^F[1-5]$")


def _parse_changed_files(changed_files: str | None) -> tuple[str | None, list[str]]:
    """
    Returns (fixture_id, file_paths).

    - If `changed_files` is a fixture ID like "F1", returns ("F1", []).
    - Else interprets it as a comma-separated list of file paths.
    """
    if not changed_files:
        return None, []
    raw = changed_files.strip()
    if _FIXTURE_ID_RE.match(raw):
        return raw, []
    paths = [p.strip() for p in raw.split(",") if p.strip()]
    return None, paths


@click.command()
@click.option("--mock", is_flag=True, default=False, help="Use mock fixture-driven provider (Phase 1).")
@click.option("--mode", type=click.Choice(["mock", "sandbox"]), default=None, help="Execution mode.")
@click.option("--transport", type=click.Choice(["rest", "mcp"]), default="mcp", help="Sandbox metadata transport.")
@click.option("--om-host", type=str, default=None, envvar="OM_HOST", help="OpenMetadata host, e.g. http://openmetadata:8585")
@click.option("--om-token", type=str, default=None, help="OpenMetadata JWT token (or set OM_JWT_TOKEN)")
@click.option("--om-asset", type=str, default=None, help="Asset reference (UUID or fully qualified name) for Phase 2 smoke test")
@click.option("--pr-number", type=int, default=None, help="Pull request number to post a comment to (Phase 3).")
@click.option("--repo", type=str, default=None, help="GitHub repo owner/name for PR mode.")
@click.option("--output", type=click.Choice(["stdout", "github"]), default="stdout", help="Output destination.")
@click.option(
    "--changed-files",
    type=str,
    default=None,
    help="Fixture ID (F1..F5) in --mock mode, or comma-separated file paths.",
)
@click.option(
    "--fixture",
    type=str,
    default=None,
    hidden=True,
    help="Deprecated alias for --changed-files when using mock fixtures.",
)
@click.option("--depth", type=int, default=5, show_default=True, help="Max downstream traversal depth for Phase 2 smoke test")
def main(
    mock: bool,
    mode: str | None,
    transport: str,
    om_host: str | None,
    om_token: str | None,
    om_asset: str | None,
    pr_number: int | None,
    repo: str | None,
    output: str,
    changed_files: str | None,
    fixture: str | None,
    depth: int,
) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    fixture_id_from_changed, file_paths = _parse_changed_files(changed_files)

    effective_mode = mode or ("mock" if mock else None)

    if effective_mode == "mock":
        fixture_id = fixture_id_from_changed or fixture
        if not fixture_id:
            raise SystemExit("--changed-files is required with --mock (use F1..F5).")
        if file_paths:
            raise SystemExit("In --mock mode, --changed-files must be a fixture id (F1..F5), not file paths.")

        logger.info("Running MetaGuard in mock mode with fixture '%s'", fixture_id)
        try:
            body = render_fixture_markdown(fixture_id)
        except (FixtureNotFoundError, FixtureValidationError) as exc:
            raise SystemExit(str(exc)) from exc
        if output == "github" and pr_number is not None:
            gh = GitHubAdapter.from_env() if repo is None else GitHubAdapter(github_token=os.getenv("GITHUB_TOKEN", ""), repo=repo)
            gh.post_pr_comment(pr_number=pr_number, body=body)
            logger.info("Posted MetaGuard report to PR #%s", pr_number)
            return

        click.echo(body)
        logger.info("Rendered MetaGuard markdown report to stdout")
        return

    if effective_mode == "sandbox" and om_asset:
        logger.info("Running MetaGuard in sandbox mode for asset '%s'", om_asset)
        try:
            body = render_sandbox_markdown(
                asset_ref=om_asset,
                transport=transport,
                depth=depth,
                file_paths=file_paths,
            )
        except Exception as exc:
            logger.error("Sandbox run failed: %s", exc)
            raise SystemExit(f"Sandbox run failed: {exc}") from exc

        if output == "github" and pr_number is not None:
            gh = (
                GitHubAdapter.from_env()
                if repo is None
                else GitHubAdapter(github_token=os.getenv("GITHUB_TOKEN", ""), repo=repo)
            )
            gh.post_pr_comment(pr_number=pr_number, body=body)
            logger.info("Posted MetaGuard report to PR #%s", pr_number)
            return

        click.echo(body)
        logger.info("Rendered MetaGuard markdown report to stdout")
        return

    # Legacy Phase 2 path: explicit host + token.
    if om_host and om_asset:
        token = om_token or JWTAuthProvider().get_token()
        smoke_openmetadata(host=om_host, token=token, asset_ref=om_asset, depth=depth)
        return

    raise SystemExit(
        "Usage: --mode mock --changed-files F1..F5 OR --mode sandbox --transport mcp|rest --om-asset <fqn>."
    )


if __name__ == "__main__":
    main()
