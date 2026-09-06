"""Independent re-implementation of g2_tall's OUTER loops (no min_generators),
counting label tuples walked and (graph,T0) pairs that reach min_generators.
Transcribed from src/g2_tall.py.  usage: pairs_g2.py <rows> <max_t>"""
import sys, itertools
sys.path.insert(0, "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src")
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import local_requirement, POOL3
from fastcore import rank

rows_ = int(sys.argv[1]); max_t = int(sys.argv[2])
POOL = POOL3; X = [ZERO] + POOL
d = [2, rows_]; n = 2 * rows_
keys2 = [(c, r) for c in (1, 2) for r in range(1, rows_)]
alphabet = [ZERO] + POOL
tuples = pairs = 0
for labs in itertools.product(alphabet, repeat=len(keys2)):
    tuples += 1
    f2 = {k: v for k, v in zip(keys2, labs) if v != ZERO}
    G = ConstructibleGraph(X, d, [{(1,): (1, 0)}, f2])
    base_rows, idx = build_rows(G, [])
    rk = rank(base_rows)
    for t in range(max_t + 1):
        q = n - t
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
            pairs += 1
print(f"g2_tall 2x{rows_} max_t={max_t}: walked={tuples} pairs={pairs}")
