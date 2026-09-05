"""Dense random matrices at tiny p: maximal pressure on pivot selection
("first nonzero row from rk downward", no magnitude pivoting), the full-RREF
above-and-below elimination, the rk>=nB early break, and the ascending
first-hit found-vertex scan.  Also checks WHICH vertex is forced first by
recording the whole forcing trajectory, not just the final set.
"""
import random
import sys
from harness import (P, Results, fastcore, py_force, rs_force,
                     call_py_force, call_rs_force, call_py_rank, call_rs_rank)

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 5
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40000
rng = random.Random(SEED)
R = Results("fuzz-pivot seed=%d" % SEED)

PS = [2, 2, 3, 3, 5, 5, 7, 11, 13, 4, 6, 8, 9, 10, P]


def trajectory(F, rows, n, T0, p):
    """Force one vertex at a time so the ORDER of forced vertices is observed,
    not just the final set (the ascending-U scan is only visible this way)."""
    T = set(T0)
    order = []
    for _ in range(n + 1):
        fastcore._INV.clear()
        ok, T2 = F(rows, n, T, p)
        new = sorted(set(T2) - set(T))
        order.append((bool(ok), tuple(new)))
        if ok or not new:
            break
        # re-run with only the single lowest new vertex added, so each step
        # reveals exactly which j the scan picked first
        T = set(T) | {new[0]}
    return tuple(order)


for _ in range(N):
    p = PS[rng.randrange(len(PS))]
    n = rng.randrange(1, 6)
    m = rng.randrange(0, 8)
    rows = [[rng.randrange(0, p) for _ in range(2 * n)] for _ in range(m)]
    if rng.random() < 0.3:                       # inject exact ±label rows
        j = rng.randrange(n)
        r = [0] * (2 * n)
        r[2 * j] = 1
        r[2 * j + 1] = p - 1
        rows.append(r)
    if rng.random() < 0.25 and rows:             # duplicate a row
        rows.append(list(rows[rng.randrange(len(rows))]))
    if rng.random() < 0.25:                      # all-zero row
        rows.insert(rng.randrange(len(rows) + 1), [0] * (2 * n))
    T0 = set(rng.sample(range(n), rng.randrange(0, n)))

    R.cmp("force(m=%d n=%d p=%d T0=%r) rows=%r" % (m, n, p, sorted(T0), rows),
          call_py_force(rows, n, T0, p), call_rs_force(rows, n, T0, p))
    R.cmp("trajectory(n=%d p=%d T0=%r) rows=%r" % (n, p, sorted(T0), rows),
          trajectory(py_force, rows, n, T0, p),
          trajectory(rs_force, rows, n, T0, p))
    R.cmp("rank(p=%d) rows=%r" % (p, rows),
          call_py_rank(rows, p), call_rs_rank(rows, p))
    if len(R.div) > 6:
        break

nd = R.report()
print("TOTAL DIVERGENCES:", nd)
