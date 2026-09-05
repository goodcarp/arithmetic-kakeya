"""Probe: can an object with NO generators and NO free vertices force at all?

Such an object would have score exactly m/n, so it is the cheapest possible shape.
Nothing in the structure lemmas forbids it: the first witness must be
delta_v (x) tau supported on one vertex, and its image under psi(a,b) = a+b is
zero, so the component-sum obstruction does not bite.  This enumerates the whole
label space for small boxes and simply runs the forcing once per graph -- no
generator search, so it is ~500x cheaper than the general scan.
"""
import sys, os, itertools, json, time, random
sys.path.insert(0, os.path.dirname(__file__))
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import domains, m_of_labels, graph_from_labels, POOL4, POOL6
from fastcore import force
from math import prod


def sweep(d, pool, limit=None, seed=0, max_r=0, tlimit=1800):
    doms = domains(d)
    nslots = sum(len(x) for x in doms)
    n = prod(d)
    X = [ZERO] + list(pool)
    alphabet = [ZERO] + list(pool)
    if limit is None:
        it = itertools.product(alphabet, repeat=nslots)
        total = len(alphabet) ** nslots
    else:
        rng = random.Random(seed)
        it = (tuple(rng.choice(alphabet) for _ in range(nslots)) for _ in range(limit))
        total = limit
    best = None; cnt = 0; forcing = 0
    t0 = time.time()
    for labels in it:
        cnt += 1
        if time.time() - t0 > tlimit:
            break
        m = m_of_labels(d, doms, labels)
        G = ConstructibleGraph(X, d, graph_from_labels(d, doms, labels))
        rows, idx = build_rows(G, [])
        ok, _ = force(rows, n, set())
        if ok:
            forcing += 1
            sc = Fraction(m, n)
            if best is None or sc < best:
                best = sc
                print(f"  generator-free forcing object! m={m} n={n} score={sc}"
                      f" labels={labels}", flush=True)
    return best, cnt, total, forcing, time.time() - t0


if __name__ == "__main__":
    jobs = [([2, 2], POOL6, None), ([2, 2, 2], POOL4, None), ([2, 3], POOL4, None),
            ([3, 2], POOL4, None), ([2, 2, 2], POOL6, 60000), ([2, 2, 2, 2], POOL4, 60000)]
    for d, pool, lim in jobs:
        b, c, tot, fo, el = sweep(d, pool, limit=lim, tlimit=600)
        print("RESULT", json.dumps({"tag": "rzero", "d": d, "pool": len(pool),
              "scanned": c, "total": tot, "forcing_objects": fo,
              "best_score": str(b) if b else None,
              "complete": lim is None and c >= tot, "seconds": round(el, 1)}), flush=True)
