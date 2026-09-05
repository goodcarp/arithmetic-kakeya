"""Independent randomised differential: real driver distribution + adversarial shapes.
Written without reference to rust/difftest.py."""
import sys, random, itertools
sys.path.insert(0, "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src")
import fastcore, fastcore_rs
import kakeya, search

PY_F, PY_R = fastcore._force_py, fastcore._rank_py
RS_F, RS_R = fastcore_rs.force, fastcore_rs.rank

def call(fn, *a):
    try:
        return ("ok", fn(*a))
    except BaseException as e:
        return ("raise", type(e).__name__)

def norm_force(r):
    if r[0] != "ok": return r
    ok, T = r[1]; return ("ok", bool(ok), frozenset(T))
def norm_rank(r):
    return r

bad = []
nchk = 0

def cmp_force(rows, n, T0, p=None):
    global nchk
    a = (rows, n, T0) if p is None else (rows, n, T0, p)
    fastcore._INV.clear(); x = norm_force(call(PY_F, *[list(map(list,rows)), n, set(T0)] + ([] if p is None else [p])))
    fastcore._INV.clear(); y = norm_force(call(RS_F, *[list(map(list,rows)), n, set(T0)] + ([] if p is None else [p])))
    nchk += 1
    if x != y: bad.append(("force", rows, n, sorted(T0), p, x, y))

def cmp_rank(rows, p=None):
    global nchk
    fastcore._INV.clear(); x = norm_rank(call(PY_R, *[list(map(list,rows))] + ([] if p is None else [p])))
    fastcore._INV.clear(); y = norm_rank(call(RS_R, *[list(map(list,rows))] + ([] if p is None else [p])))
    nchk += 1
    if x != y: bad.append(("rank", rows, None, None, p, x, y))

rnd = random.Random(20260905)

# ---- A. real driver distribution -----------------------------------------
POOL8 = search.POOL8
DS = [[2],[3],[4],[2,2],[2,3],[3,2],[2,2,2],[2,4],[2,2,2,2]]
nA = 0
for it in range(6000):
    d = rnd.choice(DS)
    n = 1
    for k in d: n *= k
    X = [kakeya.ZERO] + POOL8
    f = {}
    try:
        G = kakeya.ConstructibleGraph(X, d, f)
    except Exception:
        continue
    nv = G.n
    R = [(rnd.randrange(nv), rnd.choice(POOL8)) for _ in range(rnd.randrange(0, 4))]
    try:
        rows, idx = kakeya.build_rows(G, R)
    except Exception:
        continue
    rows = [list(r) for r in rows]
    t = rnd.randrange(0, min(3, nv) + 1)
    T0 = set(rnd.sample(range(nv), t)) if t else set()
    cmp_force(rows, nv, T0)
    cmp_rank(rows)
    nA += 1
print("A driver-distribution instances: %d" % nA)

# ---- B. raw random rows, entries -3..3, multi-round force ----------------
for it in range(20000):
    n = rnd.randrange(1, 9)
    m = rnd.randrange(0, 12)
    rows = [[rnd.randrange(-3, 4) for _ in range(2*n)] for _ in range(m)]
    T0 = set(rnd.sample(range(n), rnd.randrange(0, n+1)))
    cmp_force(rows, n, T0)
    cmp_rank(rows)

# ---- C. sparse delta-like rows (forces long chains) ----------------------
for it in range(20000):
    n = rnd.randrange(2, 10)
    m = rnd.randrange(1, n+3)
    rows = []
    for _ in range(m):
        r = [0]*(2*n)
        u = rnd.randrange(n); v = rnd.randrange(n)
        x = rnd.choice(POOL8)
        r[2*u] += x[0]; r[2*u+1] += x[1]
        r[2*v] -= x[0]; r[2*v+1] -= x[1]
        rows.append(r)
    cmp_force(rows, n, set())
    cmp_force(rows, n, {rnd.randrange(n)})
    cmp_rank(rows)

# ---- D. small primes / composites / p=1,2,3 ------------------------------
PS = [2,3,4,5,6,7,8,9,10,11,1,13,15,16,17,101,65537,2147483647,(1<<31)-1, 2**16, 4294967291]
for it in range(12000):
    n = rnd.randrange(1, 6)
    m = rnd.randrange(0, 7)
    rows = [[rnd.randrange(-8, 9) for _ in range(2*n)] for _ in range(m)]
    p = rnd.choice(PS)
    T0 = set(rnd.sample(range(n), rnd.randrange(0, n+1)))
    cmp_force(rows, n, T0, p)
    cmp_rank(rows, p)

# ---- E. large entries within i64, and mod-p-zero entries ------------------
BIG = [0, 1, -1, 2147483647, -2147483647, 2147483648, -2147483648, 4294967294,
       (1<<62), -(1<<62), (1<<63)-1, -(1<<63), 2147483647*3, -2147483647*5]
for it in range(8000):
    n = rnd.randrange(1, 5)
    m = rnd.randrange(0, 6)
    rows = [[rnd.choice(BIG) for _ in range(2*n)] for _ in range(m)]
    cmp_force(rows, n, set())
    cmp_rank(rows)

# ---- F. ragged / short / long rows (IndexError territory) ----------------
for it in range(12000):
    n = rnd.randrange(1, 5)
    m = rnd.randrange(0, 6)
    rows = [[rnd.randrange(-3,4) for _ in range(rnd.randrange(0, 2*n+3))] for _ in range(m)]
    T0 = set(rnd.sample(range(n), rnd.randrange(0, n+1)))
    cmp_force(rows, n, T0)
    cmp_rank(rows)

# ---- G. out-of-range / negative T0 ---------------------------------------
for it in range(8000):
    n = rnd.randrange(1, 6)
    m = rnd.randrange(0, 6)
    rows = [[rnd.randrange(-3,4) for _ in range(2*n)] for _ in range(m)]
    T0 = set(rnd.sample(range(-4, n+4), rnd.randrange(0, 4)))
    cmp_force(rows, n, T0)

# ---- H. exhaustive tiny sweep (n=1,2 over {-1,0,1} entries) --------------
vals = (-1,0,1)
cnt = 0
for n in (1,2):
    w = 2*n
    allrows = list(itertools.product(vals, repeat=w))
    for m in (1,2):
        for combo in itertools.product(range(len(allrows)), repeat=m):
            rows = [list(allrows[i]) for i in combo]
            for T0 in ([set()] if n==1 else [set(), {0}, {1}]):
                cmp_force(rows, n, T0)
            cmp_rank(rows)
            cnt += 1
print("H exhaustive tiny combos: %d" % cnt)

print("checks=%d mismatches=%d" % (nchk, len(bad)))
for b in bad[:40]:
    print("  MISMATCH", b)
