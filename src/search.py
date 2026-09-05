"""Search for low-scoring X-constructible objects.

Symmetry: the problem is invariant under projective transformations of the
slope line fixing the target slope -1 (Tao 2025, sec 1.1); that group is
2-transitive on the other slopes, so two of the labels actually used may
always be normalised to (1,0) (slope 0) and (0,1) (slope oo).  X itself is
free -- it never appears in the score -- so the only real choice is *which*
slopes get used as labels.

Pruning facts used (see KAKEYA-WORKBENCH.md for proofs):
  P1  a generator at a vertex already in T is useless  -> only branch on
      currently-unforced vertices;
  P2  at most two generators per vertex, never two parallel  (two independent
      labels at v force v outright);
  P3  rank bound: every forcing step consumes a fresh dimension of the module,
      so  m_rank + r >= n - t,  i.e.  r >= (n-t) - rank(edge rows).
  P4  LOCAL NECESSITY (the strong one).  If f in M has f(v) = tau then, reading
      off the v-coordinate of f as a combination of the generators, f(v) lies
      in the span of {labels of edges incident to v} u {labels of generators
      at v}.  No single label is parallel to tau = (1,-1) (that is exactly the
      condition a+b != 0 on X), so that span must have rank 2.  Hence every
      v outside T_0 must see at least two non-parallel directions among its
      incident edge labels and its own generators.  This
        (a) lower-bounds r by  sum_v max(0, 2 - indep(v))  over v not in T_0,
        (b) *pins the positions* of the mandatory generators, leaving only
            their directions and any optional extras to be searched.
"""
import sys, os, itertools, random, time
from fractions import Fraction
from math import prod
sys.path.insert(0, os.path.dirname(__file__))
from kakeya import ConstructibleGraph, build_rows, ZERO
from fastcore import force, rank

POOL3 = [(1, 0), (0, 1), (1, 1)]      # the sums-differences alphabet (Goal 2)
POOL4 = [(1, 0), (0, 1), (1, 1), (1, 2)]
POOL5 = POOL4 + [(1, 3)]
POOL6 = POOL5 + [(2, 1)]
POOL8 = POOL6 + [(1, -2), (3, 1)]


def domains(d):
    out = []
    for i in range(1, len(d) + 1):
        pref = list(itertools.product(*[range(1, d[j] + 1) for j in range(i - 1)]))
        out.append([tuple(list(p) + [last]) for p in pref for last in range(1, d[i - 1])])
    return out


def mult(d, i):
    return prod(d[i:]) if i < len(d) else 1


def graph_from_labels(d, doms, labels):
    f, pos = [], 0
    for i in range(1, len(d) + 1):
        fi = {}
        for key in doms[i - 1]:
            if labels[pos] != ZERO:
                fi[key] = labels[pos]
            pos += 1
        f.append(fi)
    return f


def m_of_labels(d, doms, labels):
    tot, pos = 0, 0
    for i in range(1, len(d) + 1):
        mu = mult(d, i)
        for _ in doms[i - 1]:
            if labels[pos] != ZERO:
                tot += mu
            pos += 1
    return tot


def gen_row(n, j, s):
    row = [0] * (2 * n)
    row[2 * j] = s[0]
    row[2 * j + 1] = s[1]
    return row


def indep_dirs(labels):
    """number of pairwise non-parallel directions (capped at 2)."""
    seen = []
    for s in labels:
        if s == ZERO:
            continue
        if not seen:
            seen.append(s); continue
        if all(a[0]*s[1] - a[1]*s[0] != 0 for a in seen):
            seen.append(s)
            if len(seen) >= 2:
                return 2, seen
    return len(seen), seen


def local_requirement(G, idx, n, T0, pool):
    """(mandatory_total, per-vertex list of (vertex, existing_dirs, need))
    using P4.  Returns None if some vertex cannot be repaired at all."""
    inc = {j: [] for j in range(n)}
    for (u, v, x) in G.edges():
        inc[idx[u]].append(x)
        inc[idx[v]].append(x)
    total = 0
    need = []
    for j in range(n):
        if j in T0:
            continue
        k, seen = indep_dirs(inc[j])
        if k < 2:
            total += 2 - k
            need.append((j, seen, 2 - k))
    return total, need


