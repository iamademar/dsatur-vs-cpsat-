# Exam timetabling as graph colouring — DSATUR vs CP-SAT (vs an LLM)

University exam timetabling is a scheduling problem: assign every final exam to a
time slot so that no student has to sit two exams at once. It maps cleanly onto
**graph colouring**.

| Timetabling concept | Graph-theory representation |
|---|---|
| Exam | Vertex |
| A student enrolled in two exams | Edge between those two exam vertices |
| Time slot | Colour |
| Valid timetable | Proper vertex colouring (no edge has both ends the same colour) |
| Minimum number of time slots | Chromatic number χ(G) |

So "what is the fewest number of exam slots we need?" becomes "what is the
chromatic number of the conflict graph?" — which is NP-hard in general. This
project implements and benchmarks two approaches to it, plus an exploratory
third:

1. **DSATUR** — a classical graph-colouring heuristic (`dsatur.py`).
2. **Google OR-Tools CP-SAT** — a modern constraint-programming solver
   (`cpsat.py`), warm-started from DSATUR.
3. **A general-purpose AI assistant** (ChatGPT) prompted to colour the same
   instances directly, scored with the same validator (`check_ai.py`).

This repository is the code behind a University of Waikato COMPX546 (Graph
Theory) report; it is self-contained and reproduces every number in that report.

## How the two methods work

**DSATUR** ("degree of saturation") is greedy: it repeatedly colours the
uncoloured vertex that currently sees the most distinct colours among its
neighbours (ties broken by ordinary degree), giving it the smallest free colour.
In timetabling terms: schedule the most constrained exams first. It is fast and
deterministic, but not guaranteed optimal in general.

**CP-SAT** models the problem as variables (one slot per exam) and not-equal
constraints (one per conflict edge), then searches the whole space — propagating,
branching, learning from dead ends, and tightening a lower and upper bound until
they meet. When they meet it has *proven* the optimum; if its time budget runs
out first it returns the best timetable found so far without a proof. Here it is
warm-started from DSATUR's colouring and breaks symmetry by pinning the first
exam to slot 0.

## Datasets

Five synthetic enrolment datasets under `datasets/`, one folder per scenario,
each a long-format `enrolments.csv` (`student_id,exam_id`, one row per
enrolment). The conflict graph is **derived** from the enrolments (two exams
conflict iff a student takes both), which keeps the realistic clique structure
that a student roster induces. Generation is seeded, so the CSVs — and therefore
the edge counts below — are exact and reproducible.

| Scenario | Exams | Students | Depts | Edges | Density | Intent |
|---|---:|---:|---:|---:|---:|---|
| `tiny`   | 15  | 45    | 2 | 100    | 0.95 | hand-inspectable; near-complete |
| `small`  | 40  | 250   | 3 | 659    | 0.84 | one full undergraduate programme |
| `medium` | 100 | 700   | 4 | 3,303  | 0.67 | two faculties' worth of papers |
| `dense`  | 60  | 400   | 2 | 1,755  | 0.99 | worst-case constrained exam week |
| `large`  | 250 | 3,000 | 6 | 14,404 | 0.46 | university-scale, long 5xx tail |

See `datasets/README.md` for the CSV schema and the CSV→graph derivation snippet.

## Results

Both methods on the five datasets (CP-SAT capped at 20 s per instance,
warm-started from DSATUR). **Colours** = slots used; **t(s)** = runtime;
**opt** = whether CP-SAT proved optimality.

| instance | exams | edges | DSATUR | t(s) | CP-SAT | t(s) | opt |
|---|---:|---:|---:|---:|---:|---:|:--:|
| tiny   | 15  | 100   | 14 | <0.001 | 14 | 0.03  | Y |
| small  | 40  | 659   | 25 | <0.001 | 25 | 20.04 | N |
| medium | 100 | 3,303 | 30 | 0.002  | 28 | 20.02 | N |
| dense  | 60  | 1,755 | 51 | <0.001 | 51 | 0.11  | Y |
| large  | 250 | 14,404| 46 | 0.005  | 44 | 20.04 | N |

