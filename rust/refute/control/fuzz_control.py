"""Randomised control-flow fuzz: ragged rows, degenerate shapes, odd T0, odd p.

Only shapes where the contract promises agreement are counted as divergences;
the four declared divergences (p<0, p>=2**32, entries outside i64, non-int
entries) are excluded by construction.
"""
import random
import sys
from harness import (P, Results, call_py_force, call_rs_force,
                     call_py_rank, call_rs_rank)

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 20260905
N = int(sys.argv[2]) if len(sys.argv) > 2 else 60000
rng = random.Random(SEED)

R = Results("fuzz-control seed=%d" % SEED)

PS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 13, 97, 257, 65537, P, P - 1, 2 ** 31,
      2 ** 32 - 1, 0]
ENTRY_POOL = [-3, -2, -1, 0, 0, 0, 1, 2, 3, P, P - 1, P + 1, -P, 2 * P,
              2 ** 31, -(2 ** 31), 6, 12, 2 ** 40, -(2 ** 40), True, False]


def rand_row(width):
    return [ENTRY_POOL[rng.randrange(len(ENTRY_POOL))] for _ in range(width)]


def rand_rows(n, ragged):
    m = rng.randrange(0, 7)
    out = []
    for _ in range(m):
        if ragged:
            w = rng.randrange(0, 2 * max(n, 1) + 3)
        else:
            w = 2 * max(n, 0)
        r = rand_row(w)
        if rng.random() < 0.2:
            r = [0] * len(r)
        out.append(r)
        if out and rng.random() < 0.15:
            out.append(list(out[rng.randrange(len(out))]))
    return out


def rand_T0(n):
    k = rng.randrange(0, 4)
    vals = []
    for _ in range(k):
        c = rng.random()
        if c < 0.65 and n > 0:
            vals.append(rng.randrange(n))
        elif c < 0.8:
            vals.append(rng.randrange(n, n + 5) if n > 0 else rng.randrange(0, 5))
        else:
            vals.append(-rng.randrange(1, 5))
    shape = rng.randrange(5)
    if shape == 0:
        return vals
    if shape == 1:
        return tuple(vals)
    if shape == 2:
        return set(vals)
    if shape == 3:
        return frozenset(vals)
    return list(vals)


for _ in range(N):
    ragged = rng.random() < 0.45
    n = rng.choice([-1, 0, 1, 1, 2, 2, 3, 3, 4, 5])
    rows = rand_rows(n, ragged)
    if rng.random() < 0.15:
        rows = tuple(tuple(r) for r in rows)
    p = PS[rng.randrange(len(PS))]
    if p <= 0 or p >= 2 ** 32:
        p = P                     # declared divergences, skip
    T0 = rand_T0(n)
    label = "force(rows=%r, n=%r, T0=%r, p=%r)" % (rows, n, T0, p)
    if not R.cmp(label, call_py_force(rows, n, T0, p),
                 call_rs_force(rows, n, T0, p)):
        if len(R.div) > 6:
            break

    rrows = rand_rows(rng.choice([0, 1, 2, 3, 4]), ragged)
    if rng.random() < 0.15:
        rrows = tuple(tuple(r) for r in rrows)
    label = "rank(rows=%r, p=%r)" % (rrows, p)
    if not R.cmp(label, call_py_rank(rrows, p), call_rs_rank(rrows, p)):
        if len(R.div) > 6:
            break

nd = R.report()
print("TOTAL DIVERGENCES:", nd)
