"""Mutation, object-freshness, warm-start and buffer-reuse / re-entrancy tests."""
import copy
from harness import (P, Results, fastcore, fastcore_rs,
                     py_force, py_rank, rs_force, rs_rank,
                     call_py_force, call_rs_force)

R = Results("state")
fails = []


def check(label, cond, extra=""):
    R.n += 1
    if not cond:
        R.div.append((label, "expected-invariant", extra or "VIOLATED"))


E1 = [1, -1, 0, 0]
E2 = [0, 0, 1, -1]
CHAIN3 = [[1, -1, 0, 0, 0, 0], [0, 0, 1, -1, 0, 0], [0, 0, 0, 0, 1, -1]]

# ---------------------------------------------------------------- 1. mutation
for name, fn in (("py", py_force), ("rs", rs_force)):
    rows = [list(E1), list(E2)]
    before = copy.deepcopy(rows)
    T0 = {0}
    T0_before = set(T0)
    fastcore._INV.clear()
    ok, T = fn(rows, 2, T0)
    check("%s force does not mutate rows" % name, rows == before,
          "before=%r after=%r" % (before, rows))
    check("%s force does not mutate T0" % name, T0 == T0_before,
          "before=%r after=%r" % (T0_before, T0))
    check("%s force result is not the caller's T0 object" % name, T is not T0)
    check("%s force result is a real set" % name, type(T) is set, repr(type(T)))
    check("%s force ok is a real bool" % name, type(ok) is bool, repr(type(ok)))
    # mutating the result must not touch T0
    T.add(999)
    check("%s mutating result leaves T0 alone" % name, T0 == T0_before)

    rows2 = [list(E1), list(E2)]
    b2 = copy.deepcopy(rows2)
    fastcore._INV.clear()
    (py_rank if name == "py" else rs_rank)(rows2)
    check("%s rank does not mutate rows" % name, rows2 == b2,
          "before=%r after=%r" % (b2, rows2))

# two successive calls must return distinct set objects
rows = [E1, E2]
_, A = rs_force(rows, 2, set())
_, B = rs_force(rows, 2, set())
check("rs successive results are distinct objects", A is not B)
_, A2 = py_force(rows, 2, set())
_, B2 = py_force(rows, 2, set())
check("py successive results are distinct objects", A2 is not B2)

# ------------------------------------------------- 2. warm-start monotonicity
# force(rows, n, T0) == force(rows, n, force(rows0, n, T0)[1]) for rows0 subset
import itertools
import random

rng = random.Random(20260905)
POOL = [(1, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1), (1, -2), (3, 1)]


def rand_rows(n, m):
    out = []
    for _ in range(m):
        r = [0] * (2 * n)
        u = rng.randrange(n)
        v = rng.randrange(n)
        x = POOL[rng.randrange(len(POOL))]
        r[2 * u] += x[0]
        r[2 * u + 1] += x[1]
        if v != u:
            r[2 * v] -= x[0]
            r[2 * v + 1] -= x[1]
        out.append(r)
    return out


warm_bad = 0
for _ in range(4000):
    n = rng.randrange(1, 9)
    m = rng.randrange(0, 2 * n + 2)
    rows = rand_rows(n, m)
    k = rng.randrange(0, m + 1)
    rows0 = rows[:k]
    T0 = set(rng.sample(range(n), rng.randrange(0, n + 1)))
    for tag, F in (("py", py_force), ("rs", rs_force)):
        fastcore._INV.clear()
        direct = F(rows, n, T0)
        fastcore._INV.clear()
        _, mid = F(rows0, n, T0)
        fastcore._INV.clear()
        warm = F(rows, n, mid)
        if (direct[0], sorted(direct[1])) != (warm[0], sorted(warm[1])):
            warm_bad += 1
            R.n += 1
            R.div.append(("%s warm-start monotonicity" % tag,
                          repr((rows, n, sorted(T0), sorted(rows0 and [] or []))),
                          "direct=%r warm=%r" % (direct, warm)))
            break
    R.n += 1
check("warm-start held on 4000 random instances (both kernels)", warm_bad == 0,
      "%d failures" % warm_bad)

# ------------------------------------------- 3. buffer reuse across call shapes
# thread_local buffers are reused; alternate big/small/error calls and compare
seq = [
    ([[1, -1, 0, 0, 0, 0, 0, 0]] * 30, 4, set()),
    ([E1], 1, set()),
    ([], 3, {5}),
    (CHAIN3, 3, set()),
    ([[1, -1]], 2, set()),          # IndexError
    ([E1, E2], 2, set()),
    ([[0] * 32] * 20, 16, set()),
    ([E2, E1], 2, {7}),
    ([[1, -1]], 2, set()),          # IndexError again
    (CHAIN3, 3, {-4}),
]
for rep in range(200):
    for i, (rows, n, T0) in enumerate(seq):
        R.cmp("buffer-reuse rep%d case%d" % (rep, i),
              call_py_force(rows, n, set(T0)),
              call_rs_force(rows, n, set(T0)))

# --------------------------------------------------------- 4. re-entrancy
class ReentrantRows:
    """Iterating this calls back into fastcore_rs.force while the outer call
    holds the thread-local buffers."""
    def __init__(self, rows):
        self.rows = rows
        self.inner = None

    def __iter__(self):
        for r in self.rows:
            self.inner = rs_force([E1, E2], 2, set())
            yield r


try:
    rr = ReentrantRows(CHAIN3)
    got = rs_force(rr, 3, set())
    exp = call_py_force(CHAIN3, 3, set())
    R.cmp("re-entrant rows container",
          exp, ("force", bool(got[0]), type(got[0]).__name__,
                sorted(got[1]), type(got[1]).__name__))
    check("inner re-entrant call still correct",
          rr.inner is not None and rr.inner[0] is True and set(rr.inner[1]) == {0, 1},
          repr(rr.inner))
except Exception as e:
    R.n += 1
    R.div.append(("re-entrant rows container", "no exception",
                  "%s: %s" % (type(e).__name__, e)))


class ReentrantT0:
    def __iter__(self):
        rs_force([[0] * 32] * 20, 16, set())
        rs_rank([[1, 0], [0, 1]])
        return iter([0])


try:
    got = rs_force([E1, E2], 2, ReentrantT0())
    R.cmp("re-entrant T0 iterable",
          call_py_force([E1, E2], 2, [0]),
          ("force", bool(got[0]), type(got[0]).__name__,
           sorted(got[1]), type(got[1]).__name__))
except Exception as e:
    R.n += 1
    R.div.append(("re-entrant T0 iterable", "no exception",
                  "%s: %s" % (type(e).__name__, e)))

# ------------------------------------- 5. error mid-extraction leaves clean state
try:
    rs_force([[1, -1, 0, 0], [1, "bad", 0, 0]], 2, set())
except Exception:
    pass
R.cmp("call after a mid-extraction TypeError",
      call_py_force([E1, E2], 2, set()), call_rs_force([E1, E2], 2, set()))
try:
    rs_rank([[1, 2], [3, "bad"]])
except Exception:
    pass
from harness import call_py_rank, call_rs_rank
R.cmp("rank after a mid-extraction TypeError",
      call_py_rank([[1, 0], [0, 1]]), call_rs_rank([[1, 0], [0, 1]]))

nd = R.report()
print("TOTAL DIVERGENCES:", nd)
