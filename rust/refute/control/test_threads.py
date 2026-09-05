"""Concurrency: fastcore_rs releases the GIL (py.detach) around a thread_local
buffer.  Hammer it from several Python threads and compare every result to the
single-threaded Python reference.  Also probes truthy-but-empty containers.
"""
import random
import threading
from harness import (P, Results, fastcore, py_force, py_rank, rs_force, rs_rank,
                     call_py_rank, call_rs_rank)

R = Results("threads")
rng = random.Random(9001)
POOL = [(1, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1), (1, -2), (3, 1)]

CASES = []
for _ in range(300):
    n = rng.randrange(1, 9)
    rows = []
    for _ in range(rng.randrange(0, 2 * n + 1)):
        r = [0] * (2 * n)
        u = rng.randrange(n); v = rng.randrange(n)
        x = POOL[rng.randrange(len(POOL))]
        r[2 * u] += x[0]; r[2 * u + 1] += x[1]
        if v != u:
            r[2 * v] -= x[0]; r[2 * v + 1] -= x[1]
        rows.append(r)
    T0 = set(rng.sample(range(n), rng.randrange(0, n + 1)))
    fastcore._INV.clear()
    ok, T = py_force(rows, n, T0)
    fastcore._INV.clear()
    rk = py_rank(rows) if rows else 0
    CASES.append((rows, n, T0, (bool(ok), tuple(sorted(T))), rk))

errs = []
lock = threading.Lock()


def worker(tid):
    local = []
    for rep in range(40):
        for rows, n, T0, exp, rk in CASES:
            ok, T = rs_force(rows, n, set(T0))
            if (bool(ok), tuple(sorted(T))) != exp:
                local.append(("force", tid, rep, n, exp,
                              (bool(ok), tuple(sorted(T)))))
            got = rs_rank(rows)
            if got != rk:
                local.append(("rank", tid, rep, n, rk, got))
    with lock:
        errs.extend(local)


ts = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
for t in ts:
    t.start()
for t in ts:
    t.join()

R.n += 8 * 40 * len(CASES) * 2
for e in errs[:6]:
    R.div.append(("threaded %s" % e[0], e[4], e[5]))

print("threaded checks: %d, failures: %d" % (8 * 40 * len(CASES) * 2, len(errs)))


# --------------------------------------------- truthy-but-empty row containers
class TruthyEmpty:
    def __len__(self):
        return 1

    def __iter__(self):
        return iter([])


class FalsyNonEmpty:
    def __len__(self):
        return 0

    def __iter__(self):
        return iter([[1, 0], [0, 1]])


R.cmp("rank(TruthyEmpty())", call_py_rank(TruthyEmpty()), call_rs_rank(TruthyEmpty()))
R.cmp("rank(FalsyNonEmpty())", call_py_rank(FalsyNonEmpty()),
      call_rs_rank(FalsyNonEmpty()))
R.cmp("rank(iter([]))", call_py_rank(iter([])), call_rs_rank(iter([])))
R.cmp("rank(x for x in [])", call_py_rank((x for x in [])),
      call_rs_rank((x for x in [])))
R.cmp("rank(zip([],[]))", call_py_rank(zip([], [])), call_rs_rank(zip([], [])))
R.cmp("rank(filter(None,[]))", call_py_rank(filter(None, [])),
      call_rs_rank(filter(None, [])))
R.cmp("rank(map(list,[]))", call_py_rank(map(list, [])),
      call_rs_rank(map(list, [])))
R.cmp("rank(reversed([]))", call_py_rank(reversed([])),
      call_rs_rank(reversed([])))

nd = R.report()
print("TOTAL DIVERGENCES:", nd)