def _dir_choices(existing, pool, k):
    """Ways to add k generator directions at a vertex so its total direction set
    has rank 2 (P4).

    P5 (canonical pair).  Two non-parallel generators at v contribute exactly
    delta_v (x) Q^2 to the module -- the span does not depend on *which*
    independent pair is chosen.  So when a vertex needs two generators there is
    only one case to try, not C(|pool|,2).  This is the difference between
    |pool|^(2k) and 1 on sparse graphs.
    """
    def par(a, b): return a[0]*b[1] - a[1]*b[0] == 0
    if k == 1:
        return [(s,) for s in pool if all(not par(s, e) for e in existing)]
    if k >= 2:
        # P6: a vertex needing two generators is strictly better off inside T
        # (see tests/test_p6_swap.py).  Such a graph/T pair is discarded here;
        # it reappears, improved, in the enumeration with that vertex in T.
        return []
    return [()]


def min_generators(base_rows, n, T0, pool, budget, mand=None):
    """Fewest generators making the forcing succeed, <= budget; None if none.

    Mandatory positions come from P4; only their directions and any optional
    extras are searched."""
    if mand is None:
        mand = []
    mand_total = sum(k for (_, _, k) in mand)
    if mand_total > budget:
        return None
    slots = [(_j, _dir_choices(_ex, pool, _k)) for (_j, _ex, _k) in mand]
    if any(len(c) == 0 for _, c in slots):
        return None
    cand = [(j, s) for j in range(n) if j not in T0 for s in pool]
    nc = len(cand)
    best = [None]

    def extend(rows, gens, start, T, budget_left):
        ok, T2 = force(rows, n, T)
        if ok:
            if best[0] is None or len(gens) < len(best[0]):
                best[0] = list(gens)
            return
        if budget_left == 0:
            return
        if best[0] is not None and len(gens) + 1 >= len(best[0]):
            return
        for ci in range(start, nc):
            j, sl = cand[ci]
            if j in T2:
                continue
            if any(g[0] == j for g in gens):
                continue          # P6: at most one generator per vertex
            extend(rows + [gen_row(n, j, sl)], gens + [(j, sl)], ci + 1, T2,
                   budget_left - 1)

    import itertools as _it
    for combo in _it.product(*[c for _, c in slots]):
        gens = []
        rows = list(base_rows)
        for (j, _), dirs in zip(slots, combo):
            for sl in dirs:
                gens.append((j, sl))
                rows.append(gen_row(n, j, sl))
        if best[0] is not None and len(gens) >= len(best[0]):
            continue
        extend(rows, gens, 0, set(T0), budget - len(gens))
    return best[0]


def scan_dims(d, pool, target, max_t=0, limit=None, seed=0, tlimit=None,
              verbose=True):
    """Enumerate label assignments for these dims (or `limit` random ones)."""
    doms = domains(d)
    nslots = sum(len(x) for x in doms)
    n = prod(d)
    alphabet = [ZERO] + list(pool)
    X = [ZERO] + list(pool)
    hits, best = [], None
    t0 = time.time()
    if limit is None:
        it = itertools.product(alphabet, repeat=nslots)
        total = len(alphabet) ** nslots
    else:
        rng = random.Random(seed)
        it = (tuple(rng.choice(alphabet) for _ in range(nslots)) for _ in range(limit))
        total = limit
    count = 0
    for labels in it:
        count += 1
        if tlimit and time.time() - t0 > tlimit:
            break
        m = m_of_labels(d, doms, labels)
        if m > int(target * n):
            continue
        f = graph_from_labels(d, doms, labels)
        G = ConstructibleGraph(X, d, f)
        base_rows, idx = build_rows(G, [])
        rk = rank(base_rows)
        for t in range(max_t + 1):
            den = n - t
            budget = int(target * den) - m
            if budget < 0 or den - rk > budget:
                continue
            for T0t in ([()] if t == 0 else itertools.combinations(range(n), t)):
                T0 = set(T0t)
                mand_total, mand = local_requirement(G, idx, n, T0, pool)
                if mand_total > budget:
                    continue
                gens = min_generators(base_rows, n, T0, pool, budget, mand)
                if gens is None:
                    continue
                sc = Fraction(m + len(gens), den)
                if best is None or sc < best:
                    best = sc
                if sc <= target:
                    hits.append({"d": list(d), "labels": labels, "m": m,
                                 "gens": gens, "T0": sorted(T0), "score": sc, "n": n})
                    if verbose:
                        print(f"   HIT {sc} (={float(sc):.4f})  d={d} m={m} "
                              f"r={len(gens)} t={t}", flush=True)
    return hits, best, count, total, time.time() - t0
