"""E6: derive and freeze the cyber graph of the 10 C2 units from the physical network.

Rule: connect each unit to its k nearest units by transmission-network hop
count (ties broken by lower series-reactance path length, then by bus number),
symmetrize, give every edge weight 1, and verify connectivity and single-link /
single-unit loss tolerance.  k=2 was tried first (declared a priori) and gave a
connected graph that is not tolerant to the loss of one link or unit, so k is
raised to the smallest value that is (recorded in "rejected_k" below).  The
frozen graph is written to artifacts; the C2 case file is read only.
"""

from __future__ import annotations

import heapq
import itertools
import json
from pathlib import Path

import andes
import numpy as np

from run_e0_ieee39 import ARTIFACTS_DIR, PROJECT_ROOT, sha256

CASE = PROJECT_ROOT / "Paper_manuscript" / "cases" / "ieee39_C2_6SG_4GFM.xlsx"
OUT = ARTIFACTS_DIR / "IEEE39_E6_C2_communication_graph.json"


def shortest(adj: dict[int, list[tuple[int, float]]], src: int) -> dict[int, tuple[int, float]]:
    """Dijkstra on (hops, reactance) lexicographic cost."""
    best = {src: (0, 0.0)}
    heap = [(0, 0.0, src)]
    while heap:
        hops, x, u = heapq.heappop(heap)
        if best[u] != (hops, x):
            continue
        for v, xv in adj[u]:
            cand = (hops + 1, x + xv)
            if v not in best or cand < best[v]:
                best[v] = cand
                heapq.heappush(heap, (*cand, v))
    return best


def laplacian(nodes: list[int], edges: set[tuple[int, int]]) -> np.ndarray:
    index = {b: i for i, b in enumerate(nodes)}
    a = np.zeros((len(nodes), len(nodes)))
    for u, v in edges:
        a[index[u], index[v]] = a[index[v], index[u]] = 1.0
    return np.diag(a.sum(1)) - a


def connected(nodes: list[int], edges: set[tuple[int, int]]) -> bool:
    if len(nodes) <= 1:
        return True
    return int(np.sum(np.linalg.eigvalsh(laplacian(nodes, edges)) < 1e-9)) == 1


def main() -> int:
    system = andes.load(str(CASE), setup=True, default_config=True, no_output=True)
    adj: dict[int, list[tuple[int, float]]] = {int(b): [] for b in system.Bus.idx.v}
    for b1, b2, x in zip(system.Line.bus1.v, system.Line.bus2.v, system.Line.x.v):
        adj[int(b1)].append((int(b2), float(x)))
        adj[int(b2)].append((int(b1), float(x)))
    sg = [int(b) for b in system.GENROU.bus.v]
    gfm = [int(b) for b in system.REGF1.bus.v]
    nodes = sorted(sg + gfm)
    dist = {u: shortest(adj, u) for u in nodes}
    rejected: dict[str, dict[str, bool]] = {}
    for k_nearest in range(2, len(nodes)):
        edges: set[tuple[int, int]] = set()
        for u in nodes:
            near = sorted((v for v in nodes if v != u), key=lambda v: (*dist[u][v], v))[:k_nearest]
            edges.update(tuple(sorted((u, v))) for v in near)
        link_loss = {f"{u}-{v}": connected(nodes, edges - {(u, v)}) for u, v in sorted(edges)}
        unit_loss = {str(n): connected([m for m in nodes if m != n],
                                       {e for e in edges if n not in e}) for n in nodes}
        if all(link_loss.values()) and all(unit_loss.values()):
            break
        rejected[str(k_nearest)] = {"edges": len(edges), "links_not_tolerated": [k for k, v in link_loss.items() if not v],
                                    "units_not_tolerated": [k for k, v in unit_loss.items() if not v]}
    lap = laplacian(nodes, edges)
    eig = np.linalg.eigvalsh(lap)
    result = {
        "rule": f"{k_nearest} nearest units by (hop count, series reactance, bus number), symmetrized, unit weights",
        "case_sha256": sha256(CASE), "nodes_bus": nodes, "sg_buses": sg, "gfm_buses": gfm,
        "k_nearest": k_nearest, "rejected_k": rejected, "edges": sorted(edges), "weights": 1.0,
        "degree": {str(n): int(sum(n in e for e in edges)) for n in nodes},
        "laplacian_eigenvalues": eig.tolist(), "algebraic_connectivity": float(eig[1]),
        "connected": bool(eig[1] > 1e-9),
        "survives_single_link_loss": link_loss, "survives_single_unit_loss": unit_loss,
        "all_single_link_losses_ok": all(link_loss.values()),
        "all_single_unit_losses_ok": all(unit_loss.values()),
        "physical_hop_distance": {f"{u}-{v}": dist[u][v][0] for u, v in itertools.combinations(nodes, 2)},
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "k_nearest", "rejected_k", "edges", "degree", "algebraic_connectivity", "connected",
        "all_single_link_losses_ok", "all_single_unit_losses_ok")}, indent=1))
    print({k: v for k, v in link_loss.items() if not v}, {k: v for k, v in unit_loss.items() if not v})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
