"""Exhaustive check of the 8-cycle sub-family of cycles8 (POOL6), using a proved
necessary condition to prune generator placements.

Lemma C (component condition; proof in PREDICTIONS.md).  For any slope c let G_{-c}
be the graph of edges whose label is not parallel to c.  If the object forces, then
every connected component of G_{-c} contains a vertex of T0 or a generator whose
label is not parallel to c.  Hence  #comp(G_{-c}) <= t + r_{-c}  for every c.

The 8-cycle has labels x,z1,x,y,x,z2,x,y (x = f1, y = f2 bundle, z1,z2 = f3 slots).
Generators: one per vertex (P6), slope from POOL6.  Targets from cycles8.py:
t=0 -> r<=5, t=1 -> r<=3, t=2 -> r<=2  (den 8/7/6, budget floor(67/40*den)-8).
For each (labels, t) we enumerate generator sets satisfying Lemma C for every slope in
POOL6 plus P4, and call fastcore.force.  Any success is a HIT (score <= 67/40)."""
import sys, os, itertools, json, time
from multiprocessing import Pool
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from search import POOL6
from fastcore import force

N = 8
# cycle vertices 0..7, edge i joins i and i+1 mod 8; label pattern x,z1,x,y,x,z2,x,y
def labels_of(x, y, z1, z2):
    return [x, z1, x, y, x, z2, x, y]

def par(a, b): return a[0]*b[1] - a[1]*b[0] == 0

def components(labs, c):
    """components of the cycle with edges parallel to c removed"""
    parent = list(range(N))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for i in range(N):
        if not par(labs[i], c):
            a, b = find(i), find((i + 1) % N)
            if a != b: parent[a] = b
    comps = {}
    for v in range(N):
        comps.setdefault(find(v), []).append(v)
    return list(comps.values())

def rows_of(labs, gens):
    rows = []
    for i in range(N):
        x = labs[i]
        row = [0] * (2 * N)
        j = (i + 1) % N
        row[2*i] += x[0]; row[2*i+1] += x[1]
        row[2*j] -= x[0]; row[2*j+1] -= x[1]
        rows.append(row)
    for (v, s) in gens:
        row = [0] * (2 * N)
        row[2*v] = s[0]; row[2*v+1] = s[1]
        rows.append(row)
    return rows

def feasible(labs, T0, gens, slopes):
    """Lemma C for every slope in `slopes`, and P4 at every vertex outside T0."""
    for c in slopes:
        for comp in components(labs, c):
            if any(v in T0 for v in comp): continue
            if any(v in comp and not par(s, c) for (v, s) in gens): continue
            return False
    gat = {v: s for (v, s) in gens}
    for v in range(N):
        if v in T0: continue
        dirs = [labs[(v - 1) % N], labs[v]] + ([gat[v]] if v in gat else [])
        ok = any(not par(dirs[i], dirs[j]) for i in range(len(dirs)) for j in range(i+1, len(dirs)))
        if not ok: return False
    return True

def check_graph(args):
    x, y, z1, z2, rmax_by_t = args
    labs = labels_of(x, y, z1, z2)
    slopes = list(POOL6) + [(2, 3)]          # (2,3) stands for "a slope used by nothing"
    hits = []; calls = 0; enumerated = 0
    for t, rmax in rmax_by_t.items():
        for T0t in itertools.combinations(range(N), t):
            T0 = set(T0t)
            free = [v for v in range(N) if v not in T0]
            for r in range(0, rmax + 1):
                for vs in itertools.combinations(free, r):
                    for ss in itertools.product(POOL6, repeat=r):
                        gens = list(zip(vs, ss))
                        enumerated += 1
                        if not feasible(labs, T0, gens, slopes): continue
                        calls += 1
                        ok, T = force(rows_of(labs, gens), N, T0)
                        if ok:
                            hits.append({"labels": labs, "T0": sorted(T0), "gens": gens, "r": r, "t": t,
                                         "score": f"{8 + r}/{8 - t}"})
    return {"x": x, "y": y, "z1": z1, "z2": z2, "enumerated": enumerated, "force_calls": calls, "hits": hits}

if __name__ == "__main__":
    phase = sys.argv[1]      # "cheap" = t=2 r<=2, t=1 r<=3, t=0 r<=4 ; "r5" = t=0 r=5 only
    rmax = {2: 2, 1: 3, 0: 4} if phase == "cheap" else {0: 5}
    jobs = [(x, y, z1, z2, rmax) for x in POOL6 for y in POOL6 for z1 in POOL6 for z2 in POOL6]
    outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"cycle8_{phase}.out")
    t0 = time.time(); done = 0; total_calls = 0; total_hits = 0
    with Pool(10) as pool, open(outp, "a") as f:
        for res in pool.imap_unordered(check_graph, jobs, chunksize=4):
            done += 1; total_calls += res["force_calls"]; total_hits += len(res["hits"])
            if res["hits"]:
                f.write("HIT " + json.dumps(res) + "\n"); f.flush()
            if done % 100 == 0 or done == len(jobs):
                f.write(f"progress {done}/{len(jobs)} force_calls={total_calls} hits={total_hits} {time.time()-t0:.0f}s\n"); f.flush()
        f.write(f"DONE phase={phase} graphs={done} force_calls={total_calls} hits={total_hits} {time.time()-t0:.0f}s\n")
