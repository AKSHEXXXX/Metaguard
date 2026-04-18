from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

from src.domain.enums import AssetType
from src.domain.models import Asset, LineageEdge, LineageGraph
from src.providers.base import AssetNotFoundError, MetadataProvider


_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _normalize_host(host: str) -> str:
    host = host.strip()
    if not host:
        raise ValueError("host must be non-empty")
    if not host.startswith(("http://", "https://")):
        host = "https://" + host
    if not host.endswith("/"):
        host += "/"
    return host


def _asset_type_from_om_entity(entity_type: str | None) -> AssetType:
    if not entity_type:
        return AssetType.TABLE
    t = entity_type.strip().lower()
    return {
        "table": AssetType.TABLE,
        "view": AssetType.VIEW,
        "dashboard": AssetType.DASHBOARD,
        "pipeline": AssetType.PIPELINE,
        "mlmodel": AssetType.MODEL,
        "model": AssetType.MODEL,
        "featurestore": AssetType.FEATURE_STORE,
        "feature_store": AssetType.FEATURE_STORE,
        "feature-store": AssetType.FEATURE_STORE,
    }.get(t, AssetType.TABLE)


def _om_entity_from_asset_type(asset_type: AssetType) -> str:
    return {
        AssetType.TABLE: "table",
        AssetType.VIEW: "table",
        AssetType.DASHBOARD: "dashboard",
        AssetType.PIPELINE: "pipeline",
        AssetType.MODEL: "mlmodel",
        AssetType.FEATURE_STORE: "featurestore",
    }.get(asset_type, "table")


def _extract_owner(payload: dict[str, Any]) -> str | None:
    owner = payload.get("owner")
    if isinstance(owner, dict):
        return owner.get("displayName") or owner.get("name")
    return None


def _extract_criticality(payload: dict[str, Any]) -> str | None:
    # OpenMetadata commonly encodes tier/criticality as tags like "Tier.Tier1".
    tags = payload.get("tags")
    if isinstance(tags, list):
        for tag in tags:
            if not isinstance(tag, dict):
                continue
            tag_fqn = tag.get("tagFQN") or tag.get("tagFqn") or tag.get("name")
            if isinstance(tag_fqn, str) and tag_fqn.startswith("Tier."):
                return tag_fqn.split(".", 1)[1]
    return payload.get("criticality") if isinstance(payload.get("criticality"), str) else None


def _extract_domain(payload: dict[str, Any]) -> str | None:
    domain = payload.get("domain")
    if isinstance(domain, dict):
        return domain.get("fullyQualifiedName") or domain.get("name")
    if isinstance(domain, str):
        return domain
    return None


def _asset_name(payload: dict[str, Any]) -> str:
    return (
        payload.get("fullyQualifiedName")
        or payload.get("fullyQualifiedNameHash")
        or payload.get("name")
        or payload.get("displayName")
        or ""
    )


@dataclass(frozen=True)
class _EntitySpec:
    # OM collection path segment, e.g. "tables"
    collection: str
    # OM lineage entity path segment, e.g. "table"
    lineage_entity: str
    asset_type: AssetType


_ENTITY_SPECS: list[_EntitySpec] = [
    _EntitySpec(collection="tables", lineage_entity="table", asset_type=AssetType.TABLE),
    _EntitySpec(collection="dashboards", lineage_entity="dashboard", asset_type=AssetType.DASHBOARD),
    _EntitySpec(collection="pipelines", lineage_entity="pipeline", asset_type=AssetType.PIPELINE),
    _EntitySpec(collection="mlmodels", lineage_entity="mlmodel", asset_type=AssetType.MODEL),
]


