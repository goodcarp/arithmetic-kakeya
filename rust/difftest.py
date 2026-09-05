"""Differential test: fastcore_rs (Rust) vs the pure-Python fastcore.

Every reference evaluation clears fastcore._INV first -- the memo is keyed on
`a` alone, so without that the Python corpus is not reproducible (S1 contract
sec 2.1).

Run:  /usr/bin/python3 rust/difftest.py     (cwd anywhere)
"""
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

import fastcore                      # noqa: E402
import fastcore_rs                   # noqa: E402

# Survive the step-6 drop-in wiring, which shadows fastcore.force/rank.
PY_FORCE = getattr(fastcore, "_force_py", fastcore.force)
PY_RANK = getattr(fastcore, "_rank_py", fastcore.rank)
RS_FORCE = fastcore_rs.force
RS_RANK = fastcore_rs.rank

P = (1 << 31) - 1

# Documented divergences (S1 contract sec 5.4): Python has bignums, Rust
# extracts entries as i64.  Not counted as mismatches.
EXPECTED_DIVERGENCE = {
    "rank([[9223372036854775808,1],[1,0]])",
}


def call_py(fn, *a):
    fastcore._INV.clear()
    try:
        return ("ok", fn(*a))
    except Exception as e:                       # noqa: BLE001
        return ("exc", type(e).__name__)


def call_rs(fn, *a):
    try:
        return ("ok", fn(*a))
    except Exception as e:                       # noqa: BLE001
        return ("exc", type(e).__name__)


def norm(kind, tag, val):
    if tag == "exc":
        return ("exc", val)
    if kind == "force":
        ok, T = val
        return ("ok", bool(ok), tuple(sorted(T)))
    return ("ok", int(val))


class Counter:
    def __init__(self):
        self.cases = 0
        self.mismatches = 0
        self.divergences = 0
        self.reports = []

    def check(self, kind, args, label=None):
        self.cases += 1
        pyf, rsf = (PY_FORCE, RS_FORCE) if kind == "force" else (PY_RANK, RS_RANK)
        pt, pv = call_py(pyf, *args)
        rt, rv = call_rs(rsf, *args)
        try:
            a = norm(kind, pt, pv)
        except Exception:                        # noqa: BLE001
            a = ("unnormalisable", repr(pv))
        try:
            b = norm(kind, rt, rv)
        except Exception:                        # noqa: BLE001
            b = ("unnormalisable", repr(rv))
        if a == b:
            return True
        if label in EXPECTED_DIVERGENCE:
            self.divergences += 1
            return True
        self.mismatches += 1
        if len(self.reports) < 25:
            self.reports.append(
                "MISMATCH %s%r\n    py = %r\n    rs = %r" % (kind, args, a, b))
        return False


# ---------------------------------------------------------------------------
# (a) the S1 edge cases
# ---------------------------------------------------------------------------

EDGE_CASES = json.load(open(os.path.join(HERE, "edge_cases.json")))


def run_edge_cases(c):
    import ast
    n0 = c.cases
    for raw in EDGE_CASES:
        expr = raw.split("  #")[0].strip()
        tree = ast.parse(expr, mode="eval").body
        kind = tree.func.id
        args = [eval(ast.unparse(a) if hasattr(ast, "unparse") else "",
                     {"set": set, "frozenset": frozenset}) for a in tree.args]
        c.check(kind, tuple(args), label=expr)
    return c.cases - n0


# ---------------------------------------------------------------------------
# (b) randomised sweep
# ---------------------------------------------------------------------------

PS = [2147483647, 7, 97, 1000000007, 91]
SMALL = list(range(-5, 6))
BIG = [-(2 ** 33), -(2 ** 33) + 1, -(2 ** 33) - 7, 2 ** 33, 2 ** 33 + 1,
       2 ** 33 - 3, 2 ** 40, -(2 ** 40) - 1]
