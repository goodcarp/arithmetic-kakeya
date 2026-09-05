"""Empirical check of Lemma C (PREDICTIONS.md 2.1) on random forcing objects:
for every slope c (each pool slope plus an unused one), every component of the graph
with c-parallel edges removed must contain a T0 vertex or a generator not parallel to c."""
import sys, os, random, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import domains, graph_from_labels, POOL6, gen_row
from fastcore import force

def par(a, b): return a[0]*b[1] - a[1]*b[0] == 0

def comps(n, edges, c):
    parent = list(range(n))
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for (u, v, x) in edges:
        if not par(x, c):
            a, b = find(u), find(v)
            if a != b: parent[a] = b
    out = {}
    for v in range(n): out.setdefault(find(v), []).append(v)
    return list(out.values())

rng = random.Random(11)
checked = 0; forced_objs = 0; violations = 0
for trial in range(40000):
    d = rng.choice([[2, 2], [2, 3], [3, 2], [2, 2, 2], [4]])
    doms = domains(d); nslots = sum(len(x) for x in doms)
    alphabet = [ZERO] + POOL6
    labels = tuple(rng.choice(alphabet) for _ in range(nslots))
    X = [ZERO] + POOL6
    G = ConstructibleGraph(X, d, graph_from_labels(d, doms, labels))
    n = G.n
    base_rows, idx = build_rows(G, [])
    edges = [(idx[u], idx[v], x) for (u, v, x) in G.edges()]
    t = rng.choice([0, 0, 1, 2])
    T0 = set(rng.sample(range(n), t))
    r = rng.randint(0, n)
    gens = [(v, rng.choice(POOL6)) for v in rng.sample(range(n), r)]
    rows = base_rows + [gen_row(n, v, s) for (v, s) in gens]
    ok, T = force(rows, n, T0)
    checked += 1
    if not ok: continue
    forced_objs += 1
    for c in POOL6 + [(2, 3), (5, -2)]:
        for K in comps(n, edges, c):
            if any(v in T0 for v in K): continue
            if any(v in K and not par(s, c) for (v, s) in gens): continue
            violations += 1
            print("VIOLATION", d, labels, T0, gens, c, K)
print(f"checked={checked} forcing_objects={forced_objs} lemma_C_violations={violations}")
