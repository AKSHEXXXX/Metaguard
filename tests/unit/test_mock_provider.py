from __future__ import annotations

import pytest


def test_mock_provider_module_imports() -> None:
    mod = pytest.importorskip("src.providers.mock_provider")
    assert mod is not None


def test_mock_provider_f1_contract_placeholder() -> None:
    mod = pytest.importorskip("src.providers.mock_provider")

    provider_cls = getattr(mod, "MockMetadataProvider", None)
    err_cls = getattr(mod, "AssetNotFoundError", None)

    if provider_cls is None or err_cls is None:
        pytest.skip("MockMetadataProvider/AssetNotFoundError not implemented yet")

    from src.domain.models import Asset, LineageGraph

    provider = provider_cls("F1")

    graph = provider.get_downstream_lineage("t1")
    assert isinstance(graph, LineageGraph)

    asset = provider.resolve_asset("analytics.customers")
    assert isinstance(asset, Asset)

    with pytest.raises(err_cls):
        provider.resolve_asset("does.not.exist")
