"""Real-driver-distribution differential: graphs built exactly the way search.py
builds them (domains -> graph_from_labels -> build_rows), then generator rows
appended the way min_generators.extend does, with warm-started T0."""
import sys, random
sys.path.insert(0, "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src")
import fastcore, fastcore_rs, kakeya, search
from kakeya import ZERO

PY_F, PY_R = fastcore._force_py, fastcore._rank_py
RS_F, RS_R = fastcore_rs.force, fastcore_rs.rank
bad = []; nchk = 0; ninst = 0

def cmp_force(rows, n, T0):
    global nchk
    fastcore._INV.clear(); a = PY_F([r[:] for r in rows], n, set(T0))
    fastcore._INV.clear(); b = RS_F([r[:] for r in rows], n, set(T0))
    nchk += 1
    if (bool(a[0]), frozenset(a[1])) != (bool(b[0]), frozenset(b[1])):
        bad.append(("force", rows, n, sorted(T0), a, b))
    return a[1]

def cmp_rank(rows):
    global nchk
    fastcore._INV.clear(); a = PY_R([r[:] for r in rows])
    fastcore._INV.clear(); b = RS_R([r[:] for r in rows])
    nchk += 1
    if a != b: bad.append(("rank", rows, None, None, a, b))

rnd = random.Random(4242)
DS = [[2],[3],[4],[2,2],[2,3],[3,2],[2,2,2],[2,4],[2,2,2,2]]
POOLS = [search.POOL3, search.POOL4, search.POOL5, search.POOL6, search.POOL8]

for it in range(4000):
    d = rnd.choice(DS)
    pool = rnd.choice(POOLS)
    doms = search.domains(d)
    nlab = sum(len(x) for x in doms)
    labels = [rnd.choice([ZERO] + pool) for _ in range(nlab)]
    f = search.graph_from_labels(d, doms, labels)
    X = [ZERO] + pool
    G = kakeya.ConstructibleGraph(X, d, f)
    n = G.n
    R = [(rnd.choice(G.vertices()), rnd.choice(pool)) for _ in range(rnd.randrange(0,3))]
    rows, idx = kakeya.build_rows(G, R)
    ninst += 1
    cmp_rank(rows)
    t = rnd.randrange(0, min(3, n)+1)
    T = set(rnd.sample(range(n), t))
    # DFS-style warm-started chain, exactly like min_generators.extend
    cur = list(rows)
    for depth in range(rnd.randrange(1, 5)):
        T2 = cmp_force(cur, n, T)
        T = T2
        j = rnd.randrange(n); s = rnd.choice(pool)
        cur = cur + [search.gen_row(n, j, s)]
        cmp_rank(cur)

print("instances=%d checks=%d mismatches=%d" % (ninst, nchk, len(bad)))
for b in bad[:20]: print("  MISMATCH", b)
