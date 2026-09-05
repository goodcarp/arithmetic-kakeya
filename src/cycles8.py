"""Targeted shot: 2-regular constructible objects on n = 8 (d = 2x2x2).

Rationale.  If every vertex has degree exactly 2 then sum of degrees = 2n gives
m = n, and the score is 1 + r/n.  Beating 1.675 at n = 8 therefore needs only
r <= 5 (score 13/8 = 1.625).  The certified 7/4 object is exactly the n = 4
2-regular case with r = 3.  This enumerates every 2-regular constructible graph
on the 2x2x2 box over a rich slope alphabet and asks for the cheapest generator
set.
"""
import sys, os, itertools, time, json
sys.path.insert(0, os.path.dirname(__file__))
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import min_generators, local_requirement, POOL6, POOL8
from fastcore import rank

d = [2, 2, 2]
n = 8
K1 = [(1,)]
K2 = [(1, 1), (2, 1)]
K3 = [(a, b, 1) for a in (1, 2) for b in (1, 2)]
SLOTS = [("f1", k) for k in K1] + [("f2", k) for k in K2] + [("f3", k) for k in K3]


def build(pattern, labels, X):
    f1, f2, f3 = {}, {}, {}
    li = 0
    for (lvl, key), on in zip(SLOTS, pattern):
        if not on:
            continue
        lab = labels[li]; li += 1
        (f1 if lvl == "f1" else f2 if lvl == "f2" else f3)[key] = lab
    return ConstructibleGraph(X, d, [f1, f2, f3])


def main(pool, target=Fraction(67, 40), deg=2, tlimit=2400):
    X = [ZERO] + list(pool)
    t0 = time.time()
    # step 1: which presence patterns give a deg-regular graph with m = n
    good = []
    for pattern in itertools.product([0, 1], repeat=len(SLOTS)):
        G = build(pattern, [pool[0]] * sum(pattern), X)
        if G.m != n:
            continue
        degs = {v: 0 for v in G.vertices()}
        for (u, v, x) in G.edges():
            degs[u] += 1; degs[v] += 1
        if all(v == deg for v in degs.values()):
            good.append(pattern)
    print(f"{len(good)} presence patterns are {deg}-regular with m = {n}", flush=True)
    best, bestobj, hits = None, None, []
    tested = 0
    for pattern in good:
        npres = sum(pattern)
        for labels in itertools.product(pool, repeat=npres):
            if time.time() - t0 > tlimit:
                print("TIME LIMIT", flush=True)
                return best, bestobj, hits, tested
            G = build(pattern, labels, X)
            base_rows, idx = build_rows(G, [])
            rk = rank(base_rows)
            for t in (0, 1, 2):
                den = n - t
                budget = int(target * den) - G.m
                if budget < 0 or den - rk > budget:
                    continue
                for T0t in ([()] if t == 0 else itertools.combinations(range(n), t)):
                    T0 = set(T0t)
                    mt, mand = local_requirement(G, idx, n, T0, pool)
                    if mt > budget:
                        continue
                    tested += 1
                    gens = min_generators(base_rows, n, T0, pool, budget, mand)
                    if gens is None:
                        continue
                    sc = Fraction(G.m + len(gens), den)
                    if best is None or sc < best:
                        best, bestobj = sc, (pattern, labels, len(gens), sorted(T0), t)
                        print(f"  new best {sc} = {float(sc):.4f}  pattern={pattern} "
                              f"labels={labels} r={len(gens)} t={t}", flush=True)
                    if sc <= target:
                        hits.append((str(sc), pattern, labels, gens, sorted(T0)))
    return best, bestobj, hits, tested


if __name__ == "__main__":
    pool = POOL8 if len(sys.argv) > 1 and sys.argv[1] == "8" else POOL6
    b, bo, h, tested = main(pool)
    print("RESULT", json.dumps({"tag": "cycles8", "pool": len(pool),
          "best": str(b) if b else None, "hits": len(h), "tested": tested}), flush=True)
    for x in h[:20]:
        print("HITOBJ", json.dumps(x, default=str), flush=True)
