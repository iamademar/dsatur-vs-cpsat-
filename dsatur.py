"""DSATUR graph-colouring heuristic (Method 1 in the report).

DSATUR ("degree of saturation", Brelaz, 1979) colours vertices greedily,
always taking the most constrained uncoloured vertex next. The saturation
degree of a vertex is the number of distinct colours already used by its
neighbours.

Selection rule (matching the report's Section 4):
    1. Start with every vertex uncoloured.
    2. Repeatedly pick the uncoloured vertex with the highest saturation
       degree, breaking ties by highest ordinary degree, then alphabetically.
    3. Assign it the smallest colour not used by any coloured neighbour.
    4. Update and repeat until all vertices are coloured.

Pure standard library: runs on any Python 3 install.
"""

from __future__ import annotations

import sys

from graphutils import is_proper_colouring, load_graph, num_colours


def dsatur_colour(graph: dict[str, set[str]]) -> dict[str, int]:
    """Colour the graph with DSATUR. Returns {vertex: colour_int}."""
    colouring: dict[str, int] = {}
    degree = {v: len(neighbours) for v, neighbours in graph.items()}
    # saturation[v] = set of colours currently used by v's neighbours
    neighbour_colours: dict[str, set[int]] = {v: set() for v in graph}

    uncoloured = set(graph)
    while uncoloured:
        # Highest saturation, then highest degree, then alphabetical (min name).
        # max() with a key that negates the name would mis-order strings, so we
        # pick by (saturation, degree) max and resolve the name tie with min().
        best_key = max(
            (len(neighbour_colours[v]), degree[v]) for v in uncoloured
        )
        candidates = [
            v
            for v in uncoloured
            if (len(neighbour_colours[v]), degree[v]) == best_key
        ]
        vertex = min(candidates)  # alphabetical tie-break

        # Smallest colour not used by a coloured neighbour.
        used = {colouring[n] for n in graph[vertex] if n in colouring}
        colour = 0
        while colour in used:
            colour += 1
        colouring[vertex] = colour

        # Update saturation of uncoloured neighbours.
        for n in graph[vertex]:
            if n in uncoloured:
                neighbour_colours[n].add(colour)
        uncoloured.discard(vertex)

    return colouring


def _main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else "datasets/tiny/enrolments.csv"
    graph = load_graph(path)
    colouring = dsatur_colour(graph)
    print(f"dataset:        {path}")
    print(f"vertices:       {len(graph)}")
    print(f"colours used:   {num_colours(colouring)}")
    print(f"valid:          {is_proper_colouring(graph, colouring)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
