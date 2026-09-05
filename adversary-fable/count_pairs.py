"""Replicate each driver's outer loops WITHOUT calling min_generators, counting how
many (graph, T0) pairs survive the budget / rank / P4 prunes.  For cycles8 this is
exactly the `tested` figure a faithful port must print.  Read-only on K/src."""
import sys, os, itertools, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from fractions import Fraction
from kakeya import ConstructibleGraph, build_rows, ZERO
from search import local_requirement, POOL3, POOL4, POOL6
from fastcore import rank
import cycles8 as C8

out = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "count_pairs.out"), "a")
def log(s):
    print(s, flush=True); out.write(s + "\n"); out.flush()

def cycles8_count(pool, target=Fraction(67, 40)):
    X = [ZERO] + list(pool); n = 8
    good = []
    for pattern in itertools.product([0, 1], repeat=len(C8.SLOTS)):
        G = C8.build(pattern, [pool[0]] * sum(pattern), X)
        if G.m != n: continue
        degs = {v: 0 for v in G.vertices()}
        for (u, v, x) in G.edges():
            degs[u] += 1; degs[v] += 1
        if all(v == 2 for v in degs.values()): good.append(pattern)
    tested = 0; graphs = 0; per_pattern = []
    for pattern in good:
        tp = 0
        for labels in itertools.product(pool, repeat=sum(pattern)):
            graphs += 1
            G = C8.build(pattern, labels, X)
            base_rows, idx = build_rows(G, [])
            rk = rank(base_rows)
            for t in (0, 1, 2):
                den = n - t
                budget = int(target * den) - G.m
                if budget < 0 or den - rk > budget: continue
                for T0t in ([()] if t == 0 else itertools.combinations(range(n), t)):
                    T0 = set(T0t)
                    mt, mand = local_requirement(G, idx, n, T0, pool)
                    if mt > budget: continue
                    tested += 1; tp += 1
        per_pattern.append((pattern, tp))
    log(f"cycles8 pool={len(pool)}: patterns={len(good)} labelled_graphs={graphs} tested_pairs={tested} per_pattern={per_pattern}")

def stacked_count(pool, max_t=2, target=Fraction(7, 4)):
    X = [ZERO] + list(pool); d = [2, 2, 2]; n = 8
    f1 = {(1,): (1, 0)}; f2 = {(1, 1): (0, 1), (2, 1): (1, 2)}
    keys3 = [(a, b, 1) for a in (1, 2) for b in (1, 2)]
    alphabet = [ZERO] + list(pool)
    tuples = 0; pairs = 0
    for labs in itertools.product(alphabet, repeat=4):
        tuples += 1
        f3 = {k: v for k, v in zip(keys3, labs) if v != ZERO}
        G = ConstructibleGraph(X, d, [f1, f2, f3]); m = G.m
        base_rows, idx = build_rows(G, []); rk = rank(base_rows)
        for t in range(max_t + 1):
            den = n - t; budget = int(target * den) - m
            if budget < 0 or den - rk > budget: continue
            for T0t in ([()] if t == 0 else itertools.combinations(range(n), t)):
                T0 = set(T0t)
                mt, mand = local_requirement(G, idx, n, T0, pool)
                if mt > budget: continue
                pairs += 1
    log(f"stacked pool={len(pool)}: label_tuples={tuples} pairs_into_min_generators={pairs}")

def g2_tall_count(rows_, max_t=1, report_every=50000):
    POOL = POOL3; X = [ZERO] + POOL
    d = [2, rows_]; n = 2 * rows_
    keys2 = [(c, r) for c in (1, 2) for r in range(1, rows_)]
    alphabet = [ZERO] + POOL
    tuples = 0; pairs = 0; budget_hist = {}; t0 = time.time()
    for labs in itertools.product(alphabet, repeat=len(keys2)):
        tuples += 1
        f2 = {k: v for k, v in zip(keys2, labs) if v != ZERO}
        G = ConstructibleGraph(X, d, [{(1,): (1, 0)}, f2])
        base_rows, idx = build_rows(G, []); rk = rank(base_rows)
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
                key = (t, budget - mt)
                budget_hist[key] = budget_hist.get(key, 0) + 1
        if tuples % report_every == 0:
            log(f"  g2_tall 2x{rows_}: {tuples} tuples, {pairs} pairs so far, {time.time()-t0:.0f}s")
    log(f"g2_tall 2x{rows_}: label_tuples={tuples} pairs_into_min_generators={pairs} "
        f"free_budget_hist(t,budget-mandatory)={sorted(budget_hist.items())} {time.time()-t0:.0f}s")

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "cycles8": cycles8_count(POOL6)
    elif which == "stacked": stacked_count(POOL4); stacked_count(POOL6)
    elif which == "g2_4": g2_tall_count(4)
    elif which == "g2_5": g2_tall_count(5)
    elif which == "g2_6": g2_tall_count(6)
