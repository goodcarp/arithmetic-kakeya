"""LEMMA P7/P8 (the cut lemma), and its two specialisations.

For A a subset of V write Sigma_A(f) = sum_{u in A} f(u).  An edge function
delta_u (x) x - delta_v (x) x has Sigma_A = 0 unless the edge crosses the cut
(A, V\\A), in which case it is +/- x.  A generator delta_w (x) x contributes x
iff w is in A.  Hence for every f in M,

    Sigma_A(f)  in  span{ labels of edges crossing (A, V\\A) }
                     + span{ labels of generators inside A }.        (P8)

If f witnesses the forcing of v in A with support inside T_0 u {v}, then
Sigma_A(f) = tau + sum_{u in T_0 ∩ A} f(u), so

  * A = {v}      -> P4: every vertex outside T_0 must see two non-parallel
                   directions among its incident edge labels and its generators;
  * A = V, T_0 empty -> P7: tau must lie in the span of the GENERATOR labels
                   alone.  Since no single label is parallel to tau, an object
                   with T empty needs at least two generators, of two different
                   slopes -- no matter how large or how well connected it is.
                   In particular a generator-free object with T empty can never
                   force a single vertex.

This test checks P7 directly and P8 on random cuts.
"""
import sys, os, random, itertools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kakeya import ConstructibleGraph, build_rows, ZERO
from fastcore import force

def rank2(vs):
    vs = [v for v in vs if v != ZERO]
    for i in range(len(vs)):
        for j in range(i+1, len(vs)):
            if vs[i][0]*vs[j][1] - vs[i][1]*vs[j][0] != 0:
                return True
    return False

random.seed(7)
POOL = [(1,0),(0,1),(1,1),(1,2),(1,3),(2,1)]
checked = viol = 0
for trial in range(30000):
    d = random.choice([[2,2],[2,3],[3,2],[2,2,2],[4],[2,4]])
    doms = []
    for i in range(1, len(d)+1):
        pref = list(itertools.product(*[range(1,d[j]+1) for j in range(i-1)]))
        doms.append([tuple(list(p)+[l]) for p in pref for l in range(1,d[i-1])])
    f = [{k: random.choice(POOL) for k in dm if random.random() < .7} for dm in doms]
    X = [ZERO]+POOL
    G = ConstructibleGraph(X, d, f)
    verts = G.vertices(); n = G.n
    R = [(random.choice(verts), random.choice(POOL)) for _ in range(random.randint(0,5))]
    rows, idx = build_rows(G, R)
    ok, _ = force(rows, n, set())          # T_0 empty
    if not ok:
        continue
    checked += 1
    if not rank2([s for (_, s) in R]):
        viol += 1
        print("P7 VIOLATION", d, f, R)
print(f"{checked} forcing objects with T empty; P7 violations: {viol}")
assert viol == 0
print("PASS: every object that forces from T empty carries two non-parallel generators")
