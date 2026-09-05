"""Time the Python driver's per-graph work (including min_generators) on random
label tuples of the g2_tall 2xr family, with a per-graph alarm.  Gives the cost
distribution needed to scale a Rust runtime estimate."""
import sys, os, itertools, random, time, signal, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import min_generators, local_requirement, POOL3
from fastcore import rank, force

class TO(Exception): pass
def _alarm(*a): raise TO()
signal.signal(signal.SIGALRM, _alarm)

out = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "time_sample.out"), "a")
def log(s):
    print(s, flush=True); out.write(s + "\n"); out.flush()

def one(rows_, labs, max_t=1, cap_s=300):
    POOL = POOL3; X = [ZERO] + POOL
    d = [2, rows_]; n = 2 * rows_
    keys2 = [(c, r) for c in (1, 2) for r in range(1, rows_)]
    f2 = {k: v for k, v in zip(keys2, labs) if v != ZERO}
    G = ConstructibleGraph(X, d, [{(1,): (1, 0)}, f2])
    base_rows, idx = build_rows(G, []); rk = rank(base_rows)
    calls = [0]
    import fastcore, search
    orig = search.force
    def counting_force(*a, **k):
        calls[0] += 1; return orig(*a, **k)
    search.force = counting_force
    t0 = time.time(); status = "done"; found = None; pairs = 0
    signal.alarm(cap_s)
    try:
        for t in range(max_t + 1):
            q = n - t
            cap = int(Fraction(11, 6) * q)
            if Fraction(cap, q) >= Fraction(11, 6): cap -= 1
            budget = cap - G.m
            if budget < 0 or q - rk > budget: continue
            for T0t in ([()] if t == 0 else itertools.combinations(range(n), t)):
                T0 = set(T0t)
                mt, mand = local_requirement(G, idx, n, T0, POOL)
                if mt > budget: continue
                pairs += 1
                gens = min_generators(base_rows, n, T0, POOL, budget, mand)
                if gens is not None:
                    found = (str(Fraction(G.m + len(gens), q)), len(gens), t)
    except TO:
        status = "TIMEOUT"
    finally:
        signal.alarm(0); search.force = orig
    return {"rows": rows_, "labs": labs, "m": G.m, "rk": rk, "pairs": pairs,
            "force_calls": calls[0], "seconds": round(time.time() - t0, 2),
            "status": status, "found": found}

if __name__ == "__main__":
    rows_ = int(sys.argv[1]); k = int(sys.argv[2]); seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    cap_s = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    rng = random.Random(seed)
    alphabet = [ZERO] + POOL3
    nk = 2 * (rows_ - 1)
    if seed < 0:   # prefix mode: the first k tuples in itertools.product order (what the logged runs walked)
        it = itertools.islice(itertools.product(alphabet, repeat=nk), k)
        for i, labs in enumerate(it):
            r = one(rows_, labs, cap_s=cap_s); r["prefix_index"] = i
            log(json.dumps(r))
    else:
        for i in range(k):
            labs = tuple(rng.choice(alphabet) for _ in range(nk))
            r = one(rows_, labs, cap_s=cap_s)
            log(json.dumps(r))