class OpenMetadataProvider(MetadataProvider):
    def __init__(self, host: str, jwt_token: str) -> None:
        self._host = _normalize_host(host)
        self._jwt_token = jwt_token.strip()

    def resolve_asset(self, ref: str) -> Asset:
        ref = ref.strip()
        if not ref:
            raise AssetNotFoundError(ref)

        is_uuid = bool(_UUID_RE.match(ref))
        for spec in _ENTITY_SPECS:
            try:
                if is_uuid:
                    payload = self._get_json(f"/api/v1/{spec.collection}/{quote(ref)}")
                else:
                    payload = self._get_json(f"/api/v1/{spec.collection}/name/{quote(ref, safe='')}")
                return Asset(
                    id=str(payload.get("id") or ref),
                    name=_asset_name(payload) or ref,
                    type=_asset_type_from_om_entity(payload.get("entityType") or payload.get("type"))
                    if (payload.get("entityType") or payload.get("type"))
                    else spec.asset_type,
                    owner=_extract_owner(payload),
                    criticality=_extract_criticality(payload),
                    domain=_extract_domain(payload),
                )
            except HTTPError as e:
                if e.code == 404:
                    continue
                raise

        raise AssetNotFoundError(ref)

    def get_downstream_lineage(self, root_asset_id: str, depth: int = 5) -> LineageGraph:
        root_asset = self.resolve_asset(root_asset_id)
        entity = _om_entity_from_asset_type(root_asset.type)

        payload = self._get_json(
            f"/api/v1/lineage/{quote(entity)}/{quote(root_asset.id)}"
            f"?upstreamDepth=0&downstreamDepth={int(depth)}"
        )

        nodes: dict[str, Asset] = {root_asset.id: root_asset}

        for n in payload.get("nodes", []) or []:
            if not isinstance(n, dict):
                continue
            node_id = n.get("id")
            if not isinstance(node_id, str):
                continue
            nodes[node_id] = Asset(
                id=node_id,
                name=(n.get("fullyQualifiedName") or n.get("name") or node_id),
                type=_asset_type_from_om_entity(n.get("entityType") or n.get("type")),
                owner=None,
                criticality=None,
                domain=None,
            )

        edges: list[LineageEdge] = []
        raw_edges = payload.get("edges", []) or payload.get("downstreamEdges", []) or []
        for e in raw_edges:
            if not isinstance(e, dict):
                continue
            from_ent = e.get("fromEntity") or {}
            to_ent = e.get("toEntity") or {}
            from_id = from_ent.get("id") if isinstance(from_ent, dict) else from_ent
            to_id = to_ent.get("id") if isinstance(to_ent, dict) else to_ent
            if not (isinstance(from_id, str) and isinstance(to_id, str)):
                continue

            column_map = self._extract_column_map(e.get("lineageDetails") or {})
            edges.append(LineageEdge(from_id=from_id, to_id=to_id, column_map=column_map))

        return LineageGraph(nodes=nodes, edges=edges)

    def _get_json(self, path: str) -> dict[str, Any]:
        url = urljoin(self._host, path.lstrip("/"))
        headers = {"Accept": "application/json"}
        if self._jwt_token:
            headers["Authorization"] = f"Bearer {self._jwt_token}"
        req = Request(url=url, headers=headers, method="GET")
        with urlopen(req, timeout=10) as resp:  # nosec - tests mock this; prod host is user-supplied
            raw = resp.read()
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise TypeError(f"Expected JSON object from OpenMetadata, got {type(data)}")
        return data

    @staticmethod
    def _extract_column_map(lineage_details: dict[str, Any]) -> list[dict[str, str]] | None:
        columns_lineage = lineage_details.get("columnsLineage")
        if not isinstance(columns_lineage, list) or not columns_lineage:
            return None

        out: list[dict[str, str]] = []
        for item in columns_lineage:
            if not isinstance(item, dict):
                continue
            from_cols = item.get("fromColumns") or []
            to_cols = item.get("toColumns") or []
            if not (isinstance(from_cols, list) and isinstance(to_cols, list)):
                continue
            for fc in from_cols:
                if not isinstance(fc, str):
                    continue
                for tc in to_cols:
                    if not isinstance(tc, str):
                        continue
                    out.append({fc: tc})
        return out or None
