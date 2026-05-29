"""Shared utilities for the exam-timetabling comparison.

Pure standard library so it runs on any Python 3 install. Provides:
  - loading the enrolment CSVs committed under datasets/
  - deriving the conflict graph from enrolments
  - basic graph statistics (the descriptors used in the report)
  - validation of a colouring (the "validity" metric from the report)

The conflict graph is the same one described in datasets/README.md: two exams
conflict (share an edge) iff at least one student is enrolled in both.
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from itertools import combinations


def load_enrolments(csv_path: str) -> dict[str, list[str]]:
    """Read a two-column enrolments.csv and group exams by student.

    Returns {student_id: [exam_id, ...]}.
    """
    by_student: dict[str, list[str]] = defaultdict(list)
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            by_student[row["student_id"]].append(row["exam_id"])
    return dict(by_student)


def build_conflict_graph(enrolments: dict[str, list[str]]) -> dict[str, set[str]]:
    """Derive the undirected conflict graph as an adjacency map.

    Every pair of exams a single student takes becomes a conflict edge. Exams
    with no shared students still appear as isolated vertices (degree 0), which
    is the case examined in the report's "isolated exams" example.
    """
    graph: dict[str, set[str]] = defaultdict(set)
    for exams in enrolments.values():
        for exam in exams:
            graph.setdefault(exam, set())  # ensure isolated exams are vertices
        for u, v in combinations(sorted(set(exams)), 2):
            graph[u].add(v)
            graph[v].add(u)
    return dict(graph)


def load_graph(csv_path: str) -> dict[str, set[str]]:
    """Convenience: CSV path straight to a conflict graph."""
    return build_conflict_graph(load_enrolments(csv_path))


def graph_stats(graph: dict[str, set[str]]) -> dict:
    """Return the descriptors the report uses to characterise an instance."""
    n = len(graph)
    degrees = [len(neighbours) for neighbours in graph.values()]
    n_edges = sum(degrees) // 2
    max_possible = n * (n - 1) / 2 if n > 1 else 1
    density = n_edges / max_possible if max_possible else 0.0
    return {
        "n_vertices": n,
        "n_edges": n_edges,
        "density": density,
        "max_degree": max(degrees) if degrees else 0,
        "avg_degree": (sum(degrees) / n) if n else 0.0,
    }


def is_proper_colouring(graph: dict[str, set[str]], colouring: dict[str, int]) -> bool:
    """True iff no edge has both endpoints assigned the same colour."""
    for u, neighbours in graph.items():
        if u not in colouring:
            return False
        for v in neighbours:
            if colouring.get(v) == colouring[u]:
                return False
    return True


def num_colours(colouring: dict[str, int]) -> int:
    """Number of distinct colours (time slots) used."""
    return len(set(colouring.values())) if colouring else 0


def greedy_clique_lower_bound(graph: dict[str, set[str]]) -> int:
    """A fast greedy estimate of the largest clique size.

    Returns a *lower bound* on the clique number omega(G), which is itself a
    lower bound on the chromatic number (chi(G) >= omega(G), the bound stated
    in the report's Section 2). Greedy and therefore not guaranteed to find the
    maximum clique, so the true chromatic number may be higher than this value.

    Strategy: seed from the highest-degree vertex, then repeatedly add the
    candidate (a vertex adjacent to everything chosen so far) with the most
    connections to the remaining candidates.
    """
    if not graph:
        return 0
    # Seed from the highest-degree vertex (ties broken alphabetically).
    seed = max(sorted(graph), key=lambda v: len(graph[v]))
    clique = {seed}
    candidates = set(graph[seed])
    while candidates:
        # Pick the candidate adjacent to the most other candidates.
        best = max(
            sorted(candidates),
            key=lambda v: len(graph[v] & candidates),
        )
        clique.add(best)
        # Keep only candidates still adjacent to every clique member.
        candidates = (candidates & graph[best]) - clique
    return len(clique)


def generate_random_conflict_graph(
    n_vertices: int, density: float, seed: int = 0
) -> dict[str, set[str]]:
    """Generate a random (Erdos-Renyi) conflict graph at a target density.

    This is a *synthetic random* graph, distinct from the enrolment-derived
    datasets: it has no cohort/clique structure and exists only to probe the
    density axis in isolation (used by the notebook's density sweep). Each
    possible edge is included independently with probability `density`.

    Vertices are named V000, V001, ... to keep them distinct from the
    department-coded exam IDs in the real datasets.
    """
    rng = random.Random(seed)
    vertices = [f"V{i:03d}" for i in range(n_vertices)]
    graph: dict[str, set[str]] = {v: set() for v in vertices}
    for i in range(n_vertices):
        for j in range(i + 1, n_vertices):
            if rng.random() < density:
                graph[vertices[i]].add(vertices[j])
                graph[vertices[j]].add(vertices[i])
    return graph
