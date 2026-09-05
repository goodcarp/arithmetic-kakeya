"""LEMMA P6 (T beats a double generator).
Putting a vertex v into T is exactly equivalent, for the forcing dynamics, to
adding delta_v (x) Q^2 to the module -- i.e. to giving v two non-parallel
generators.  (If f is supported in T u {v} u {e}, then f - delta_v (x) f(v) is
supported in T u {e} and lies in M + delta_v (x) Q^2, and conversely.)  But the
two cost differently: two generators cost 2 in the numerator, while v in T costs
1 in the denominator.  Since
        (p-2)/(q-1) < p/q   <=>   p < 2q   <=>   score < 2,
every object with score < 2 that carries two generators at one vertex is
strictly improved by deleting them and putting that vertex in T.

COROLLARY: in an optimal object (score < 2) every vertex carries at most one
generator, and r <= n.

This test performs the swap on random objects and checks (a) the forcing still
succeeds, (b) the score strictly drops.
"""
import sys, os, random, itertools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from fastcore import force

random.seed(99)
POOL = [(1,0),(0,1),(1,1),(1,2),(1,3)]
checked = broke = notbetter = 0
for trial in range(60000):
    d = random.choice([[2,2],[2,3],[3,2],[2,2,2],[4],[3]])
    doms = []
    for i in range(1, len(d)+1):
        pref = list(itertools.product(*[range(1,d[j]+1) for j in range(i-1)]))
        doms.append([tuple(list(p)+[l]) for p in pref for l in range(1,d[i-1])])
    f = [{k: random.choice(POOL) for k in dm if random.random() < .6} for dm in doms]
    X = [ZERO]+POOL
    G = ConstructibleGraph(X, d, f)
    verts = G.vertices(); n = G.n
    idx = {v: j for j, v in enumerate(verts)}
    v = random.choice(verts)
    a, b = random.sample(POOL, 2)
    if a[0]*b[1]-a[1]*b[0] == 0:
        continue
    R = [(v, a), (v, b)] + [(random.choice(verts), random.choice(POOL))
                            for _ in range(random.randint(0,2))]
    R = [(w, s) for (w, s) in R if not (w == v and (w, s) not in [(v,a),(v,b)])]
    rows, _ = build_rows(G, R)
    ok, _ = force(rows, n, set())
    if not ok:
        continue
    sc = Fraction(G.m + len(R), n)
    checked += 1
    # swap: drop the two generators at v, put v into T
    R2 = [(w, s) for (w, s) in R if w != v]
    rows2, _ = build_rows(G, R2)
    ok2, _ = force(rows2, n, {idx[v]})
    sc2 = Fraction(G.m + len(R2), n - 1)
    if not ok2:
        broke += 1
        print("SWAP BROKE FORCING", d, f, R, v)
    elif sc < 2 and not (sc2 < sc):
        notbetter += 1
        print("SWAP DID NOT IMPROVE", sc, "->", sc2)
print(f"{checked} forcing objects with a double-generator vertex")
print(f"   forcing broken by the swap: {broke}")
print(f"   score not strictly improved (among those with score < 2): {notbetter}")
assert broke == 0 and notbetter == 0
print("PASS: P6 holds on every sampled instance")
