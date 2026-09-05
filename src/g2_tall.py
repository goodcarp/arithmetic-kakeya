"""Goal 2, focused: the 11/6 record object is the 2 x 3 box with the single level-1
bundle (1,0) carrying all horizontal edges.  This enumerates the same shape one, two
and three rows taller -- 2 x r boxes with f_1(1) = (1,0) and every level-2 label free
over the three-slope alphabet -- and asks for the cheapest generator set.

Targets (strictly below 11/6):  q=8 -> 14/8,  q=10 -> 9/5,  q=11 -> 20/11, q=12 -> 7/4.
"""
import sys, os, itertools, json, time
sys.path.insert(0, os.path.dirname(__file__))
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import min_generators, local_requirement, POOL3
from fastcore import rank

POOL = POOL3
X = [ZERO] + POOL


def run(rows_, max_t=1, tlimit=900):
    d = [2, rows_]
    n = 2 * rows_
    keys2 = [(c, r) for c in (1, 2) for r in range(1, rows_)]
    alphabet = [ZERO] + POOL
    best, bestobj, hits = None, None, []
    t0 = time.time()
    for labs in itertools.product(alphabet, repeat=len(keys2)):
        if time.time() - t0 > tlimit:
            print(f"  [2x{rows_}] TIME LIMIT", flush=True); break
        f2 = {k: v for k, v in zip(keys2, labs) if v != ZERO}
        G = ConstructibleGraph(X, d, [{(1,): (1, 0)}, f2])
        base_rows, idx = build_rows(G, [])
        rk = rank(base_rows)
        for t in range(max_t + 1):
            q = n - t
            # strict improvement on 11/6
            cap = int(Fraction(11, 6) * q)
            if Fraction(cap, q) >= Fraction(11, 6):
                cap -= 1
            budget = cap - G.m
            if budget < 0 or q - rk > budget:
                continue
            for T0t in ([()] if t == 0 else itertools.combinations(range(n), t)):
                T0 = set(T0t)
                mt, mand = local_requirement(G, idx, n, T0, POOL)
                if mt > budget:
                    continue
                gens = min_generators(base_rows, n, T0, POOL, budget, mand)
                if gens is None:
                    continue
                sc = Fraction(G.m + len(gens), q)
                if best is None or sc < best:
                    best, bestobj = sc, (labs, G.m, gens, sorted(T0), t)
                    print(f"  [2x{rows_}] score {sc} = {float(sc):.4f}  m={G.m} "
                          f"r={len(gens)} t={t} labels={labs} gens={gens}", flush=True)
                hits.append((str(sc), labs, G.m, [list(g[1]) for g in gens], sorted(T0)))
    return best, bestobj, hits, time.time() - t0


if __name__ == "__main__":
    for rows_ in (4, 5, 6):
        b, bo, h, el = run(rows_, max_t=1, tlimit=700)
        print("RESULT", json.dumps({"tag": f"g2_tall_2x{rows_}", "d": [2, rows_],
              "pool": 3, "max_t": 1, "target": "<11/6",
              "best": str(b) if b else None, "hits": len(h),
              "complete": (el < 700), "seconds": round(el, 1)}), flush=True)
