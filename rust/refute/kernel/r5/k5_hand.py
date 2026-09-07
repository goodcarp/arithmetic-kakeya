"""r5/kernel: 40 hand-crafted force/rank cases aimed at what modular, control and
boundary did not target: greedy-choice ordering across rounds, the zero-inverse
pivot state under composite p, p in {1,2}, degenerate rank rows, out-of-range /
negative T0, warm-start monotonicity, and n at the Rust 2**20 clamp.

Reference is fastcore._force_py / _rank_py with fastcore._INV.clear() before
every call.  Comparison is on VALUE (ints), not repr, so {True} == {1}.
"""
import os, sys
SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
sys.path.insert(0, SRC)
os.environ["KAKEYA_PURE_PY"] = "1"
import fastcore, fastcore_rs

PYF, PYR, INV = fastcore._force_py, fastcore._rank_py, fastcore._INV
RSF, RSR = fastcore_rs.force, fastcore_rs.rank

def nf(v):
    ok, T = v
    return ("force", bool(ok), tuple(sorted(int(x) for x in T)))
def nr(v):
    return ("rank", int(v))

def run(kind, fn, args, kw, clear):
    if clear: INV.clear()
    try:
        v = fn(*args, **kw)
        return (nf if kind == "force" else nr)(v)
    except BaseException as e:
        return ("exc", type(e).__name__)

N = 0; BAD = []
def case(label, kind, *args, **kw):
    global N
    N += 1
    a = run(kind, PYF if kind == "force" else PYR, args, kw, True)
    b = run(kind, RSF if kind == "force" else RSR, args, kw, False)
    tag = "ok " if a == b else "DIVERGE"
    if a != b: BAD.append((label, args, kw, a, b))
    print("%-7s %-58s py=%-34s rs=%s" % (tag, label, a, b))

# --- A. greedy-choice ordering across rounds -------------------------------
# force picks the SMALLEST j in U whose delta_v lies in the span, then re-does
# the whole reduction with that j removed.  A port that picked a different
# qualifying j would still return ok=True but a different T, or a different
# partial T on failure.
r2 = lambda n: [[0]*(2*n) for _ in range(0)]
case("A1 two qualify, must take j=0", "force",
     [[1,-1,0,0],[0,0,1,-1]], 2, [])
case("A2 two qualify, reversed rows", "force",
     [[0,0,1,-1],[1,-1,0,0]], 2, [])
case("A3 only j=1 qualifies (partial T on fail)", "force",
     [[0,0,1,-1]], 2, [])
case("A4 only j=2 qualifies of 3", "force",
     [[0,0,0,0,1,-1]], 3, [])
case("A5 round2 unlocks j=0 after j=2", "force",
     [[0,0,0,0,1,-1],[1,-1,3,4,0,0],[0,0,3,4,0,0]], 3, [])
case("A6 4 coords, cascade 3->0->1, fails at 2", "force",
     [[0,0,0,0,0,0,1,-1],[1,-1,0,0,0,0,5,5],[0,0,1,-1,0,0,0,0]], 4, [])
case("A7 same rows, T0 pre-seeds the LAST coord", "force",
     [[0,0,0,0,0,0,1,-1],[1,-1,0,0,0,0,5,5],[0,0,1,-1,0,0,0,0]], 4, [3])
case("A8 row nonzero only on forced coords (dropped in round 2)", "force",
     [[1,-1,0,0],[7,3,0,0]], 2, [])
case("A9 all rows drop in round 2 -> fail with T={0}", "force",
     [[1,-1,0,0],[5,5,0,0]], 2, [])

# --- B. composite p, zero-inverse pivot ------------------------------------
# _inv(2,4)=pow(2,2,4)=0 -> the pivot row becomes all zeros, rk still advances
# and the pivot column is appended to piv.  Rows below keep a nonzero there.
case("B1 rank p=4 zero-inverse pivot", "rank", [[2,1],[0,2]], p=4)
case("B2 rank p=4 pivot 2, row below nonzero at same col", "rank", [[2,3],[2,1]], p=4)
case("B3 rank p=8 pivot 2 (inv=pow(2,6,8)=0)", "rank", [[2,1,1],[4,1,0],[6,0,1]], p=8)
case("B4 rank p=9 pivot 3 (inv=pow(3,7,9)=0)", "rank", [[3,1],[6,2]], p=9)
case("B5 force p=4 zero-inverse pivot in the span test", "force",
     [[2,2,1,3],[0,2,2,1]], 2, [], p=4)
case("B6 force p=8 three rows, two zero-inverse pivots", "force",
     [[2,6,1,1],[4,4,2,2],[1,7,0,0]], 2, [], p=8)
