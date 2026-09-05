"""Timing: fastcore_rs (Rust) vs pure-Python fastcore, fixed seed.

Instances come from the real driver distribution -- ConstructibleGraph +
build_rows, with a few generator rows appended the way search.min_generators
does -- so the numbers reflect the actual hot path.

Run:  /usr/bin/python3 rust/bench.py
"""
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import fastcore                      # noqa: E402
import fastcore_rs                   # noqa: E402
from kakeya import ConstructibleGraph, build_rows, ZERO   # noqa: E402
from search import POOL8, domains, graph_from_labels, gen_row  # noqa: E402

PY_FORCE = getattr(fastcore, "_force_py", fastcore.force)
PY_RANK = getattr(fastcore, "_rank_py", fastcore.rank)
RS_FORCE = fastcore_rs.force
RS_RANK = fastcore_rs.rank

SEED = 20260904
DIMS = {6: [2, 3], 8: [2, 4], 10: [2, 5]}


def make_instances(n, count, seed):
    """(rows, T0) pairs shaped like search.min_generators' DFS nodes."""
    rng = random.Random(seed)
    d = DIMS[n]
    doms = domains(d)
    nslots = sum(len(x) for x in doms)
    alphabet = [ZERO] + list(POOL8)
    out = []
    while len(out) < count:
        labels = tuple(rng.choice(alphabet) for _ in range(nslots))
        try:
            G = ConstructibleGraph(alphabet, d, graph_from_labels(d, doms, labels))
            rows, idx = build_rows(G, [])
        except Exception:                        # noqa: BLE001
            continue
        rows = [list(r) for r in rows]
        for _ in range(rng.randint(0, 4)):       # generator rows the DFS adds
            rows.append(gen_row(n, rng.randrange(n), rng.choice(POOL8)))
        T0 = set(rng.sample(range(n), rng.randint(0, 2)))
        out.append((rows, T0))
    return out


def time_force(fn, insts, n, reps):
    t = time.perf_counter()
    for _ in range(reps):
        for rows, T0 in insts:
            fn(rows, n, T0)
    return time.perf_counter() - t


def bench_force(n, count=200, reps=5):
    insts = make_instances(n, count, SEED + n)
    calls = count * reps
    # warm-up
    for rows, T0 in insts[:20]:
        PY_FORCE(rows, n, T0)
        RS_FORCE(rows, n, T0)
    # best of 3 trials each: wall-clock on a shared machine is noisy
    tp = min(time_force(PY_FORCE, insts, n, reps) for _ in range(3))
    tr = min(time_force(RS_FORCE, insts, n, reps) for _ in range(3))
    ok_frac = sum(1 for rows, T0 in insts if RS_FORCE(rows, n, T0)[0]) / len(insts)
    return tp / calls * 1e6, tr / calls * 1e6, ok_frac


def bench_rank(count=400, reps=20):
    rng = random.Random(SEED)
    mats = []
    for _ in range(count):
        n = rng.choice([6, 8, 10])
        d = DIMS[n]
        doms = domains(d)
        nslots = sum(len(x) for x in doms)
        alphabet = [ZERO] + list(POOL8)
        labels = tuple(rng.choice(alphabet) for _ in range(nslots))
        G = ConstructibleGraph(alphabet, d, graph_from_labels(d, doms, labels))
        rows, _ = build_rows(G, [])
        mats.append([list(r) for r in rows])
    calls = count * reps
    for m in mats[:20]:
        PY_RANK(m)
        RS_RANK(m)
    def run(fn):
        t = time.perf_counter()
        for _ in range(reps):
            for m in mats:
                fn(m)
        return time.perf_counter() - t

    tp = min(run(PY_RANK) for _ in range(3))
    tr = min(run(RS_RANK) for _ in range(3))
    return tp / calls * 1e6, tr / calls * 1e6


def main():
    print("best of 3 trials per row")
    print("%-10s %14s %14s %10s   %s" %
          ("workload", "python us/call", "rust us/call", "speedup", "notes"))
    print("-" * 78)
    results = {}
    for n in (6, 8, 10):
        tp, tr, okf = bench_force(n)
        results["force_n%d" % n] = (tp, tr, tp / tr)
        print("%-10s %14.2f %14.2f %9.1fx   %.0f%% of instances force"
              % ("force n=%d" % n, tp, tr, tp / tr, okf * 100))
    tp, tr = bench_rank()
    results["rank"] = (tp, tr, tp / tr)
    print("%-10s %14.2f %14.2f %9.1fx   %s" % ("rank", tp, tr, tp / tr,
                                               "7-31 row build_rows matrices"))
    print()
    print("BENCH_JSON " + repr({k: {"py_us": round(v[0], 3),
                                    "rs_us": round(v[1], 3),
                                    "speedup": round(v[2], 2)}
                                for k, v in results.items()}))


if __name__ == "__main__":
    main()
