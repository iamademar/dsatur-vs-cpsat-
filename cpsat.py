"""CP-SAT exact / optimising colouring (Method 2 in the report).

Builds the integer-variable model from the report's Listing 1 and Section 5.2:
  - one integer variable per exam holding its slot,
  - one not-equal constraint per conflict edge,
  - minimise the largest slot index (slots used = that index + 1),
  - warm start from a DSATUR colouring (initial upper bound + solution hint),
  - symmetry breaking by pinning the first vertex to slot 0.

Requires Google OR-Tools. OR-Tools wheels lag the newest CPython, so this
needs a Python 3.11-3.13 virtual environment; see code/README.md.
"""

from __future__ import annotations

import sys
import time

from graphutils import is_proper_colouring, load_graph, num_colours

try:
    from ortools.sat.python import cp_model
except ImportError as exc:  # pragma: no cover - environment guard
    raise ImportError(
        "ortools is not installed. CP-SAT needs a Python 3.11-3.13 virtual "
        "environment with `pip install -r requirements.txt`; see code/README.md."
    ) from exc


def cpsat_colour(
    graph: dict[str, set[str]],
    warm_start: dict[str, int] | None = None,
    upper_bound: int | None = None,
    time_limit_s: float = 20.0,
) -> dict:
    """Solve the colouring as a CP-SAT optimisation problem.

    Returns a dict with keys: colouring, num_colours, status, proven_optimal,
    wall_time.
    """
    vertices = sorted(graph)
    if not vertices:
        return {
            "colouring": {},
            "num_colours": 0,
            "status": "EMPTY",
            "proven_optimal": True,
            "wall_time": 0.0,
        }

    # Upper bound on slots: default to the warm-start colour count, else |V|.
    if upper_bound is None:
        if warm_start:
            upper_bound = num_colours(warm_start)
        else:
            upper_bound = len(vertices)
    ub = max(1, upper_bound)

    model = cp_model.CpModel()
    # One integer variable per exam, domain 0..ub-1.
    x = {v: model.NewIntVar(0, ub - 1, v) for v in vertices}

    # One not-equal constraint per conflict edge (each edge once).
    for u in vertices:
        for w in graph[u]:
            if u < w:  # avoid adding both (u,w) and (w,u)
                model.Add(x[u] != x[w])

    # Symmetry breaking: pin the first vertex to slot 0.
    model.Add(x[vertices[0]] == 0)

    # Objective: minimise the largest slot index used.
    max_slot = model.NewIntVar(0, ub - 1, "max_slot")
    model.AddMaxEquality(max_slot, list(x.values()))
    model.Minimize(max_slot)

    # Warm start hint from DSATUR.
    if warm_start:
        for v in vertices:
            if v in warm_start:
                model.AddHint(x[v], min(warm_start[v], ub - 1))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s

    start = time.perf_counter()
    status = solver.Solve(model)
    wall_time = time.perf_counter() - start

    colouring: dict[str, int] = {}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        colouring = {v: int(solver.Value(x[v])) for v in vertices}

    return {
        "colouring": colouring,
        "num_colours": num_colours(colouring),
        "status": solver.StatusName(status),
        "proven_optimal": status == cp_model.OPTIMAL,
        "wall_time": wall_time,
    }


def _main(argv: list[str]) -> int:
    # Local import so dsatur stays optional if someone only wants the model.
    from dsatur import dsatur_colour

    path = argv[1] if len(argv) > 1 else "datasets/tiny/enrolments.csv"
    graph = load_graph(path)
    warm = dsatur_colour(graph)
    result = cpsat_colour(graph, warm_start=warm, time_limit_s=20.0)
    print(f"dataset:        {path}")
    print(f"vertices:       {len(graph)}")
    print(f"DSATUR colours: {num_colours(warm)}")
    print(f"CP-SAT colours: {result['num_colours']}")
    print(f"status:         {result['status']}")
    print(f"proven optimal: {result['proven_optimal']}")
    print(f"wall time (s):  {result['wall_time']:.3f}")
    print(f"valid:          {is_proper_colouring(graph, result['colouring'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
