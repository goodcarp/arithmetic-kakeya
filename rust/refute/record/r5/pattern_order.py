# Independent recomputation of cycles8's 5 presence patterns, in itertools.product
# order, with their cycle types.  Read-only against src/.
import sys, os, itertools
SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
sys.path.insert(0, SRC)
from kakeya import ConstructibleGraph, ZERO
from search import POOL6
import cycles8 as C8

n = 8
pool = POOL6
X = [ZERO] + list(pool)
good = []
for pattern in itertools.product([0, 1], repeat=len(C8.SLOTS)):
    G = C8.build(pattern, [pool[0]] * sum(pattern), X)
    if G.m != n:
        continue
    degs = {v: 0 for v in G.vertices()}
    for (u, v, x) in G.edges():
        degs[u] += 1; degs[v] += 1
    if all(v == 2 for v in degs.values()):
        good.append(pattern)

def cycle_type(G):
    adj = {}
    for (u, v, x) in G.edges():
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
    seen = set(); comps = []
    for v in adj:
        if v in seen: continue
        stack=[v]; comp=set()
        while stack:
            w=stack.pop()
            if w in comp: continue
            comp.add(w); stack.extend(adj[w])
        seen |= comp; comps.append(len(comp))
    return sorted(comps)

print("index  pattern                 npres  labeltuples(POOL6)  cycle_type")
tot = 0
for i, p in enumerate(good):
    G = C8.build(p, [pool[0]] * sum(p), X)
    npres = sum(p)
    lt = len(pool) ** npres
    tot += lt
    print(f"{i:5d}  {p}  {npres:5d}  {lt:18d}  {cycle_type(G)}")
print("total label tuples:", tot)
