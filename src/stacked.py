"""Targeted experiment: two copies of the certified 7/4 trapezoid stacked along a
third coordinate, searching every interface label pattern and the cheapest
generator set.  Tests directly whether an interleaved forcing order across the two
blocks can buy anything over the block's own score (cf. the Chain remark)."""
import sys, os, itertools, time
sys.path.insert(0, os.path.dirname(__file__))
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import min_generators, local_requirement, POOL4, POOL6
from fastcore import force, rank

def run(pool, max_t=2, target=Fraction(7, 4)):
    X = [ZERO] + list(pool)
    d = [2, 2, 2]
    n = 8
    f1 = {(1,): (1, 0)}
    f2 = {(1, 1): (0, 1), (2, 1): (1, 2)}
    keys3 = [(a, b, 1) for a in (1, 2) for b in (1, 2)]
    alphabet = [ZERO] + list(pool)
    best = None; bestobj = None; hits = []
    t0 = time.time()
    for labs in itertools.product(alphabet, repeat=4):
        f3 = {k: v for k, v in zip(keys3, labs) if v != ZERO}
        G = ConstructibleGraph(X, d, [f1, f2, f3])
        m = G.m
        base_rows, idx = build_rows(G, [])
        rk = rank(base_rows)
        for t in range(max_t + 1):
            den = n - t
            budget = int(target * den) - m
            if budget < 0 or den - rk > budget:
                continue
            for T0t in ([()] if t == 0 else itertools.combinations(range(n), t)):
                T0 = set(T0t)
                mt, mand = local_requirement(G, idx, n, T0, pool)
                if mt > budget:
                    continue
                gens = min_generators(base_rows, n, T0, pool, budget, mand)
                if gens is None:
                    continue
                sc = Fraction(m + len(gens), den)
                if best is None or sc < best:
                    best = sc
                    bestobj = (labs, m, gens, sorted(T0), t)
                if sc < Fraction(7, 4):
                    hits.append((sc, labs, m, gens, sorted(T0)))
    return best, bestobj, hits, time.time() - t0

if __name__ == "__main__":
    for name, pool in (("POOL4", POOL4), ("POOL6", POOL6)):
        b, bo, h, el = run(pool)
        print(f"{name}: best score over all interfaces = {b} ({float(b) if b else None})")
        print(f"   witness: interface labels={bo[0]} m={bo[1]} r={len(bo[2])} "
              f"t={bo[4]} T0={bo[3]}")
        print(f"   strictly-better-than-7/4 hits: {len(h)}   [{el:.1f}s]")
        for x in h[:5]:
            print("      ", x)
