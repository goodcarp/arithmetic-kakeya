"""r5 external: wide independent differential sweep of force/rank.

Pure-Python originals (fastcore._force_py/_rank_py) vs the Rust PyO3 module
(fastcore_rs.force/rank), same process.  _INV cleared before EVERY call so the
documented cross-p cache quirk never fires.

Widens r2's sweep on the axes it left narrow: entry values (r2 used {0,1} only),
modulus (r2 used p in {0,1,2}), row raggedness, and n > row width.
"""
import itertools, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import fastcore, fastcore_rs

PY_F, PY_R = fastcore._force_py, fastcore._rank_py
RS_F, RS_R = fastcore_rs.force, fastcore_rs.rank
P = fastcore.P


def call(fn, *a):
    fastcore._INV.clear()
    try:
        v = fn(*a)
    except Exception as e:
        return ("raise", type(e).__name__)
    if isinstance(v, tuple):
        return ("ok", bool(v[0]), tuple(sorted(v[1])))
    return ("ok", int(v))


def cmp(kind, args):
    f_py, f_rs = (PY_F, RS_F) if kind == "force" else (PY_R, RS_R)
    a = call(f_py, *args)
    b = call(f_rs, *args)
    return a, b, (a == b)


PS = [0, 1, 2, 3, 4, 5, 7, 9, 257, (1 << 31) - 1, (1 << 32) - 1, 1 << 32, (1 << 32) + 1, -5]
ENT = [0, 1, -1, 2, -2, 3, 6, 4294967295, 4294967296, 4294967297,
       (1 << 62), -(1 << 62), (1 << 63) - 1, -(1 << 63), True, False]

def DOC(p):
    """documented divergences: p<0 and p>=2**32 are ValueError in Rust"""
    return p < 0 or p >= (1 << 32)

bad = []
ndoc = [0]
n_cases = 0
t_start = time.time()

# ---- block 1: rank, exhaustive over small ragged shapes with wide entries ---
random.seed(20260906)
shapes = []
for nr in (1, 2, 3):
    for lens in itertools.product((0, 1, 2, 3), repeat=nr):
        shapes.append(list(lens))
for p in PS:
    for sh in shapes:
        for _ in range(3):
            rows = [[random.choice(ENT) for _ in range(L)] for L in sh]
            n_cases += 1
            a, b, ok = cmp("rank", (rows, p))
            if not ok and not DOC(p):
                bad.append(("rank", rows, p, a, b))
print("block1 rank ragged/wide-entry: cases=%d mismatches=%d  (%.1fs)"
      % (n_cases, len(bad), time.time() - t_start))

# ---- block 2: force, ragged + n larger than row width ----------------------
b2_bad = []
c2 = 0
for p in PS:
    for nr in (0, 1, 2):
        for L in (0, 1, 2, 3, 4, 6):
            for n in (0, 1, 2, 3):
                for T0 in ((), (0,), (1,), (0, 0), (-1,), (5,), (0, 5, -1), (True,)):
                    rows = [[random.choice(ENT) for _ in range(L)] for _ in range(nr)]
                    c2 += 1
                    a, b, ok = cmp("force", (rows, n, list(T0), p))
                    if not ok and not DOC(p):
                        b2_bad.append((rows, n, list(T0), p, a, b))
print("block2 force ragged/n-vs-width: cases=%d mismatches=%d  (%.1fs)"
      % (c2, len(b2_bad), time.time() - t_start))

# ---- block 3: force, exhaustive small over entries {0,1,p-1,2} at p=5,7,P ---
b3_bad = []
c3 = 0
for p in (5, 7, P):
    E = [0, 1, p - 1, 2]
    for n in (1, 2):
        w = 2 * n
        for nr in (1, 2):
            for cells in itertools.product(E, repeat=w * nr):
                rows = [list(cells[i * w:(i + 1) * w]) for i in range(nr)]
                for T0 in ((), (0,)):
                    c3 += 1
                    a, b, ok = cmp("force", (rows, n, list(T0), p))
                    if not ok and not DOC(p):
                        b3_bad.append((rows, n, list(T0), p, a, b))
            if nr == 2 and n == 2:
                break  # 4^8*... too big; the n=2/nr=1 and n=1 blocks carry it
print("block3 force exhaustive-small: cases=%d mismatches=%d  (%.1fs)"
      % (c3, len(b3_bad), time.time() - t_start))

# ---- block 4: rank exhaustive tiny over p, entries {0,1,p-1} --------------
b4_bad = []
c4 = 0
for p in (2, 3, 4, 5, 9, P, (1 << 32) - 1):
    E = [0, 1, p - 1]
    for nr in (1, 2, 3):
        for w in (1, 2, 3):
            for cells in itertools.product(E, repeat=w * nr):
                rows = [list(cells[i * w:(i + 1) * w]) for i in range(nr)]
                c4 += 1
                a, b, ok = cmp("rank", (rows, p))
                if not ok and not DOC(p):
                    b4_bad.append((rows, p, a, b))
print("block4 rank exhaustive-tiny: cases=%d mismatches=%d  (%.1fs)"
      % (c4, len(b4_bad), time.time() - t_start))

TOT = n_cases + c2 + c3 + c4
ALL = bad + b2_bad + b3_bad + b4_bad
print("\nTOTAL cases=%d  mismatches=%d" % (TOT, len(ALL)))
for x in ALL:
    print("  MISMATCH", x)
