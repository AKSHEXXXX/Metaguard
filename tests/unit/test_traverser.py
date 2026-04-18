from __future__ import annotations

from src.domain.models import LineageEdge, LineageGraph
from src.engine.traverser import LineageTraverser
from src.providers.mock_provider import MockMetadataProvider


def test_traverse_f1_returns_four_downstream_assets_with_paths() -> None:
    provider = MockMetadataProvider("F1")
    graph = provider.get_downstream_lineage("t1")

    results = LineageTraverser.traverse(root_id="t1", graph=graph, depth=10)
    by_id = {asset.id: path for asset, path in results}

    assert set(by_id.keys()) == {"t2", "t3", "d1", "p1"}
    assert by_id["t2"] == ["analytics.customers", "stg_customers"]
    assert by_id["t3"] == ["analytics.customers", "stg_customers", "mart_customer_360"]
    assert by_id["d1"] == ["analytics.customers", "stg_customers", "mart_customer_360", "Revenue by Customer"]
    assert by_id["p1"] == ["analytics.customers", "nightly_customer_rollup"]


def test_traverse_avoids_cycles() -> None:
    provider = MockMetadataProvider("F1")
    g = provider.get_downstream_lineage("t1")
    graph = LineageGraph(nodes=g.nodes, edges=[*g.edges, LineageEdge(from_id="d1", to_id="t1", column_map=None)])

    results = LineageTraverser.traverse(root_id="t1", graph=graph, depth=10)
    assert len(results) == 4
