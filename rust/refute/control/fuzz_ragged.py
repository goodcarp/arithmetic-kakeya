"""Hammer the two hardest control-flow paths:

  rank : zip(B[i], pr) truncation when the pivot row is shorter than the row
         being eliminated, plus the exact index at which IndexError fires.
  force: rows too short for some U-column, where U shrinks each round so a row
         that was fatal in round 1 may be skipped in round 2 (and vice versa).
"""
import random
import sys
from harness import (P, Results, call_py_force, call_rs_force,
                     call_py_rank, call_rs_rank)

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 11
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40000
rng = random.Random(SEED)
R = Results("fuzz-ragged seed=%d" % SEED)

PS = [2, 3, 4, 5, 7, 11, 97, 65537, P]
VALS = [0, 0, 1, 1, 2, 3, -1, -2, -3, 4, 5, 6, P, P - 1, P + 1]


def ragged_rows(maxrows=5, maxw=7):
    return [[VALS[rng.randrange(len(VALS))] for _ in range(rng.randrange(0, maxw))]
            for _ in range(rng.randrange(1, maxrows + 1))]


for _ in range(N):
    p = PS[rng.randrange(len(PS))]
    rows = ragged_rows()
    R.cmp("rank(%r, %r)" % (rows, p), call_py_rank(rows, p), call_rs_rank(rows, p))

    # force: n up to 4, rows of length anywhere in 0..2n+2, T0 possibly covering
    # the vertices whose columns are the short ones.
    n = rng.randrange(1, 5)
    frows = [[VALS[rng.randrange(len(VALS))] for _ in range(rng.randrange(0, 2 * n + 3))]
             for _ in range(rng.randrange(0, 5))]
    T0 = set(rng.sample(range(n), rng.randrange(0, n + 1)))
    R.cmp("force(%r, %r, %r, %r)" % (frows, n, sorted(T0), p),
          call_py_force(frows, n, T0, p), call_rs_force(frows, n, T0, p))
    if len(R.div) > 6:
        break

nd = R.report()
print("TOTAL DIVERGENCES:", nd)