NEARP = [P - 2, P - 1, P, P + 1, P + 2, -P, -P + 1, -P - 1, 2 * P, 2 * P + 1,
         P // 2, 90, 91, 92, 96, 97, 98, 6, 7, 8]


def entry(rng, mode):
    if mode == 0:
        return rng.choice(SMALL)
    if mode == 1:
        return rng.choice(SMALL + BIG)
    if mode == 2:
        return rng.choice(SMALL + NEARP)
    return rng.choice(SMALL + BIG + NEARP)


def run_random(c, count, seed=12345):
    rng = random.Random(seed)
    for it in range(count):
        n = rng.randint(1, 12)
        w = 2 * n
        nrows = rng.randint(0, 2 * n + 3)
        mode = it % 4
        # bias towards sparse rows so forcing actually succeeds sometimes
        density = rng.choice([0.15, 0.3, 0.6, 1.0])
        rows = []
        for _ in range(nrows):
            r = [0] * w
            for k in range(w):
                if rng.random() < density:
                    r[k] = entry(rng, mode)
            if rng.random() < 0.25:
                # tau-shaped edge row, the real driver's shape
                r = [0] * w
                u = rng.randrange(n)
                v = rng.randrange(n)
                x = rng.choice([(1, 0), (0, 1), (1, 1), (1, 2), (1, 3),
                                (2, 1), (1, -2), (3, 1)])
                r[2 * u] += x[0]
                r[2 * u + 1] += x[1]
                r[2 * v] -= x[0]
                r[2 * v + 1] -= x[1]
            rows.append(r)
        kind = rng.random()
        if kind < 0.1:
            rows = tuple(tuple(r) for r in rows)
        p = rng.choice(PS)

        t0kind = rng.random()
        if t0kind < 0.35:
            T0 = set()
        elif t0kind < 0.75:
            k = rng.randint(1, n)
            T0 = set(rng.sample(range(n), k))
        elif t0kind < 0.85:
            T0 = set(range(n))
        elif t0kind < 0.93:
            T0 = list(rng.sample(range(n), rng.randint(1, n)))
            T0 = T0 + T0[:1]                     # duplicate
        else:
            T0 = set(rng.sample(range(n), rng.randint(0, n)))
            T0.add(rng.choice([n, n + 3, -1, -2, 99]))

        c.check("force", (rows, n, T0, p))
        c.check("rank", (rows, p))
        # warm start from the returned closure, the search.py pattern
        fastcore._INV.clear()
        ok, T2 = PY_FORCE(rows, n, T0, p)
        if not ok and rng.random() < 0.4:
            extra = [0] * w
            j = rng.randrange(n)
            s = rng.choice([(1, 0), (0, 1), (1, 1), (1, 2)])
            extra[2 * j] = s[0]
            extra[2 * j + 1] = s[1]
            rows2 = list(rows) + [extra]
            c.check("force", (rows2, n, T2, p))


def run_ragged(c, count, seed=777):
    """Short / long / ragged rows: IndexError parity and zip truncation."""
    rng = random.Random(seed)
    for _ in range(count):
        n = rng.randint(1, 6)
        w = 2 * n
        nrows = rng.randint(1, 5)
        rows = []
        for _ in range(nrows):
            ln = rng.randint(0, w + 3)
            rows.append([rng.choice(SMALL) for _ in range(ln)])
        p = rng.choice(PS)
        T0 = set(rng.sample(range(n), rng.randint(0, n)))
        c.check("force", (rows, n, T0, p))
        c.check("rank", (rows, p))


def run_drivers(c, count, seed=99):
    """The real input distribution: build_rows over ConstructibleGraph."""
    try:
        from kakeya import ConstructibleGraph, build_rows, ZERO
        from search import POOL8, domains, graph_from_labels, prod
    except Exception as e:                       # noqa: BLE001
        print("  driver block skipped:", e)
        return 0
    rng = random.Random(seed)
    dims = [[2], [3], [4], [2, 2], [2, 3], [3, 2], [2, 2, 2], [2, 4], [2, 2, 2, 2]]
    alphabet = [ZERO] + list(POOL8)
    n0 = c.cases
    done = 0
    while done < count:
        d = rng.choice(dims)
        doms = domains(d)
        nslots = sum(len(x) for x in doms)
        labels = tuple(rng.choice(alphabet) for _ in range(nslots))
        n = prod(d)
        try:
            G = ConstructibleGraph([ZERO] + list(POOL8), d, graph_from_labels(d, doms, labels))
            R = [(rng.randrange(n), rng.choice(POOL8))
                 for _ in range(rng.randint(0, 3))]
            rows, idx = build_rows(G, R)
        except Exception:                        # noqa: BLE001
            continue
        rows = [list(r) for r in rows]
        T0 = set(rng.sample(range(n), rng.randint(0, min(n, 3))))
        c.check("force", (rows, n, T0))
        c.check("rank", (rows,))
        done += 1
    return c.cases - n0


def main():
    n_random = int(os.environ.get("DIFFTEST_N", "20000"))
    c = Counter()
    t = time.time()

    a = run_edge_cases(c)
    print("edge cases:            %6d checks, %d mismatches so far" % (a, c.mismatches))

    b0 = c.cases
    run_random(c, n_random)
    print("random sweep:          %6d checks (%d instances)" % (c.cases - b0, n_random))

    b1 = c.cases
    run_ragged(c, 2000)
    print("ragged/short rows:     %6d checks" % (c.cases - b1,))

    b2 = c.cases
    run_drivers(c, 3000)
    print("real build_rows:       %6d checks" % (c.cases - b2,))

    print("-" * 60)
    print("total checks:          %6d" % c.cases)
    print("mismatches:            %6d" % c.mismatches)
    print("expected divergences:  %6d (i64 boundary, S1 sec 5.4)" % c.divergences)
    print("elapsed:               %.1fs" % (time.time() - t))
    for r in c.reports:
        print(r)
    return 1 if c.mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
