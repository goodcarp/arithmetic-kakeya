"""Stress the thread_local scratch reuse across wildly heterogeneous shapes.

The Rust boundary keeps one shared `Vec<Vec<i64>>` row buffer and one
`ForceScratch` per thread, reused by both `force` and `rank`.  A stale-buffer
bug would show up as a wrong answer only when a call is preceded by a call with
a *different* shape.  So: interleave force/rank at random widths, row counts,
raggedness, out-of-range T0 and oversized rows, always comparing against the
reconstructed original Python.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "..", "..", "src"))
sys.path.insert(0, HERE)
sys.path.insert(0, SRC)

import orig_fastcore as PY  # noqa: E402
import fastcore_rs as RS  # noqa: E402
sys.path.insert(0, SRC)
from kakeya import ConstructibleGraph, build_rows  # noqa: E402

POOL8 = [(1, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1), (1, -2), (3, 1)]
ZERO = (0, 0)
DS = [[2], [3], [4], [2, 2], [2, 3], [3, 2], [2, 2, 2], [2, 4], [2, 2, 2, 2]]

rng = random.Random(int(os.environ.get("SEED", "424242")))


def synth():
    """A deliberately awkward instance: random width, ragged, oversized rows,
    out-of-range/duplicate T0."""
    n = rng.randint(0, 10)
    w = 2 * n + rng.choice([0, 0, 0, 2, 6])          # sometimes oversized rows
    m = rng.randint(0, 10)
    rows = []
    for _ in range(m):
        rows.append([rng.choice([-3, -2, -1, 0, 0, 0, 1, 2, 3]) for _ in range(w)])
    T0 = []
    for _ in range(rng.randint(0, 4)):
        T0.append(rng.choice([rng.randrange(-3, max(n, 1) + 3)] * 1))
    return rows, n, T0


def real():
    d = rng.choice(DS)
    n = 1
    for x in d:
        n *= x
    X = [ZERO] + rng.sample(POOL8, rng.randint(1, len(POOL8)))
    k = len(d)
    f = []
    for lev in range(k):
        f.append({})
    G = ConstructibleGraph(X, d, f)
    R = []
    verts = G.vertices()
    for _ in range(rng.randint(0, 3)):
        R.append((rng.choice(verts), rng.choice(POOL8)))
    rows, idx = build_rows(G, R)
    T0 = list(rng.sample(range(G.n), rng.randint(0, G.n)))
    return rows, G.n, T0


def cmp_force(rows, n, T0):
    PY._INV.clear()
    try:
        a = ("v",) + (lambda r: (r[0], tuple(sorted(r[1]))))(PY.force(rows, n, set(T0)))
    except BaseException as e:  # noqa: BLE001
        a = ("e", type(e).__name__)
    try:
        b = ("v",) + (lambda r: (r[0], tuple(sorted(r[1]))))(RS.force(rows, n, set(T0)))
    except BaseException as e:  # noqa: BLE001
        b = ("e", type(e).__name__)
    return a, b


def cmp_rank(rows):
    PY._INV.clear()
    try:
        a = ("v", PY.rank(rows))
    except BaseException as e:  # noqa: BLE001
        a = ("e", type(e).__name__)
    try:
        b = ("v", RS.rank(rows))
    except BaseException as e:  # noqa: BLE001
        b = ("e", type(e).__name__)
    return a, b


N = int(os.environ.get("N", "30000"))
bad = []
checks = 0
for i in range(N):
    rows, n, T0 = synth() if rng.random() < 0.6 else real()
    a, b = cmp_force(rows, n, T0)
    checks += 1
    if a != b:
        bad.append(("force", rows, n, T0, a, b))
    a, b = cmp_rank(rows)
    checks += 1
    if a != b:
        bad.append(("rank", rows, None, None, a, b))
    if len(bad) > 5:
        break

print("checks=%d  mismatches=%d" % (checks, len(bad)))
for rec in bad[:6]:
    print("MISMATCH", rec)
sys.exit(1 if bad else 0)
