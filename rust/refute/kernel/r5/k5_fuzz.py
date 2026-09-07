"""r5/kernel 20k differential fuzz, fresh seed, biased at the structures the
earlier lenses under-sampled:
  * composite moduli whose pivots have inverse 0 mod p (pow(a,p-2,p)==0)
  * multi-round force instances where several j qualify per round, so the
    ascending-j greedy choice is load-bearing for the FINAL T, not just for ok
  * T0 drawn out of range (negative, >= n) so the len(T)>=n short-circuit fires
  * rows that go zero only on the UNFORCED coords in a later round
Reference: fastcore._force_py/_rank_py with fastcore._INV.clear() per call.
usage: k5_fuzz.py [n] [seed]
"""
import os, random, sys
SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
sys.path.insert(0, SRC)
os.environ["KAKEYA_PURE_PY"] = "1"
import fastcore, fastcore_rs
PYF, PYR, INV = fastcore._force_py, fastcore._rank_py, fastcore._INV
RSF, RSR = fastcore_rs.force, fastcore_rs.rank

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 51977
rng = random.Random(SEED)

# moduli where some residue has a zero Fermat "inverse": every composite here
# has a pivot value a with pow(a, p-2, p) == 0.
COMPOSITE = [4, 6, 8, 9, 10, 12, 16, 18, 25, 27, 32, 36, 49, 64, 100, 121,
             128, 256, 1024, 65536, 4294967294, 4294967295]
PRIME = [2, 3, 5, 7, 11, 13, 97, 257, 65537, 2147483647, 4294967291]
MODULI = COMPOSITE + PRIME + [1]

def entry(p):
    r = rng.random()
    if r < 0.30:                       # multiples of small factors of p
        k = rng.choice([1, 2, 3, 4, 6, 8, 9, 16])
        return k * rng.randint(-4, 4)
    if r < 0.55:
        return rng.choice([0, 1, -1, p - 1, p, p + 1, -p, 1 - p]) if p < 10**6 else rng.randint(-5, 5)
    if r < 0.75:
        return rng.choice([0, 0, 1, -1, 2, -2, 3, -3])
    return rng.randint(-(1 << 40), 1 << 40)

def gen_T0(n):
    k = rng.randint(0, min(n + 2, 5))
    out = []
    for _ in range(k):
        r = rng.random()
        if r < 0.55:  out.append(rng.randrange(0, max(n, 1)))
        elif r < 0.75: out.append(-rng.randint(1, 5))
        elif r < 0.9:  out.append(n + rng.randint(0, 4))
        else:          out.append(rng.choice([10**6, 2**40, -(2**40)]))
    return out

ndiv = 0; nchk = 0; bad = []
for it in range(N):
    p = rng.choice(MODULI)
    n = rng.randint(0, 5)
    w = 2 * n + rng.choice([0, 0, 0, 2, 4])
    m = rng.randint(0, 6)
    rows = [[entry(p) for _ in range(w)] for _ in range(m)]
    T0 = gen_T0(n)
    kw = {} if rng.random() < 0.3 else {"p": p}
    # force
    nchk += 1
    INV.clear()
    INV.clear()
    try:
        v = PYF(rows, n, T0, **kw); a = ("f", bool(v[0]), tuple(sorted(int(x) for x in v[1])))
    except BaseException as e: a = ("exc", type(e).__name__)
    try:
        v = RSF(rows, n, T0, **kw); b = ("f", bool(v[0]), tuple(sorted(int(x) for x in v[1])))
    except BaseException as e: b = ("exc", type(e).__name__)
    if a != b:
        ndiv += 1; bad.append(("force", rows, n, T0, kw, a, b))
    # rank
    nchk += 1
    INV.clear()
    try: c = ("r", int(PYR(rows, **kw)))
    except BaseException as e: c = ("exc", type(e).__name__)
    try: d = ("r", int(RSR(rows, **kw)))
    except BaseException as e: d = ("exc", type(e).__name__)
    if c != d:
        ndiv += 1; bad.append(("rank", rows, None, None, kw, c, d))
    if len(bad) > 8: break

print("k5_fuzz seed=%d instances=%d checks=%d divergences=%d" % (SEED, it + 1, nchk, ndiv))
for r in bad[:8]:
    print("  DIVERGE", r[0], "kw=%r n=%r T0=%r" % (r[4], r[2], r[3]))
    print("     rows=%r" % (r[1],))
    print("     py=%r rs=%r" % (r[5], r[6]))
sys.exit(1 if bad else 0)
