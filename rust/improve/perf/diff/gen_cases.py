"""Generate force() cases + PURE-PYTHON expected answers for the perf-lens
differential.  Distribution copied from rust/difftest.py (run_random /
run_ragged / run_drivers).  Writes a flat text corpus consumed by
improve/perf/kperf/crates/kakeya-core's `xdiff` binary.

  /usr/bin/python3 gen_cases.py <out> <n_random> <n_ragged> <n_driver> [seed]

Line format (one case per line, '|' separated):
  n | p | t0 csv | rows (rows '/' separated, entries ',' separated) | expect
expect = "T:<csv>" (ok) | "F:<csv>" (not forced) | "X:<ExcName>"
"""
import os, sys, random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ["KAKEYA_PURE_PY"] = "1"          # belt: never load the .so
import fastcore                              # noqa: E402
PY_FORCE = fastcore._force_py
assert fastcore.force is PY_FORCE, "pure-python force not selected"

P = (1 << 31) - 1
PS = [2147483647, 7, 97, 1000000007, 91]
SMALL = list(range(-5, 6))
BIG = [-(2**33), -(2**33)+1, -(2**33)-7, 2**33, 2**33+1, 2**33-3, 2**40, -(2**40)-1]
NEARP = [P-2, P-1, P, P+1, P+2, -P, -P+1, -P-1, 2*P, 2*P+1, P//2,
         90, 91, 92, 96, 97, 98, 6, 7, 8]

def entry(rng, mode):
    if mode == 0: return rng.choice(SMALL)
    if mode == 1: return rng.choice(SMALL + BIG)
    if mode == 2: return rng.choice(SMALL + NEARP)
    return rng.choice(SMALL + BIG + NEARP)

def emit(out, rows, n, T0, p):
    fastcore._INV.clear()
    try:
        ok, T = PY_FORCE(rows, n, T0, p)
        exp = ("T:" if ok else "F:") + ",".join(str(x) for x in sorted(T))
    except Exception as e:                    # noqa: BLE001
        exp = "X:" + type(e).__name__
    rs = "/".join("%d:%s" % (len(r), ",".join(str(x) for x in r)) for r in rows)
    out.write("%d|%d|%s|%s|%s\n" % (n, p, ",".join(str(x) for x in sorted(T0)), rs, exp))
    return 1

def gen_random(out, count, seed):
    rng = random.Random(seed); c = 0
    for it in range(count):
        n = rng.randint(1, 12); w = 2*n
        nrows = rng.randint(0, 2*n+3)
        mode = it % 4
        density = rng.choice([0.15, 0.3, 0.6, 1.0])
        rows = []
        for _ in range(nrows):
            r = [0]*w
            for k in range(w):
                if rng.random() < density: r[k] = entry(rng, mode)
            if rng.random() < 0.25:
                r = [0]*w
                u = rng.randrange(n); v = rng.randrange(n)
                x = rng.choice([(1,0),(0,1),(1,1),(1,2),(1,3),(2,1),(1,-2),(3,1)])
                r[2*u] += x[0]; r[2*u+1] += x[1]; r[2*v] -= x[0]; r[2*v+1] -= x[1]
            rows.append(r)
        p = rng.choice(PS)
        k = rng.random()
        if k < 0.35: T0 = set()
        elif k < 0.75: T0 = set(rng.sample(range(n), rng.randint(1, n)))
        elif k < 0.85: T0 = set(range(n))
        elif k < 0.93:
            T0 = list(rng.sample(range(n), rng.randint(1, n)))
            T0 = T0 + T0[:1]                  # duplicate member
        else:
            T0 = set(rng.sample(range(n), rng.randint(0, n)))
            T0.add(rng.choice([n, n+3, -1, -2, 99]))   # out-of-range member
        c += emit(out, rows, n, T0, p)
        fastcore._INV.clear()
        try: ok, T2 = PY_FORCE(rows, n, T0, p)
        except Exception: continue            # noqa: BLE001
        if not ok and rng.random() < 0.4:
            extra = [0]*w
            j = rng.randrange(n)
            s = rng.choice([(1,0),(0,1),(1,1),(1,2)])
            extra[2*j] = s[0]; extra[2*j+1] = s[1]
            c += emit(out, list(rows)+[extra], n, T2, p)
    return c

def gen_ragged(out, count, seed):
    rng = random.Random(seed); c = 0
    for _ in range(count):
        n = rng.randint(1, 6); w = 2*n
        rows = [[rng.choice(SMALL) for _ in range(rng.randint(0, w+3))]
                for _ in range(rng.randint(1, 5))]
        p = rng.choice(PS)
        T0 = set(rng.sample(range(n), rng.randint(0, n)))
        c += emit(out, rows, n, T0, p)
    return c

def gen_driver(out, count, seed):
    from kakeya import ConstructibleGraph, build_rows, ZERO
    from search import POOL8, domains, graph_from_labels, prod
    rng = random.Random(seed); c = 0
    dims = [[2],[3],[4],[2,2],[2,3],[3,2],[2,2,2],[2,4],[2,2,2,2]]
    alphabet = [ZERO] + list(POOL8)
    done = 0
    while done < count:
        d = rng.choice(dims); doms = domains(d)
        nslots = sum(len(x) for x in doms)
        labels = tuple(rng.choice(alphabet) for _ in range(nslots))
        n = prod(d)
        try:
            G = ConstructibleGraph([ZERO]+list(POOL8), d, graph_from_labels(d, doms, labels))
            R = [(rng.randrange(n), rng.choice(POOL8)) for _ in range(rng.randint(0, 3))]
            rows, idx = build_rows(G, R)
        except Exception:                     # noqa: BLE001
            continue
        rows = [list(r) for r in rows]
        T0 = set(rng.sample(range(n), rng.randint(0, min(n, 3))))
        c += emit(out, rows, n, T0, P)
        # warm-start chain, the real search.py pattern
        fastcore._INV.clear()
        try: ok, T2 = PY_FORCE(rows, n, T0, P)
        except Exception: ok = True           # noqa: BLE001
        if not ok:
            j = rng.randrange(n); s = rng.choice(list(POOL8))
            ex = [0]*(2*n); ex[2*j] = s[0]; ex[2*j+1] = s[1]
            c += emit(out, rows+[ex], n, T2, P)
        done += 1
    return c

if __name__ == "__main__":
    outp = sys.argv[1]
    nr, ng, nd = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 4242
    tot = 0
    with open(outp, "w") as out:
        tot += gen_random(out, nr, seed)
        tot += gen_ragged(out, ng, seed+1)
        tot += gen_driver(out, nd, seed+2)
    print("cases written:", tot)
