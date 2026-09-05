"""Threading, re-entrancy, aliasing and keyword-binding probes for fastcore_rs.

The Rust boundary keeps a `thread_local!` scratch buffer shared between `force`
and `rank`, releases the GIL with `py.detach` while holding a `RefCell` borrow of
it, and falls back to fresh allocations when the borrow is already taken.  These
probes attack that design.
"""
import os
import random
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "..", "..", "src"))
sys.path.insert(0, HERE)
sys.path.insert(0, SRC)

import orig_fastcore as PY  # noqa: E402
import fastcore_rs as RS  # noqa: E402

fails = []


def chk(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + (("  " + str(extra)) if extra else ""))
    if not cond:
        fails.append(name)


# --------------------------------------------------------------- corpus
def mk_instance(rng):
    n = rng.randint(1, 8)
    m = rng.randint(0, 8)
    rows = []
    for _ in range(m):
        r = [0] * (2 * n)
        u = rng.randrange(n)
        v = rng.randrange(n)
        x = rng.choice([(1, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1), (1, -2), (3, 1)])
        r[2 * u] += x[0]
        r[2 * u + 1] += x[1]
        if v != u:
            r[2 * v] -= x[0]
            r[2 * v + 1] -= x[1]
        rows.append(r)
    T0 = set(rng.sample(range(n), rng.randint(0, n)))
    return rows, n, T0


rng = random.Random(20260905)
CORPUS = [mk_instance(rng) for _ in range(4000)]
EXPECT = []
for rows, n, T0 in CORPUS:
    PY._INV.clear()
    ok, T = PY.force(rows, n, set(T0))
    PY._INV.clear()
    rk = PY.rank(rows) if rows else 0
    EXPECT.append((ok, frozenset(T), rk))

# single-threaded agreement first (sanity)
bad = 0
for (rows, n, T0), (ok, T, rk) in zip(CORPUS, EXPECT):
    o2, T2 = RS.force(rows, n, set(T0))
    r2 = RS.rank(rows)
    if (o2, frozenset(T2), r2) != (ok, T, rk):
        bad += 1
chk("single-thread agreement on %d instances" % len(CORPUS), bad == 0, "mismatches=%d" % bad)

# --------------------------------------------------------------- threads
NTHREAD = 8
errors = []


def worker(tid):
    local_rng = random.Random(tid)
    for _ in range(6000):
        i = local_rng.randrange(len(CORPUS))
        rows, n, T0 = CORPUS[i]
        ok, T, rk = EXPECT[i]
        try:
            o2, T2 = RS.force(rows, n, set(T0))
            r2 = RS.rank(rows)
        except BaseException as e:  # noqa: BLE001
            errors.append((tid, i, "exc", repr(e)))
            return
        if (o2, frozenset(T2), r2) != (ok, T, rk):
            errors.append((tid, i, (o2, sorted(T2), r2), (ok, sorted(T), rk)))
            return


ts = [threading.Thread(target=worker, args=(t,)) for t in range(NTHREAD)]
for t in ts:
    t.start()
for t in ts:
    t.join()
chk("%d threads x 6000 force+rank calls agree" % NTHREAD, not errors, errors[:3])

# --------------------------------------------------------------- re-entrancy
class ReentrantRows:
    """A `rows` iterable that calls back into fastcore_rs.force while being
    consumed, forcing the thread_local borrow to be already held."""

    def __init__(self, rows, inner):
        self.rows = rows
        self.inner = inner
        self.results = []

    def __iter__(self):
        for r in self.rows:
            self.results.append(RS.force(*self.inner))
            yield r


inner = ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, set())
PY._INV.clear()
exp_outer = PY.force([[1, -1, 0, 0, 0, 0], [0, 0, 1, -1, 0, 0]], 3, set())
PY._INV.clear()
exp_inner = PY.force(*inner)
rr = ReentrantRows([[1, -1, 0, 0, 0, 0], [0, 0, 1, -1, 0, 0]], inner)
got = RS.force(rr, 3, set())
chk("re-entrant rows: outer result correct",
    (got[0], frozenset(got[1])) == (exp_outer[0], frozenset(exp_outer[1])),
    "%r vs %r" % (got, exp_outer))
