"""cycles8 residual: the driver loops t in (0,1,2) only.  At t=3 the budget is
   int(67/40 * 5) - 8 = 8 - 8 = 0, so r = 0 and score = 8/5 = 1.6 <= 67/40.
   t=4 gives budget int(6.7)-8 < 0, so t=3 is the ONLY uncovered phase.
   This enumerates it exhaustively: every deg-2 presence pattern, every POOL6
   label tuple, every 3-subset T0, r = 0, and asks force() directly.
   usage: t3_check.py [patterns]   patterns = 8cycle | 4+4 | all
"""
import sys, os, itertools, time, json
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "..", "..", "..", "src")
sys.path.insert(0, os.path.abspath(SRC))
from kakeya import build_rows, ZERO
from search import POOL6, indep_dirs
from fastcore import force
import cycles8 as C8

which = sys.argv[1] if len(sys.argv) > 1 else "8cycle"
pool = POOL6
X = [ZERO] + list(pool)
n = 8
t = 3

# step 1: the deg-2, m=n presence patterns, in the driver's own product order
good = []
for pattern in itertools.product([0, 1], repeat=len(C8.SLOTS)):
    G = C8.build(pattern, [pool[0]] * sum(pattern), X)
    if G.m != n:
        continue
    degs = {v: 0 for v in G.vertices()}
    for (u, v, x) in G.edges():
        degs[u] += 1
        degs[v] += 1
    if all(v == 2 for v in degs.values()):
        good.append(pattern)
print("patterns:", good, flush=True)

def cycles(G):
    """number of connected components of the edge graph"""
    par = list(range(n))
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    idx = {v: i for i, v in enumerate(sorted(G.vertices()))}
    for (u, v, x) in G.edges():
        a, b = find(idx[u]), find(idx[v])
        if a != b:
            par[a] = b
    return len({find(i) for i in range(n)})

sel = []
for i, p in enumerate(good):
    G = C8.build(p, [pool[0]] * sum(p), X)
    c = cycles(G)
    kind = "8cycle" if c == 1 else "4+4"
    want = (which == "all" or which == kind or
            (which.startswith("idx:") and str(i) in which[4:].split(",")))
    if want:
        sel.append((i, p, kind))
print("selected:", [(i, k) for i, p, k in sel], flush=True)

T0S = list(itertools.combinations(range(n), t))
t0 = time.time()
graphs = 0; pairs = 0; hits = []; skipped_p4 = 0
for (pi, pattern, kind) in sel:
    npres = sum(pattern)
    for labels in itertools.product(pool, repeat=npres):
        G = C8.build(pattern, labels, X)
        graphs += 1
        base_rows, idx = build_rows(G, [])
        # P4 with r = 0: every vertex outside T0 must see two non-parallel
        # incident edge labels.  Collect the vertices that fail.
        inc = {v: [] for v in range(n)}
        for (u, v, x) in G.edges():
            inc[idx[u]].append(x)
            inc[idx[v]].append(x)
        bad = frozenset(v for v in range(n) if indep_dirs(inc[v])[0] < 2)
        if len(bad) > t:
            skipped_p4 += 1
            continue
        for T0t in T0S:
            T0 = set(T0t)
            if not bad <= T0:
                continue
            pairs += 1
            ok, _ = force(base_rows, n, T0)
            if ok:
                hits.append((pi, kind, labels, sorted(T0)))
                print("HIT", json.dumps([pi, kind, labels, sorted(T0)], default=str),
                      flush=True)
el = time.time() - t0
print("RESULT", json.dumps({"tag": "cycles8_t3_r0", "pool": 6, "which": which,
      "t": 3, "r": 0, "score_if_hit": "8/5", "graphs": graphs,
      "skipped_by_P4": skipped_p4, "pairs": pairs, "hits": len(hits),
      "seconds": round(el, 1)}), flush=True)
