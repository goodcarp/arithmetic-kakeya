"""Reachability analysis of the four uncovered 'found something' paths.

Pure analysis: no comparison, no claim about either implementation's numbers.
Uses only rank()/force() from src/fastcore.py plus the drivers' own constants.
"""
import sys, os, itertools
SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
sys.path.insert(0, SRC)
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import POOL3, POOL4, POOL5, POOL6, POOL8, domains, m_of_labels, graph_from_labels
from fastcore import rank, force

which = sys.argv[1]

if which == "rzero-invariant":
    # Every edge row has total column-sum (0,0) over the 2n coords, grouped as
    # (sum of even entries, sum of odd entries).  delta_j (x) (1,-1) has (1,-1).
    # So no combination of edge rows can equal it -> force(rows,n,set()) is
    # always False.  Check the invariant empirically over a big label space.
    bad = 0; tried = 0
    for d, pool in (([2,2], POOL6), ([2,2,2], POOL4), ([2,3], POOL4), ([3,2], POOL4)):
        doms = domains(d); nslots = sum(len(x) for x in doms)
        n = 1
        for z in d: n *= z
        X = [ZERO] + list(pool); alpha = [ZERO] + list(pool)
        for labels in itertools.product(alpha, repeat=nslots):
            G = ConstructibleGraph(X, d, graph_from_labels(d, doms, labels))
            rows, idx = build_rows(G, [])
            tried += 1
            for r in rows:
                s0 = sum(r[2*j] for j in range(n)); s1 = sum(r[2*j+1] for j in range(n))
                if (s0, s1) != (0, 0):
                    bad += 1
            ok, _ = force(rows, n, set())
            if ok:
                print("FORCING OBJECT", d, labels); bad += 1000000
    print(f"rzero-invariant: {tried} graphs, rows violating column-sum-zero: {bad}")

elif which == "stacked-rank":
    # stacked.py: sc = (m + r)/den with r >= den - rk (P3).  So
    #   sc >= 1 + (m - rk)/den.  sc < 7/4 requires m - rk < (3/4)*den.
    k = int(sys.argv[2]); max_t = int(sys.argv[3])
    pool = {3:POOL3,4:POOL4,5:POOL5,6:POOL6,8:POOL8}[k]
    X = [ZERO] + list(pool); d = [2,2,2]; n = 8
    f1 = {(1,): (1, 0)}
    f2 = {(1,1): (0,1), (2,1): (1,2)}
    keys3 = [(a,b,1) for a in (1,2) for b in (1,2)]
    alphabet = [ZERO] + list(pool)
    feasible = 0; total = 0; best_lb = None; mrk_min = None
    for labs in itertools.product(alphabet, repeat=4):
        total += 1
        f3 = {kk: v for kk, v in zip(keys3, labs) if v != ZERO}
        G = ConstructibleGraph(X, d, [f1, f2, f3])
        m = G.m
        base_rows, idx = build_rows(G, [])
        rk = rank(base_rows)
        if mrk_min is None or m - rk < mrk_min: mrk_min = m - rk
        for t in range(max_t + 1):
            den = n - t
            lb = Fraction(m + max(0, den - rk), den)
            if best_lb is None or lb < best_lb: best_lb = lb
            if lb < Fraction(7, 4):
                feasible += 1
                print("  POSSIBLE HIT", labs, "m", m, "rk", rk, "t", t, "lb", lb)
    print(f"stacked-rank POOL{k} max_t={max_t}: {total} interfaces, "
          f"min (m-rk) = {mrk_min}, min score lower bound = {best_lb}, "
          f"interfaces that could give a <7/4 hit: {feasible}")

elif which == "g2tall-rank":
    rows_ = int(sys.argv[2]); max_t = int(sys.argv[3])
    d = [2, rows_]; n = 2 * rows_
    keys2 = [(c, r) for c in (1, 2) for r in range(1, rows_)]
    alphabet = [ZERO] + POOL3
    X = [ZERO] + POOL3
    feasible = 0; total = 0
    for labs in itertools.product(alphabet, repeat=len(keys2)):
        total += 1
        f2 = {kk: v for kk, v in zip(keys2, labs) if v != ZERO}
        G = ConstructibleGraph(X, d, [{(1,): (1, 0)}, f2])
        base_rows, idx = build_rows(G, [])
        rk = rank(base_rows)
        for t in range(max_t + 1):
            q = n - t
            if q <= 0: continue
            cap = int(Fraction(11, 6) * q)
            if Fraction(cap, q) >= Fraction(11, 6): cap -= 1
            budget = cap - G.m
            if budget < 0 or q - rk > budget: continue
            feasible += 1
    print(f"g2tall-rank 2x{rows_} max_t={max_t}: {total} label tuples, "
          f"(tuple,t) pairs surviving the cap+rank prune: {feasible}")
