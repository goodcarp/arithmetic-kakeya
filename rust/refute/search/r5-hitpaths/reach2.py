"""Refined reachability for stacked's `for x in h[:5]` block (sc < 7/4).

Lower bound on r used here is the driver's OWN two prunes, nothing new:
  P3  r >= den - rank(base_rows)
  P4  r >= local_requirement(...)[0]        (mandatory generator positions)
  P6  if any mandatory vertex needs 2 generators, min_generators returns None
      (search._dir_choices returns [] for k >= 2), so that (graph,T0) is dead.
sc = (m + r)/den, so sc >= (m + max(P3,P4))/den.
"""
import sys, os, itertools
SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
sys.path.insert(0, SRC)
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import (POOL3, POOL4, POOL5, POOL6, POOL8, local_requirement,
                    _dir_choices)
from fastcore import rank

k = int(sys.argv[1]); max_t = int(sys.argv[2])
target = Fraction(sys.argv[3]) if len(sys.argv) > 3 else Fraction(7, 4)
pool = {3:POOL3,4:POOL4,5:POOL5,6:POOL6,8:POOL8}[k]
X = [ZERO] + list(pool); d = [2,2,2]; n = 8
f1 = {(1,): (1, 0)}
f2 = {(1,1): (0,1), (2,1): (1,2)}
keys3 = [(a,b,1) for a in (1,2) for b in (1,2)]
alphabet = [ZERO] + list(pool)
alive = 0; total = 0; best_lb = None; examples = []
for labs in itertools.product(alphabet, repeat=4):
    total += 1
    f3 = {kk: v for kk, v in zip(keys3, labs) if v != ZERO}
    G = ConstructibleGraph(X, d, [f1, f2, f3])
    m = G.m
    base_rows, idx = build_rows(G, [])
    rk = rank(base_rows)
    for t in range(max_t + 1):
        den = n - t
        budget = int(target * den) - m          # the driver's own budget
        if budget < 0 or den - rk > budget:
            continue
        for T0t in ([()] if t == 0 else itertools.combinations(range(n), t)):
            T0 = set(T0t)
            mt, mand = local_requirement(G, idx, n, T0, pool)
            if mt > budget:
                continue
            if any(len(_dir_choices(ex, pool, kk)) == 0 for (_j, ex, kk) in mand):
                continue                         # P6: min_generators returns None
            rlb = max(den - rk, mt, 0)
            lb = Fraction(m + rlb, den)
            if best_lb is None or lb < best_lb:
                best_lb = lb
            if lb < Fraction(7, 4):
                alive += 1
                if len(examples) < 5:
                    examples.append((labs, m, rk, t, sorted(T0), mt, str(lb)))
print(f"POOL{k} max_t={max_t} target={target}: {total} interfaces; "
      f"(graph,T0) pairs that survive P3+P4+P6 AND could still score < 7/4: {alive}; "
      f"min achievable-score lower bound = {best_lb}")
for e in examples:
    print("   example", e)
