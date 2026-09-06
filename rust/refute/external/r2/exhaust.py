"""Exhaustive small-input differential: pure-Python fastcore vs fastcore_rs.

Covers what difftest.py's random sweep does not: tiny p (1,2,3,4), p at the
2^32 ceiling, every ragged row shape up to length 4, n<=0, and out-of-range T0.
"""
import itertools, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import fastcore, fastcore_rs
PY_F = fastcore._force_py; PY_R = fastcore._rank_py
RS_F = fastcore_rs.force;  RS_R = fastcore_rs.rank

def cpy(fn, *a):
    fastcore._INV.clear()
    try: return ("ok", fn(*a))
    except Exception as e: return ("exc", type(e).__name__)
def crs(fn, *a):
    try: return ("ok", fn(*a))
    except Exception as e: return ("exc", type(e).__name__)
def nf(t):
    k, v = t
    if k == "exc": return ("exc", v)
    ok, T = v; return ("ok", bool(ok), tuple(sorted(T)))
def nr(t):
    k, v = t
    if k == "exc": return ("exc", v)
    return ("ok", int(v))

bad = []
cases = 0
def chk(kind, args):
    global cases
    cases += 1
    if kind == "force":
        a = nf(cpy(PY_F, *args)); b = nf(crs(RS_F, *args))
    else:
        a = nr(cpy(PY_R, *args)); b = nr(crs(RS_R, *args))
    if a != b and len(bad) < 40:
        bad.append((kind, args, a, b))
    return a == b

PS = [int(x) for x in os.environ.get("EX_PS", "1,2,3,4,5,6,7,8,9,91,2147483647,4294967291,4294967295").split(",")]
MAXLEN = int(os.environ.get("EX_MAXLEN", "4"))
ENTRIES = [0, 1, 2, 3, -1, -2]

def rowsets(maxlen, entries, lens=None):
    out = []
    for L in (lens if lens is not None else range(maxlen + 1)):
        for t in itertools.product(entries, repeat=L):
            out.append(list(t))
    return out

t0 = time.time()
# --- pass 1: single row, exhaustive over shape+entries -----------------------
R1 = rowsets(MAXLEN, [0, 1, 2, -1])
print("pass1 rows:", len(R1))
for p in PS:
    for r in R1:
        chk("rank", ([r], p))
        for n in (0, 1, 2):
            for T0 in (set(), {0}, {1}, {5}, {-1}, {0, 1}):
                chk("force", ([r], n, T0, p))
print("pass1 done %d cases %.1fs bad=%d" % (cases, time.time() - t0, len(bad)))

# --- pass 2: two rows, shorter shapes ---------------------------------------
R2 = rowsets(3, [0, 1, 2])
print("pass2 rows:", len(R2))
for p in (2, 3, 4, 7, 2147483647):
    for r1 in R2:
        for r2 in R2:
            chk("rank", ([r1, r2], p))
            for n in (1, 2):
                chk("force", ([r1, r2], n, set(), p))
print("pass2 done %d cases %.1fs bad=%d" % (cases, time.time() - t0, len(bad)))

# --- pass 3: negative / zero / huge n, weird T0 ------------------------------
for n in (-3, -1, 0, 1, 2, 3):
    for T0 in (set(), {0}, {-1}, {99}, {0, -1, 99}, {0, 1, 2, 3}):
        for rows in ([], [[1, -1]], [[1, -1, 0, 0], [0, 0, 1, -1]], [[0, 0]], [[]]):
            for p in (2, 7, 2147483647):
                chk("force", (rows, n, T0, p))
print("pass3 done %d cases %.1fs bad=%d" % (cases, time.time() - t0, len(bad)))

# --- pass 4: entries near p and near i64 -------------------------------------
P = (1 << 31) - 1
NEAR = [P - 1, P, P + 1, 2 * P, -P, -P - 1, 2**31, -2**31, 2**62, -2**62,
        2**62 - 1, 2**63 - 1, -2**63, 0, 1, -1]
for p in (2, 3, 7, 91, P, 4294967291, 4294967295):
    for a in NEAR:
        for b in NEAR:
            chk("rank", ([[a, b]], p))
            chk("force", ([[a, b]], 1, set(), p))
    for a in NEAR:
        chk("rank", ([[a]], p))
        chk("rank", ([[a, 1], [1, a]], p))
        chk("force", ([[a, 1], [1, a]], 1, set(), p))
print("pass4 done %d cases %.1fs bad=%d" % (cases, time.time() - t0, len(bad)))

print("=" * 60)
print("total cases %d  mismatches %d" % (cases, len(bad)))
for k, a, x, y in bad:
    print("  %s%r\n      py=%r\n      rs=%r" % (k, a, x, y))
