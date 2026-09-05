"""Reproduce search.min_generators.extend's exact aliasing pattern:
the returned T2 is handed to many sibling recursive calls with rows + [row].
If the Rust ever returned a shared/mutated set, sibling order would matter.
Also probes the MAX_N guard and the declared p divergences.
"""
import random
from harness import (P, Results, fastcore, py_force, rs_force,
                     call_py_force, call_rs_force)

R = Results("dfs-aliasing")
rng = random.Random(31337)
POOL = [(1, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1), (1, -2), (3, 1)]


def gen_row(n, j, s):
    row = [0] * (2 * n)
    row[2 * j] = s[0]
    row[2 * j + 1] = s[1]
    return row


def dfs(F, rows, n, T, budget, start, cand, trace):
    ok, T2 = F(rows, n, T)
    trace.append((bool(ok), tuple(sorted(T2)), id(T2) == id(T)))
    if ok or budget == 0:
        return
    for ci in range(start, len(cand)):
        j, s = cand[ci]
        if j in T2:
            continue
        dfs(F, rows + [gen_row(n, j, s)], n, T2, budget - 1, ci + 1, cand, trace)


def rand_edge_rows(n, m):
    out = []
    for _ in range(m):
        r = [0] * (2 * n)
        u = rng.randrange(n)
        v = rng.randrange(n)
        while v == u:
            v = rng.randrange(n)
        x = POOL[rng.randrange(len(POOL))]
        r[2 * u] += x[0]; r[2 * u + 1] += x[1]
        r[2 * v] -= x[0]; r[2 * v + 1] -= x[1]
        out.append(r)
    return out


for it in range(400):
    n = rng.randrange(2, 7)
    rows = rand_edge_rows(n, rng.randrange(0, 2 * n))
    cand = [(j, s) for j in range(n) for s in POOL[:rng.choice([3, 4, 6])]]
    T0 = set(rng.sample(range(n), rng.randrange(0, max(1, n - 1))))
    tp, tr = [], []
    fastcore._INV.clear()
    dfs(py_force, rows, n, set(T0), 2, 0, cand, tp)
    dfs(rs_force, rows, n, set(T0), 2, 0, cand, tr)
    R.cmp("dfs it=%d n=%d |rows|=%d |T0|=%d (%d nodes)"
          % (it, n, len(rows), len(T0), len(tp)), tp, tr)
    R.n += 1
    if any(alias for _, _, alias in tr):
        R.div.append(("dfs it=%d returned set aliases T0" % it, "fresh", "aliased"))

# --------------------------------------------------------------- MAX_N guard
# Only the short-circuit shape is probed: with len(T0) >= n the Python loop body
# never runs, so this is cheap for Python.  (Cases that DO run the body are
# O(n^2) in Python at n ~ 2**20 and are not worth the wall clock.)
for n in ((1 << 20), (1 << 20) + 1):
    T0big = set(range(n))
    R.cmp("force([], n=%d, T0=range(n)) -- Python short-circuits" % n,
          call_py_force([], n, T0big), call_rs_force([], n, T0big))
    del T0big

# ------------------------------------------------------- declared p divergences
for p in (-5, 2 ** 32, 2 ** 40):
    R.n += 1
    try:
        from harness import py_rank
        fastcore._INV.clear()
        a = ("ok", py_rank([[1, 0], [0, 1]], p))
    except Exception as e:
        a = ("raise", type(e).__name__)
    try:
        from harness import rs_rank
        b = ("ok", rs_rank([[1, 0], [0, 1]], p))
    except Exception as e:
        b = ("raise", type(e).__name__)
    print("   p=%-12d py=%-16r rs=%r" % (p, a, b))

nd = R.report()
print("TOTAL DIVERGENCES:", nd)
