"""Randomised cross-check: the O(n) per-candidate engine and the one-row-space
per-round engine must agree, mod p and over Q."""
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kakeya import ConstructibleGraph, ForcingProblem, build_rows, fast_force

random.seed(20260824)
XS = [(0,0),(1,0),(0,1),(1,1),(1,2),(1,3),(2,1)]
bad = 0
trials = 0
for trial in range(300):
    d = random.choice([[2],[3],[2,2],[2,3],[3,2],[2,2,2],[4],[2,4]])
    k = len(d)
    f = []
    for i in range(1, k+1):
        dom = []
        def rec(pref, j):
            if j == i-1:
                for last in range(1, d[i-1]):
                    dom.append(tuple(pref+[last]))
                return
            for e in range(1, d[j]+1):
                rec(pref+[e], j+1)
        rec([], 0)
        f.append({key: random.choice(XS) for key in dom})
    G = ConstructibleGraph(XS, d, f)
    verts = G.vertices()
    R = [(random.choice(verts), random.choice(XS[1:])) for _ in range(random.randint(0,4))]
    T = random.sample(verts, random.randint(0, min(2, len(verts))))
    fp = ForcingProblem(G, R, T)
    ok1, T1, _ = fp.run(backend="exact", use_local=False)
    rows, idx = build_rows(G, R)
    T0 = set(idx[t] for t in T)
    ok2, T2, _ = fast_force(rows, G.n, T0, backend="exact")
    ok3, T3, _ = fast_force(rows, G.n, T0, backend="modp")
    fp2 = ForcingProblem(G, R, T)
    ok4, T4, _ = fp2.run(backend="exact", use_local=True)
    trials += 1
    same = (ok1 == ok2 == ok3 == ok4) and (set(idx[v] for v in T1) == T2 == T3)
    if not same:
        bad += 1
        print("MISMATCH", d, f, R, T, ok1, ok2, ok3, ok4)
print(f"{trials} random instances, {bad} mismatches")
assert bad == 0
print("PASS: all four engine configurations agree")
