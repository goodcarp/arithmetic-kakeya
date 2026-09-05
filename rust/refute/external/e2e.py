"""Independent end-to-end kernel check: drive search.min_generators over a
deterministic sweep of real graphs and hash every result. Run twice, once with
KAKEYA_PURE_PY=1 (pure Python kernel) and once without (Rust kernel)."""
import sys, os, hashlib, json, time
sys.path.insert(0,"/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src")
import fastcore, kakeya, search
from kakeya import ZERO
print("kernel:", fastcore.force.__module__, file=sys.stderr)
h = hashlib.sha256(); cnt = 0
t0 = time.time()
import itertools
for d in ([2,2],[2,3],[3,2],[2,2,2]):
    pool = search.POOL4
    doms = search.domains(d)
    nlab = sum(len(x) for x in doms)
    alphabet = [ZERO] + pool
    for labels in itertools.islice(itertools.product(alphabet, repeat=nlab), 0, 4000, 7):
        f = search.graph_from_labels(d, doms, list(labels))
        G = kakeya.ConstructibleGraph(alphabet, d, f)
        n = G.n
        rows, idx = kakeya.build_rows(G, [])
        for t in (0,1):
            for T0t in itertools.combinations(range(n), t):
                T0 = set(T0t)
                lr = search.local_requirement(G, idx, n, T0, pool)
                if lr is None: continue
                mand_total, mand = lr
                r = search.min_generators(rows, n, T0, pool, 2, mand)
                rk = fastcore.rank(rows)
                s = json.dumps({"d":d,"labels":[list(x) for x in labels],"T0":sorted(T0),
                                "gens": None if r is None else [[j,list(sl)] for j,sl in r],
                                "rank": rk}, sort_keys=True)
                h.update(s.encode()); cnt += 1
print(json.dumps({"kernel": fastcore.force.__module__, "results": cnt,
                  "digest": h.hexdigest(), "seconds": round(time.time()-t0,2)}))
