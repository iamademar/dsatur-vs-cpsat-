# Exam-timetabling datasets

Five synthetic enrolment datasets for the exam-timetabling-as-graph-colouring study in
`../latex/main.tex`. Each scenario captures a different size/density regime that a real
registrar might face, from a tiny departmental exam week (`tiny`) to a multi-faculty
university-scale instance (`large`).

The datasets are stored as **student enrolments**, not as conflict graphs. The conflict
graph is *derived* from the enrolments: two exams conflict if and only if at least one
student is enrolled in both. Keeping the raw enrolments lets a reader see the clique
structure that real timetables carry (large cohorts in shared 100-level papers form
near-cliques; small honours and project papers form long tails), which would be lost if
only the derived edge list were stored.

## Directory layout

```
datasets/
  README.md          (this file)
  tiny/enrolments.csv
  small/enrolments.csv
  medium/enrolments.csv
  dense/enrolments.csv
  large/enrolments.csv
```

## CSV schema

Each `enrolments.csv` has the same two-column long-format shape:

| Column        | Type   | Notes                                                                  |
|---------------|--------|------------------------------------------------------------------------|
| `student_id`  | string | Zero-padded ID, e.g. `S0001`. Same student appears on multiple rows.   |
| `exam_id`     | string | Department code plus a 3-digit number, e.g. `COMP100`, `MATH211`.       |

- **One row per (student, exam) enrolment.** A student taking four exams appears on
  four rows.
- **Sorted by `(student_id, exam_id)`** for stable diffs.
- **No quoting, no escaping** is needed — all values are ASCII alphanumerics.

The first line of every file is the header `student_id,exam_id`.

### Exam ID convention

The numeric part of an exam ID encodes the academic level:

| Range       | Level                         |
|-------------|-------------------------------|
| 100–199     | 1st-year introductory papers  |
| 200–299     | 2nd-year                      |
| 300–399     | 3rd-year                      |
| 400–499     | 4th-year / honours            |
| 500–599     | postgraduate project, dissertation |

The departmental prefix is one of `COMP`, `MATH`, `STAT`, `PHIL`, `PSYC`, `ECON`, `HIST`,
`BIOL`. Not every department appears in every scenario; the `large` scenario uses six,
`tiny` and `dense` use only two.

## How to derive the conflict graph

Each enrolment row contributes (potentially) several edges: every pair of exams that a
single student is enrolled in becomes a conflict edge in the graph. The conflict graph
is simple and undirected; the same pair contributed by two different students collapses
into one edge.

In Python (no external libraries):

```python
import csv
from collections import defaultdict
from itertools import combinations

with open("tiny/enrolments.csv") as f:
    reader = csv.DictReader(f)
    by_student = defaultdict(list)
    for row in reader:
        by_student[row["student_id"]].append(row["exam_id"])

vertices = set()
edges = set()
for exams in by_student.values():
    vertices.update(exams)
    for u, v in combinations(sorted(exams), 2):
        edges.add((u, v))

print(f"|V| = {len(vertices)}, |E| = {len(edges)}")
```

The same derivation in pandas is two lines (self-merge on `student_id`, dedupe), but the
pure-stdlib version above runs on any Python 3 install without pip.

## Cohort structure (the "realistic" part)

Real university exam weeks have a long-tailed cohort distribution: a handful of large
intro papers, more medium-sized middle-year papers, and a long tail of small final-year
and project papers. The generator mirrors that:

| Level          | Cohort size  | Overlap behaviour                                              |
|----------------|--------------|----------------------------------------------------------------|
| 100-level      | 60–200       | broad — most students take 3+ intros, often across departments |
| 200-level      | 30–80        | moderate — clusters within a major                              |
| 300-level      | 15–40        | strong within a major, weak across departments                  |
| 400-level      | 5–15         | very strong with sibling 4xx papers (honours cohort)            |
| 500-level      | 1–3          | often isolated; produces the deg=0 vertices used in §4.1.2     |

Students have a "primary department" and a "primary level", and their enrolment is
biased toward papers in that bucket plus 1–2 cross-department fillers (typically
introductory papers, the closest real-world analogue of general-education load).

## Per-scenario summary

| Scenario | Exams | Students | Departments | Approx |E| | Approx density | Intent                              |
|----------|-------|----------|-------------|------------|----------------|-------------------------------------|
| `tiny`   | 15    | 50       | 2           | ~100       | ~0.95          | hand-inspectable; almost-complete    |
| `small`  | 40    | 250      | 3           | ~660       | ~0.84          | one full undergraduate programme    |
| `medium` | 100   | 700      | 4           | ~3300      | ~0.67          | two faculties' worth                |
| `dense`  | 60    | 400      | 2           | ~1750      | ~0.99          | worst-case constrained exam week    |
| `large`  | 250   | 3000     | 6           | ~14400     | ~0.46          | university-scale, long tail of 5xx  |

The vertex counts and ballpark densities target Table 4 in §9 of the report
(`tab:prelim`), but the generator's randomness means exact edge counts vary by a few
percent across regenerations. The README's numbers are honest descriptions of *these*
committed CSVs, not the generator's eventual mean.

## Reproducibility

These CSVs were generated with a per-scenario seed derived from the scenario name plus a
fixed offset. Re-running the (currently uncommitted) generator on the same code produces
byte-identical files. The generator script itself is expected to be committed later as
part of `code/examcolor.py` per the §10 implementation plan; until then, treat the
committed CSVs as the source of truth.