DSATUR colours every instance in milliseconds; CP-SAT either finishes instantly
(when it self-certifies optimality — `tiny`, `dense`, where a clique pins the
bound) or runs to the cap. The `opt` column above records solver
self-certification; `small` reads `N` even though its 25 is independently known
to be optimal from the same clique lower bound — CP-SAT just could not lift its
own bound to meet it within 20 s. The colour counts are always within two slots
of each other.

### AI assistant (Method 3)

Each instance given to ChatGPT as the raw `enrolments.csv`, with no algorithm
and no code, then scored by `check_ai.py`. Each figure is a **single
non-deterministic sample**, not a repeated measurement.

| instance | DSATUR | CP-SAT | AI | valid? | coverage |
|---|---:|---:|---:|:--:|---:|
| tiny   | 14 | 14 | 14 | ✓ | 15/15  |
| small  | 25 | 25 | 25 | ✓ | 40/40  |
| medium | 30 | 28 | **27** | ✓ | 100/100 |
| dense  | 51 | 51 | 51 | ✓ | 60/60  |
| large  | 46 | 44 | **43** | ✓ | 250/250 |

The assistant produced valid, complete timetables on all five instances, matched
the best result on three, and used *fewer* slots than both algorithms on
`medium` and `large`. Caveat: "better" means better than CP-SAT's best answer
within its 20 s budget, not a proven optimum (on the two instances CP-SAT
*proved*, the assistant only matched it).

## Files

| File | Role |
|------|------|
| `dsatur.py`     | Method 1 — the DSATUR heuristic. Pure standard library. |
| `cpsat.py`      | Method 2 — the CP-SAT solver. Requires OR-Tools. |
| `graphutils.py` | Shared CSV loading, conflict-graph derivation, stats, validation (`is_proper_colouring`), and the greedy clique lower bound. Pure standard library. |
| `check_ai.py`   | Method 3 — scores an AI assistant's answer against the same conflict graph and validator. |
| `ai_{tiny,small,medium,dense,large}.json` | The assistant's raw answer per instance. |
| `notebook/comparison.ipynb` | Runs both algorithms on every dataset and produces the results table and charts. Imports the files above; does not re-implement them. |
| `datasets/`     | The five committed enrolment datasets (see `datasets/README.md`). |

## Setup

`cpsat.py` needs Google OR-Tools, whose wheels currently support **Python
3.10–3.13** (not yet 3.14). Create a virtual environment with a supported
interpreter:

```bash
python3.12 -m venv .venv          # any of 3.10 / 3.11 / 3.12 / 3.13 works
source .venv/bin/activate
pip install -r requirements.txt
```

`dsatur.py` and `graphutils.py` are pure standard library and run on any
Python 3, including 3.14 — only the CP-SAT path needs the venv.

## Running

Each method file runs standalone on one dataset:

```bash
python dsatur.py datasets/tiny/enrolments.csv
python cpsat.py  datasets/dense/enrolments.csv
```

The full algorithm comparison is the notebook:

```bash
jupyter notebook notebook/comparison.ipynb
```

Run all cells top to bottom. It loads the five datasets, runs DSATUR then
CP-SAT (warm-started from DSATUR, 20 s cap each), prints the results table,
draws the colours-used and runtime charts, and validates every colouring.

## Reproducing the AI comparison (Method 3)

Give an AI assistant the same `enrolments.csv` and the rule "two exams that
share a student cannot share a slot; use as few slots as possible". Save its
JSON answer (a map from exam ID to integer slot) and score it:

```bash
python check_ai.py tiny ai_tiny.json
```

`check_ai.py` reports validity, coverage (whether every exam was assigned),
colours used, and the gap to the clique lower bound — never trusting the
assistant's self-reported validity. The five `ai_*.json` files are the answers
used in the report.

## Notes

- The conflict graph is derived from enrolments exactly as documented in
  `datasets/README.md`: two exams conflict iff at least one student takes both.
- CP-SAT is warm-started from the DSATUR colouring (initial upper bound plus a
  solution hint) and breaks symmetry by pinning the first exam to slot 0.