chk("re-entrant rows: every inner result correct",
    all((a, frozenset(b)) == (exp_inner[0], frozenset(exp_inner[1])) for a, b in rr.results),
    rr.results[:2])

# rank re-entrancy
class ReentrantRankRows:
    def __init__(self, rows):
        self.rows = rows
        self.results = []

    def __iter__(self):
        for r in self.rows:
            self.results.append(RS.rank([[1, 2], [2, 4]]))
            yield r


rr2 = ReentrantRankRows([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
PY._INV.clear()
chk("re-entrant rank: outer", RS.rank(rr2) == 3, RS.rank([[1, 0, 0], [0, 1, 0], [0, 0, 1]]))
chk("re-entrant rank: inner", all(v == 1 for v in rr2.results), rr2.results)

# --------------------------------------------------------------- aliasing
rows = [[1, -1, 0, 0], [0, 0, 1, -1]]
rows_before = [list(r) for r in rows]
T0 = {0}
T0_before = set(T0)
ok, T = RS.force(rows, 2, T0)
chk("force does not mutate rows", rows == rows_before)
chk("force does not mutate T0", T0 == T0_before)
chk("force returns a distinct object from T0", T is not T0)
chk("force returns a real set", type(T) is set, type(T))
chk("force returns a real bool", type(ok) is bool, type(ok))
chk("returned set holds real ints", all(type(x) is int for x in T), [type(x) for x in T])
T.add(999)
ok2, T2 = RS.force(rows, 2, T0)
chk("mutating the returned set does not leak into the next call", T2 == {0, 1}, T2)
chk("two calls return distinct set objects", T2 is not T)

# warm-start chain, the search.min_generators pattern
PY._INV.clear()
base = [[1, -1, 0, 0, 0, 0]]
extra = [0, 0, 1, -1, 0, 0]
ok_a, Ta = RS.force(base, 3, set())
kids = []
for _ in range(3):
    kids.append(RS.force(base + [extra], 3, Ta))
chk("warm-start: parent set survives being handed to 3 siblings",
    all(frozenset(k[1]) == frozenset(kids[0][1]) for k in kids) and frozenset(Ta) == {0},
    (sorted(Ta), [sorted(k[1]) for k in kids]))

# --------------------------------------------------------------- kwargs
try:
    a = RS.force(rows=rows, n=2, T0=set())
    kw_ok = True
except TypeError as e:
    kw_ok = False
    kw_err = repr(e)
chk("force accepts all-keyword call (rows=, n=, T0=) like Python", kw_ok,
    "" if kw_ok else kw_err)
try:
    b = RS.rank(rows=rows, p=2147483647)
    kw2 = True
except TypeError as e:
    kw2 = False
    kw2_err = repr(e)
chk("rank accepts all-keyword call (rows=, p=)", kw2, "" if kw2 else kw2_err)
chk("force accepts p by keyword", RS.force([[3, 1, 0, 0]], 1, set(), p=7) ==
    PY.force([[3, 1, 0, 0]], 1, set(), 7) or True)
PY._INV.clear()
chk("force p=7 keyword matches Python positional",
    (lambda r: (r[0], frozenset(r[1])))(RS.force([[3, 1, 0, 0]], 1, set(), p=7)) ==
    (lambda r: (r[0], frozenset(r[1])))(PY.force([[3, 1, 0, 0]], 1, set(), 7)))

# arity errors
for call, label in [
    (lambda f: f([[1, -1]], 1), "force missing T0"),
    (lambda f: f([[1, -1]], 1, set(), 7, 8), "force too many args"),
    (lambda f: f(), "rank missing rows"),
]:
    ea = eb = None
    try:
        call(PY.force if "force" in label else PY.rank)
    except BaseException as e:  # noqa: BLE001
        ea = type(e).__name__
    try:
        call(RS.force if "force" in label else RS.rank)
    except BaseException as e:  # noqa: BLE001
        eb = type(e).__name__
    chk("%s: same exception type" % label, ea == eb, "py=%s rs=%s" % (ea, eb))

print()
print("FAILS:", fails if fails else "none")
sys.exit(1 if fails else 0)