case("B7 force p=6 pivot 2 and 3 both zero-inverse", "force",
     [[2,3,1,5],[3,2,5,1]], 2, [], p=6)
case("B8 rank p=4, 4 rows all even", "rank", [[2,2],[2,0],[0,2],[2,2]], p=4)

# --- C. p = 1 and p = 2 -----------------------------------------------------
case("C1 rank p=1", "rank", [[1,2],[3,4]], p=1)
case("C2 force p=1", "force", [[1,-1,0,0],[0,0,1,-1]], 2, [], p=1)
case("C3 force p=1 n=0", "force", [[1,2]], 0, [], p=1)
case("C4 rank p=2 identity", "rank", [[1,0],[0,1]], p=2)
case("C5 rank p=2 all entries even", "rank", [[2,4],[6,8]], p=2)
case("C6 force p=2 (delta = e_a + e_b since p-1 == 1)", "force",
     [[1,1,0,0],[0,0,1,1]], 2, [], p=2)
case("C7 force p=2, -1 == 1", "force", [[1,-1,0,0]], 2, [], p=2)
case("C8 force p=2 three coords", "force",
     [[1,1,0,0,0,0],[0,0,1,1,0,0],[0,0,0,0,1,1]], 3, [], p=2)
case("C9 rank p=3 with -1 entries (floored mod)", "rank", [[-1,-2],[-2,-4]], p=3)

# --- D. degenerate rank rows ------------------------------------------------
case("D1 rank [[]]", "rank", [[]])
case("D2 rank [[],[]]", "rank", [[],[]])
case("D3 rank [[],[1,2]] (w from row 0)", "rank", [[],[1,2]])
case("D4 rank [[1,2],[]] (ragged short second row)", "rank", [[1,2],[]])
case("D5 rank []", "rank", [])
case("D6 rank all-zero 5x5", "rank", [[0]*5 for _ in range(5)])
case("D7 rank rk hits nB before columns run out", "rank", [[0,0,0,1]])
case("D8 rank single row of P (P%P==0)", "rank", [[2147483647, 2147483647]])
case("D9 rank duplicate rows", "rank", [[1,2,3],[1,2,3],[1,2,3]])
case("D10 rank tall 9x2", "rank", [[i % 7, (i*i) % 11] for i in range(9)])

# --- E. out-of-range / negative T0 -----------------------------------------
case("E1 T0 negative fills the count", "force", [], 3, [-1,-2,-3])
case("E2 T0 negative + in-range mix", "force", [[1,-1,0,0]], 2, [-5])
case("E3 T0 huge in-range-count", "force", [], 2, [10**6, 10**6+1])
case("E4 T0 with 0 and n (n itself out of range)", "force", [[1,-1,0,0]], 2, [2])
case("E5 T0 duplicates collapse below n", "force", [[1,-1,0,0]], 2, [1,1,1])
case("E6 n=0 rows nonempty", "force", [[9,9]], 0, [])
case("E7 n=0 T0 nonempty", "force", [[9,9]], 0, [4,5])

# --- F. warm-start monotonicity --------------------------------------------
ROWS_F = [[1,-1,0,0,0,0],[0,0,1,-1,0,0],[0,0,0,0,1,-1]]
case("F1 cold", "force", ROWS_F, 3, [])
case("F2 warm from {0}", "force", ROWS_F, 3, [0])
case("F3 warm from {0,1}", "force", ROWS_F, 3, [0,1])
case("F4 warm from full", "force", ROWS_F, 3, [0,1,2])
FAILROWS = [[0,0,1,-1,0,0]]
case("F5 fail cold", "force", FAILROWS, 3, [])
case("F6 fail warm from the partial T it returned", "force", FAILROWS, 3, [1])

# --- G. n at the Rust clamp -------------------------------------------------
case("G1 n=2**20 with T0=range short-circuit", "force", [], 1<<20, range(1<<20))
case("G2 n=2**20-1 T0 short-circuit", "force", [], (1<<20)-1, range((1<<20)-1))
case("G3 n=1 huge oversized row", "force", [[1,-1]+[0]*4096], 1, [])
case("G4 rank 1 x 4096", "rank", [[(i*i) % 97 for i in range(4096)]])

print()
print("cases=%d  divergences=%d" % (N, len(BAD)))
for b in BAD:
    print("  DIVERGE", b[0])
    print("     args=%r kw=%r" % (b[1], b[2]))
    print("     py=%r  rs=%r" % (b[3], b[4]))
sys.exit(1 if BAD else 0)
