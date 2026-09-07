"""r5/kernel: warm-start CHAIN agreement on real build_rows instances.

Gap this closes: every prior lens compares SINGLE force calls.  The drivers
call force repeatedly, feeding the previous T back in as T0 while rows grow
(the monotone warm start the module docstring advertises).  A port that agreed
on every isolated call could still diverge on the chain if it carried state
across calls (the thread_local scratch) or if the returned set aliased an
internal buffer.  Here the WHOLE CHAIN is compared step by step: at every step
Python and Rust are each fed their OWN previous T, so any single-step drift
compounds instead of being reset.

Reference: fastcore._force_py with fastcore._INV.clear() before each call.
usage: k5_warmchain.py [chains] [seed]
"""
import os, random, sys
SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
sys.path.insert(0, SRC)
os.environ["KAKEYA_PURE_PY"] = "1"
import fastcore, fastcore_rs
from kakeya import ConstructibleGraph, build_rows

PYF, INV = fastcore._force_py, fastcore._INV
RSF, RSR = fastcore_rs.force, fastcore_rs.rank
PYR = fastcore._rank_py

POOL8 = [(1, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1), (1, -2), (3, 1)]
ZERO = (0, 0)
DS = [[2, 2], [2, 3], [3, 2], [2, 2, 2], [2, 4], [3, 3], [2, 2, 2, 2], [2, 5]]

NCH = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 51977
rng = random.Random(SEED)

steps = 0; bad = []
for ch in range(NCH):
    d = rng.choice(DS)
    X = [ZERO] + rng.sample(POOL8, rng.randint(1, len(POOL8)))
    G = ConstructibleGraph(X, d, [{} for _ in d])
    verts = G.vertices()
    Tpy, Trs = set(), set()
    R = []
    for step in range(rng.randint(2, 6)):
        for _ in range(rng.randint(1, 3)):
            R.append((rng.choice(verts), rng.choice(POOL8)))
        rows, idx = build_rows(G, R)
        INV.clear()
        try:
            okp, Tpy2 = PYF(rows, G.n, Tpy)
            a = ("v", bool(okp), tuple(sorted(int(x) for x in Tpy2)))
            Tpy = Tpy2
        except BaseException as e:
            a = ("e", type(e).__name__); Tpy2 = Tpy
        try:
            okr, Trs2 = RSF(rows, G.n, Trs)
            b = ("v", bool(okr), tuple(sorted(int(x) for x in Trs2)))
            Trs = Trs2
        except BaseException as e:
            b = ("e", type(e).__name__); Trs2 = Trs
        steps += 1
        if a != b:
            bad.append((ch, step, d, X, R, a, b))
            break
        # also rank the same rows in the middle of the chain, to make the
        # thread_local row buffer be reused between two force calls
        INV.clear()
        ra, rb = PYR(rows), RSR(rows)
        steps += 1
        if ra != rb:
            bad.append((ch, step, d, X, R, ("rank", ra), ("rank", rb)))
            break
    if len(bad) > 4:
        break

print("k5_warmchain seed=%d chains=%d steps=%d mismatches=%d" % (SEED, ch + 1, steps, len(bad)))
for r in bad[:5]:
    print("  MISMATCH chain=%d step=%d d=%r X=%r" % (r[0], r[1], r[2], r[3]))
    print("     R=%r" % (r[4],))
    print("     py=%r rs=%r" % (r[5], r[6]))
sys.exit(1 if bad else 0)
