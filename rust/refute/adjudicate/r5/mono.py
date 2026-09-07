"""Adversarial test of the load-bearing lemma in finding 3/10 (lens hitpaths):

   for a FIXED stacked interface labelling `labs` (drawn from the SMALL pool's
   alphabet), a FIXED t and a FIXED T0, growing the pool cannot raise the score.

If that ever fails, min score(POOL3) >= min score(POOL4) does not follow from
the complete POOL4 run and the finding collapses.

Reimplements stacked.run's inner body verbatim (copied from src/stacked.py) but
loops the pool on the OUTSIDE of a fixed configuration.  Every constant that
stacked.py hardcodes (d, n, f1, f2, keys3, target 7/4, the 7/4 hit threshold)
is kept at its literal value; only `pool` varies, which is the thing under test.

usage: mono.py <max_t> <stride>   (stride subsamples the 256 POOL3 interfaces)
"""
import sys, os, itertools, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import min_generators, local_requirement, POOL3, POOL4, POOL5, POOL6, POOL8
from fastcore import force, rank
import fastcore

max_t = int(sys.argv[1]); stride = int(sys.argv[2]) if len(sys.argv) > 2 else 1
pools = [("POOL3", POOL3), ("POOL4", POOL4), ("POOL5", POOL5), ("POOL6", POOL6)]

d = [2, 2, 2]; n = 8
f1 = {(1,): (1, 0)}
f2 = {(1, 1): (0, 1), (2, 1): (1, 2)}
keys3 = [(a, b, 1) for a in (1, 2) for b in (1, 2)]
target = Fraction(7, 4)

def score_for(pool, labs, t, T0):
    """stacked.run's body for ONE (labs, t, T0); returns (m, r, sc) or None."""
    X = [ZERO] + list(pool)
    f3 = {k: v for k, v in zip(keys3, labs) if v != ZERO}
    G = ConstructibleGraph(X, d, [f1, f2, f3])
    m = G.m
    base_rows, idx = build_rows(G, [])
    rk = rank(base_rows)
    den = n - t
    budget = int(target * den) - m
    if budget < 0 or den - rk > budget:
        return ("PRUNE_BUDGET", m, rk)
    mt, mand = local_requirement(G, idx, n, T0, pool)
    if mt > budget:
        return ("PRUNE_LOCAL", m, mt)
    gens = min_generators(base_rows, n, T0, pool, budget, mand)
    if gens is None:
        return ("NONE", m, budget)
    return ("OK", m, len(gens), Fraction(m + len(gens), den))

alph3 = [ZERO] + list(POOL3)
labsets = list(itertools.product(alph3, repeat=4))[::stride]
bad = 0; cmp_n = 0; okmin = {}
t0 = time.time()
for labs in labsets:
    for t in range(max_t + 1):
        for T0t in ([()] if t == 0 else itertools.combinations(range(n), t)):
            T0 = set(T0t)
            res = []
            for name, pool in pools:
                fastcore._INV.clear()
                res.append((name, score_for(pool, labs, t, T0)))
            # monotonicity: r non-increasing, and any OK stays OK, as pool grows
            for i in range(len(res) - 1):
                a, b = res[i][1], res[i + 1][1]
                cmp_n += 1
                if a[0] == "OK":
                    if b[0] != "OK":
                        print("BREAK-OK", labs, t, sorted(T0), res[i], res[i+1]); bad += 1
                    elif b[2] > a[2]:
                        print("BREAK-R", labs, t, sorted(T0), res[i], res[i+1]); bad += 1
            for name, r in res:
                if r[0] == "OK":
                    if name not in okmin or r[3] < okmin[name]:
                        okmin[name] = r[3]
print(f"mono: {len(labsets)} interfaces x max_t={max_t}, {cmp_n} pairwise comparisons, "
      f"{bad} monotonicity breaks   [{time.time()-t0:.1f}s]")
print("  min score seen per pool (over this subsample):", {k: str(v) for k, v in okmin.items()})
