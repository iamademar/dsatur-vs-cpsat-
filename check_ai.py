"""Score an AI assistant's exam-timetable answer against the same conflict
graph the algorithms use.

The AI (ChatGPT or Claude) is given the same ``enrolments.csv`` that DSATUR and
CP-SAT receive, so for a fair comparison this script derives the conflict graph
from that identical CSV via ``graphutils`` -- nothing about the input differs
between the AI and the algorithms. The AI's reply is saved as a JSON object
mapping every exam_id to an integer slot; this script validates it and reports
the four metrics the report's "Optional Method 3" section asks for:

    1. validity  -- is the colouring proper (no two conflicting exams share a slot)?
    2. colours   -- how many slots did it use (compare against DSATUR / CP-SAT)?
    3. coverage  -- did it assign every exam exactly once (AIs silently drop some)?
    4. gap to LB -- colours minus the greedy clique lower bound.

Usage (run from code/):
    python check_ai.py <scenario> <ai_answer.json>
    python check_ai.py tiny ai_tiny.json

The JSON file should contain exactly what the AI returned, e.g.
    {"COMP101": 0, "COMP104": 1, "COMP201": 2, ...}
Slot values may be ints or numeric strings ("0"); both are accepted.
"""

import json
import os
import sys

import graphutils

DATASETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets")


def load_ai_colouring(path: str) -> dict[str, int]:
    """Read the AI's JSON answer and coerce slot values to ints.

    AIs occasionally return slots as strings ("0") or as floats (0.0); we
    normalise to int so validation matches the algorithms' integer colours. A
    value that is not a whole number is left untouched so the coverage/validity
    checks below flag it rather than silently rounding.
    """
    with open(path) as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        sys.exit(f"error: {path} must be a JSON object mapping exam_id -> slot, "
                 f"got {type(raw).__name__}")
    colouring = {}
    for exam, slot in raw.items():
        if isinstance(slot, bool):                     # bool is a subclass of int
            colouring[exam] = slot
        elif isinstance(slot, int):
            colouring[exam] = slot
        elif isinstance(slot, str) and slot.strip().lstrip("-").isdigit():
            colouring[exam] = int(slot)
        elif isinstance(slot, float) and slot.is_integer():
            colouring[exam] = int(slot)
        else:
            colouring[exam] = slot                     # leave odd values to surface
    return colouring


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: python check_ai.py <scenario> <ai_answer.json>")

    name, ai_file = sys.argv[1], sys.argv[2]
    csv_path = os.path.join(DATASETS_DIR, name, "enrolments.csv")
    if not os.path.exists(csv_path):
        sys.exit(f"error: no dataset at {csv_path} "
                 f"(expected one of: {', '.join(sorted(os.listdir(DATASETS_DIR)))})")
    if not os.path.exists(ai_file):
        sys.exit(f"error: AI answer file not found: {ai_file}")

    # Same input the algorithms get: derive the graph from the same CSV.
    graph = graphutils.load_graph(csv_path)
    colouring = load_ai_colouring(ai_file)

    # Coverage: every exam assigned exactly once, no unknown exams invented.
    exams = set(graph)
    answered = set(colouring)
    missing = exams - answered          # exams the AI dropped
    extra = answered - exams            # exam_ids the AI made up
    non_int = sorted(e for e, s in colouring.items() if not isinstance(s, int))

    # Validity requires full, integer coverage first: is_proper_colouring would
    # also return False on a missing vertex, but we separate the reasons so the
    # failure mode (dropped exams vs genuine clash) is visible in the report.
    fully_covered = not missing and not non_int
    valid = graphutils.is_proper_colouring(graph, colouring) if fully_covered else False
    colours = graphutils.num_colours({e: s for e, s in colouring.items()
                                      if isinstance(s, int)})
    lb = graphutils.greedy_clique_lower_bound(graph)

    print(f"instance       : {name}")
    print(f"exams covered  : {len(answered & exams)}/{len(exams)}"
          + (f"   MISSING {sorted(missing)}" if missing else "")
          + (f"   INVENTED {sorted(extra)}" if extra else "")
          + (f"   NON-INTEGER {non_int}" if non_int else ""))
    print(f"valid (proper) : {valid}"
          + ("" if fully_covered else "   (cannot be valid: coverage incomplete)"))
    print(f"colours used   : {colours}")
    print(f"clique LB      : {lb}   (AI gap to LB = {colours - lb})")

    if valid:
        print("\nVERDICT: proper timetable -- compare 'colours used' to the "
              "DSATUR/CP-SAT columns in the Results table.")
    else:
        print("\nVERDICT: NOT a usable timetable -- "
              + ("dropped/invalid exam assignments."
                 if not fully_covered else
                 "a proper colouring was claimed but two conflicting exams share a slot."))


if __name__ == "__main__":
    main()
