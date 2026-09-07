"""Two checks the record leans on but never states as a computation.

A. The Goal-2 symmetry group.  The workbench says two labels may always be
   normalised to (1,0),(0,1) by the projective group fixing tau (slope -1).
   For GOAL 2 the alphabet is PINNED to slopes {0, oo, 1}, so the usable
   symmetry is the subgroup that fixes -1 AND permutes {0, oo, 1}.  Enumerate
   all 6 permutations, build the unique Moebius map realising each, and test
   whether it fixes -1.

B. The 4-cycle floor PREDICTIONS 2.2 imports from the n4_p6_t1 scan ("r >= 3
   at t=0 and r >= 2 at t=1 for every 4-cycle").  Recompute it directly with
   no target budget in the way: for every POOL6 label triple on d=[2,2] with
   all three bundles present -- exactly the component shape of the cycles8
   two-4-cycle patterns -- report the minimum |R| at t=0 and at t=1.
"""
import sys, os, itertools
from fractions import Fraction as F
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "..", "..", "..", "src")
sys.path.insert(0, os.path.abspath(SRC))
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import min_generators, local_requirement, POOL6

# ---------- A ----------
print("== A. Moebius maps permuting {0, oo, 1}; does each fix -1? ==")
P0, PI, P1 = (F(0), F(1)), (F(1), F(0)), (F(1), F(1))   # [x:y], slope = x/y
NAME = {P0: "0", PI: "oo", P1: "1"}
TAU = (F(-1), F(1))

def matmul(A, B):
    return [[A[0][0]*B[0][0]+A[0][1]*B[1][0], A[0][0]*B[0][1]+A[0][1]*B[1][1]],
            [A[1][0]*B[0][0]+A[1][1]*B[1][0], A[1][0]*B[0][1]+A[1][1]*B[1][1]]]

def inv(A):
    det = A[0][0]*A[1][1] - A[0][1]*A[1][0]
    assert det != 0
    return [[A[1][1], -A[0][1]], [-A[1][0], A[0][0]]]

def to_std(a, b, c):
    """matrix sending a->0, b->1, c->oo"""
    lam = c[1]*b[0] - c[0]*b[1]
    mu  = a[1]*b[0] - a[0]*b[1]
    return [[lam*a[1], -lam*a[0]], [mu*c[1], -mu*c[0]]]

def apply(M, p):
    x = M[0][0]*p[0] + M[0][1]*p[1]
    y = M[1][0]*p[0] + M[1][1]*p[1]
    return (x, y)

def same(p, q):
    return p[0]*q[1] - p[1]*q[0] == 0

pts = [P0, PI, P1]
fixers = []
for perm in itertools.permutations(pts):
    M = matmul(inv(to_std(*perm)), to_std(*pts))
    img = apply(M, TAU)
    ok = same(img, TAU)
    s = "oo" if img[1] == 0 else str(F(img[0], img[1]))
    print("  {} -> {:>8}   -1 |-> {:>5}   fixes -1: {}".format(
        " ".join(NAME[p] for p in pts), " ".join(NAME[p] for p in perm), s, ok))
    if ok:
        fixers.append(tuple(NAME[p] for p in perm))
print("  => usable Goal-2 label symmetry group has order", len(fixers), fixers)

# ---------- B ----------
print()
print("== B. minimum |R| over every all-present POOL6 4-cycle on d=[2,2] ==")
X = [ZERO] + list(POOL6)
d, n = [2, 2], 4
obs = {0: {}, 1: {}}
for (a, b, c) in itertools.product(POOL6, repeat=3):
    G = ConstructibleGraph(X, d, [{(1,): a}, {(1, 1): b, (2, 1): c}])
    assert G.m == 4
    base_rows, idx = build_rows(G, [])
    for t in (0, 1):
        for T0t in ([()] if t == 0 else itertools.combinations(range(n), t)):
            T0 = set(T0t)
            mt, mand = local_requirement(G, idx, n, T0, POOL6)
            found = None
            for budget in range(0, 6):
                if mt > budget:
                    continue
                g = min_generators(base_rows, n, T0, POOL6, budget, mand)
                if g is not None:
                    found = len(g)
                    break
            key = found if found is not None else ">5"
            obs[t][key] = obs[t].get(key, 0) + 1
for t in (0, 1):
    ints = [k for k in obs[t] if isinstance(k, int)]
    mn = min(ints) if ints else None
    print(f"  t={t}: |R| histogram {dict(sorted(obs[t].items(), key=str))}")
    print(f"        MINIMUM |R| = {mn}  ->  min score = {F(4+mn, n-t)}"
          f" = {float(F(4+mn, n-t)):.4f}")
