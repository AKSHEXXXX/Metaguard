from __future__ import annotations

from collections import deque

from src.domain.models import Asset, LineageGraph


class LineageTraverser:
    @staticmethod
    def traverse(root_id: str, graph: LineageGraph, depth: int) -> list[tuple[Asset, list[str]]]:
        if root_id not in graph.nodes:
            return []
        if depth <= 0:
            return []

        outgoing: dict[str, list[str]] = {}
        for edge in graph.edges:
            outgoing.setdefault(edge.from_id, []).append(edge.to_id)

        results: list[tuple[Asset, list[str]]] = []
        visited: set[str] = {root_id}
        q: deque[tuple[str, list[str]]] = deque()
        q.append((root_id, [graph.nodes[root_id].name]))

        while q:
            current_id, path_names = q.popleft()
            current_depth = len(path_names) - 1
            if current_depth >= depth:
                continue

            for nxt in outgoing.get(current_id, []):
                if nxt in visited:
                    continue
                visited.add(nxt)
                nxt_asset = graph.nodes.get(nxt)
                if nxt_asset is None:
                    continue
                nxt_path = [*path_names, nxt_asset.name]
                results.append((nxt_asset, nxt_path))
                q.append((nxt, nxt_path))

        return results
