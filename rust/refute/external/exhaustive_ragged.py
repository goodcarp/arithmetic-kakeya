"""Exhaustive sweep of the ragged-row / truncation logic in rank, and of force's
IndexError ordering, at several p."""
import sys, itertools
sys.path.insert(0, "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src")
import fastcore, fastcore_rs
PY_R, RS_R = fastcore._rank_py, fastcore_rs.rank
PY_F, RS_F = fastcore._force_py, fastcore_rs.force

def call(fn, *a):
    try: return ("ok", fn(*a))
    except BaseException as e: return ("raise", type(e).__name__)

bad = []; n = 0
vals = (0,1,2)
# rank: every multiset of up to 3 rows of length 0..4 over {0,1,2}, p in {2,3,5,P}
pool = []
for L in range(0,5):
    pool += [list(t) for t in itertools.product(vals, repeat=L)]
print("row pool size", len(pool))
for p in (2,3,5,2147483647):
    for m in (1,2,3):
        for combo in itertools.combinations_with_replacement(range(len(pool)), m):
            for perm in set(itertools.permutations(combo)):
                rows = [pool[i][:] for i in perm]
                fastcore._INV.clear(); a = call(PY_R, [r[:] for r in rows], p)
                fastcore._INV.clear(); b = call(RS_R, [r[:] for r in rows], p)
                n += 1
                if a != b: bad.append((rows, p, a, b))
        print("  p=%d m=%d cumulative checks=%d bad=%d" % (p, m, n, len(bad)))
print("rank ragged exhaustive: checks=%d mismatches=%d" % (n, len(bad)))
for b in bad[:20]: print("  ", b)

# force: ragged rows, n=1..2, T0 subsets
nf = 0; badf = []
for p in (2,3,2147483647):
    for nn in (1,2):
        subs = [set()] + [{j} for j in range(nn)]
        for m in (1,2):
            for combo in itertools.product(range(len(pool)), repeat=m):
                rows = [pool[i][:] for i in combo]
                for T0 in subs:
                    fastcore._INV.clear(); a = call(PY_F, [r[:] for r in rows], nn, set(T0), p)
                    fastcore._INV.clear(); b = call(RS_F, [r[:] for r in rows], nn, set(T0), p)
                    if a[0]=="ok": a = ("ok", bool(a[1][0]), frozenset(a[1][1]))
                    if b[0]=="ok": b = ("ok", bool(b[1][0]), frozenset(b[1][1]))
                    nf += 1
                    if a != b: badf.append((rows, nn, sorted(T0), p, a, b))
print("force ragged exhaustive: checks=%d mismatches=%d" % (nf, len(badf)))
for b in badf[:20]: print("  ", b)
