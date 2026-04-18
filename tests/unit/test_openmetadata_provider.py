from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest

from src.domain.enums import AssetType
from src.providers.base import AssetNotFoundError
from src.providers.openmetadata_provider import OpenMetadataProvider


class _FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def _http_404(url: str) -> HTTPError:
    return HTTPError(url=url, code=404, msg="Not Found", hdrs=None, fp=None)


def test_resolve_asset_accepts_uuid_id(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    asset_id = "11111111-2222-3333-4444-555555555555"

    def fake_urlopen(req, timeout=10):  # noqa: ANN001
        calls.append(req.full_url)
        if req.full_url.endswith(f"/api/v1/tables/{asset_id}"):
            return _FakeHTTPResponse(
                {
                    "id": asset_id,
                    "fullyQualifiedName": "svc.db.schema.my_table",
                    "entityType": "table",
                    "owner": {"name": "data_eng"},
                    "tags": [{"tagFQN": "Tier.Tier1"}],
                }
            )
        raise _http_404(req.full_url)

    monkeypatch.setattr("src.providers.openmetadata_provider.urlopen", fake_urlopen)

    p = OpenMetadataProvider(host="http://openmetadata:8585", jwt_token="jwt")
    asset = p.resolve_asset(asset_id)

    assert asset.id == asset_id
    assert asset.name == "svc.db.schema.my_table"
    assert asset.type == AssetType.TABLE
    assert asset.owner == "data_eng"
    assert asset.criticality == "Tier1"
    assert any("/api/v1/tables/" in c for c in calls)


def test_resolve_asset_accepts_fully_qualified_name(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    fqn = "svc.db.schema.some_view"

    def fake_urlopen(req, timeout=10):  # noqa: ANN001
        calls.append(req.full_url)
        if req.full_url.endswith("/api/v1/tables/name/svc.db.schema.some_view"):
            return _FakeHTTPResponse(
                {
                    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "fullyQualifiedName": fqn,
                    "entityType": "view",
                    "owner": {"displayName": "BI Team"},
                }
            )
        raise _http_404(req.full_url)

    monkeypatch.setattr("src.providers.openmetadata_provider.urlopen", fake_urlopen)

    p = OpenMetadataProvider(host="http://openmetadata:8585", jwt_token="")
    asset = p.resolve_asset(fqn)

    assert asset.name == fqn
    assert asset.type == AssetType.VIEW
    assert asset.owner == "BI Team"
    assert any("/api/v1/tables/name/" in c for c in calls)


def test_resolve_asset_unknown_raises_asset_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout=10):  # noqa: ANN001
        raise _http_404(req.full_url)

    monkeypatch.setattr("src.providers.openmetadata_provider.urlopen", fake_urlopen)

    p = OpenMetadataProvider(host="http://openmetadata:8585", jwt_token="jwt")
    with pytest.raises(AssetNotFoundError):
        p.resolve_asset("does.not.exist")


def test_get_downstream_lineage_builds_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    asset_id = "11111111-2222-3333-4444-555555555555"
    downstream_id = "99999999-8888-7777-6666-555555555555"

    def fake_urlopen(req, timeout=10):  # noqa: ANN001
        url = req.full_url
        if url.endswith(f"/api/v1/tables/{asset_id}"):
            return _FakeHTTPResponse(
                {
                    "id": asset_id,
                    "fullyQualifiedName": "svc.db.schema.root",
                    "entityType": "table",
                }
            )
        if "/api/v1/lineage/table/" in url:
            return _FakeHTTPResponse(
                {
                    "nodes": [
                        {
                            "id": asset_id,
                            "fullyQualifiedName": "svc.db.schema.root",
                            "entityType": "table",
                        },
                        {
                            "id": downstream_id,
                            "fullyQualifiedName": "svc.db.schema.child",
                            "entityType": "dashboard",
                        },
                    ],
                    "edges": [
                        {
                            "fromEntity": {"id": asset_id, "type": "table"},
                            "toEntity": {"id": downstream_id, "type": "dashboard"},
                            "lineageDetails": {
                                "columnsLineage": [
                                    {"fromColumns": ["a"], "toColumns": ["x"]},
                                    {"fromColumns": ["b"], "toColumns": ["y"]},
                                ]
                            },
                        }
                    ],
                }
            )
        raise _http_404(url)

    monkeypatch.setattr("src.providers.openmetadata_provider.urlopen", fake_urlopen)

    p = OpenMetadataProvider(host="http://openmetadata:8585", jwt_token="jwt")
    g = p.get_downstream_lineage(asset_id, depth=5)

    assert asset_id in g.nodes
    assert downstream_id in g.nodes
    assert g.nodes[downstream_id].type == AssetType.DASHBOARD
    assert len(g.edges) == 1
    assert g.edges[0].from_id == asset_id
    assert g.edges[0].to_id == downstream_id
    assert g.edges[0].column_map == [{"a": "x"}, {"b": "y"}]

