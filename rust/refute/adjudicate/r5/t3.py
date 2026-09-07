"""Close the finding's `max_t <= 2` caveat.

stacked's hit test is `sc = (m + r)/(n - t) < 7/4` with n = 8, and for d=[2,2,2]
G.m = 8 + (#nonzero level-3 interface labels) >= 8 (kakeya.py:86-93; i=1 mult 4
x1 pinned label, i=2 mult 2 x2 pinned labels, i=3 mult 1).  So a hit needs

    m + r < 7/4 * (8 - t)

  t=0,1,2 : covered by the complete POOL4/POOL6 runs (logs/stacked.log)
  t=3     : m + r < 8.75  ->  m + r <= 8  ->  m = 8 (all-ZERO interface), r = 0
  t>=4    : m + r < 7 <= m   ->  IMPOSSIBLE for every pool and every target
  t=8     : den = 0, out of contract (Python ZeroDivisionError)

So the ONLY case above max_t=2 is: all-ZERO interface, zero generators, some
3-subset T0 that the edge rows alone force.  r = 0 means no pool is involved,
so one check settles pools 3,4,5,6 AND 8.  C(8,3) = 56 calls.
"""
import sys, os, itertools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import POOL3, POOL4, POOL5, POOL6, POOL8
from fastcore import force, rank
import fastcore

d = [2, 2, 2]; n = 8
f1 = {(1,): (1, 0)}
f2 = {(1, 1): (0, 1), (2, 1): (1, 2)}
for pname, pool in (("POOL3", POOL3), ("POOL4", POOL4), ("POOL5", POOL5),
                    ("POOL6", POOL6), ("POOL8", POOL8)):
    fastcore._INV.clear()
    X = [ZERO] + list(pool)
    G = ConstructibleGraph(X, d, [f1, f2, {}])       # all-ZERO interface
    m = G.m
    base_rows, idx = build_rows(G, [])
    rk = rank(base_rows)
    forced = []
    for T0t in itertools.combinations(range(n), 3):
        ok, T2 = force(base_rows, n, set(T0t))
        if ok:
            forced.append(T0t)
    print(f"{pname}: all-ZERO interface m={m} rank(base_rows)={rk}; "
          f"3-subsets T0 that force with r=0: {len(forced)} / 56"
          + (f"  -> HIT at t=3, sc={Fraction(m,5)}" if forced else "  -> no t=3 hit"))
# and the impossibility above t=3
for t in range(4, 8):
    print(f"  t={t}: hit needs m+r < {Fraction(7,4)*(8-t)} but m >= 8  -> impossible")
