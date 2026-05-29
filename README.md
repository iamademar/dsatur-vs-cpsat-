# Exam-timetabling comparison code

Code for the report's comparison of two exam-timetabling methods modelled as
graph colouring:

| File | Role |
|------|------|
| `dsatur.py`     | Method 1 — the DSATUR heuristic (report Section 4). Pure standard library. |
| `cpsat.py`      | Method 2 — the CP-SAT solver (report Section 5). Requires OR-Tools. |
| `graphutils.py` | Shared CSV loading, conflict-graph derivation, stats, and validation. Pure standard library. |
| `notebook/comparison.ipynb` | Runs both methods on every dataset and produces the results table and charts. Imports the files above; does not re-implement them. |
| `datasets/`     | Five committed enrolment datasets (see `datasets/README.md`). |

## Setup

`cpsat.py` needs Google OR-Tools, whose wheels currently support **Python
3.10–3.13** (not yet 3.14). Create a virtual environment with a supported
interpreter:

```bash
cd code
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

The full comparison is the notebook:

```bash
jupyter notebook notebook/comparison.ipynb
```

Run all cells top to bottom. It loads the five datasets, runs DSATUR then
CP-SAT (warm-started from DSATUR, 20 s cap each), prints a results table in the
same shape as the report's Table 4, draws the colours-used and runtime charts,
and validates every colouring.

## Notes

- The conflict graph is derived from enrolments exactly as documented in
  `datasets/README.md`: two exams conflict iff at least one student takes both.
- CP-SAT is warm-started from the DSATUR colouring (initial upper bound plus a
  solution hint) and breaks symmetry by pinning the first exam to slot 0, as
  described in report Section 5.2.
