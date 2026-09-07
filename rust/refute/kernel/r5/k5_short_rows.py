"""r5/kernel: two lazy-indexing behaviours of the pure-Python reference that no
earlier lens targeted.

H. force never reads columns of a row that belong to already-forced coordinates
   (U excludes them), so a row SHORTER than 2n is legal as long as T0 covers the
   tail.  A port that validates len(row) >= 2n up front would raise here.

J. rank's elimination is `[(a - fac*b) % p for a, b in zip(B[i], pr)]` -- zip
   TRUNCATES, so a short row silently shrinks to its own length instead of
   raising, and only raises later if a pivot column past that length is reached.
"""
import os, sys
SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
sys.path.insert(0, SRC)
os.environ["KAKEYA_PURE_PY"] = "1"
import fastcore, fastcore_rs
PYF, PYR, INV = fastcore._force_py, fastcore._rank_py, fastcore._INV
RSF, RSR = fastcore_rs.force, fastcore_rs.rank

N = 0; BAD = []
def case(label, kind, *a, **k):
    global N; N += 1
    INV.clear()
    try:
        v = (PYF if kind == "force" else PYR)(*a, **k)
        x = ("force", bool(v[0]), tuple(sorted(int(t) for t in v[1]))) if kind == "force" else ("rank", int(v))
    except BaseException as e: x = ("exc", type(e).__name__)
    try:
        v = (RSF if kind == "force" else RSR)(*a, **k)
        y = ("force", bool(v[0]), tuple(sorted(int(t) for t in v[1]))) if kind == "force" else ("rank", int(v))
    except BaseException as e: y = ("exc", type(e).__name__)
    tag = "ok " if x == y else "DIVERGE"
    if x != y: BAD.append((label, a, k, x, y))
    print("%-7s %-52s py=%-30s rs=%s" % (tag, label, x, y))

print("== H. short rows masked by T0 ==")
case("H1 len-2 row, n=2, T0={1}",            "force", [[1,-1]], 2, [1])
case("H2 len-2 row, n=2, T0={0}",            "force", [[1,-1]], 2, [0])
case("H3 len-2 row, n=3, T0={1,2}",          "force", [[1,-1]], 3, [1,2])
case("H4 len-4 row, n=3, T0={2}",            "force", [[1,-1,0,0]], 3, [2])
case("H5 len-4 row, n=3, T0={} (must raise)","force", [[1,-1,0,0]], 3, [])
case("H6 mixed lengths, tail masked",        "force", [[1,-1,0,0],[3,4]], 2, [1])
case("H7 mixed lengths, tail NOT masked",    "force", [[1,-1,0,0],[3,4]], 2, [])
case("H8 empty row, n=1, T0={0}",            "force", [[]], 1, [0])
case("H9 empty row, n=1, T0={} (must raise)","force", [[]], 1, [])
case("H10 len-2 row n=2 T0={1} p=7",         "force", [[1,6]], 2, [1], p=7)
case("H11 round-2 exposes the short tail",   "force", [[1,-1,0,0],[0,0,1,-1],[5,5]], 2, [])
case("H12 short row, T0 masks in round 1 only","force", [[0,0,1,-1],[9,9]], 2, [1])

print()
print("== J. rank zip-truncation on short trailing rows ==")
case("J1 rank [[1,2,3],[1,2]]",   "rank", [[1,2,3],[1,2]])
case("J2 rank [[1,2,3],[1,3]]",   "rank", [[1,2,3],[1,3]])
case("J3 rank [[1,2,3],[0,2]]",   "rank", [[1,2,3],[0,2]])
case("J4 rank [[1,2,3],[2]]",     "rank", [[1,2,3],[2]])
case("J5 rank [[1,2,3],[0]]",     "rank", [[1,2,3],[0]])
case("J6 rank [[1,2,3,4],[1,2],[0,0,1,1]]", "rank", [[1,2,3,4],[1,2],[0,0,1,1]])
case("J7 rank [[1,0,0],[1,1],[1,1,1]]",     "rank", [[1,0,0],[1,1],[1,1,1]])
case("J8 rank [[0,1,1],[1,2]]",   "rank", [[0,1,1],[1,2]])
case("J9 rank [[1,1],[1,1,1]] (long trailing row)", "rank", [[1,1],[1,1,1]])
case("J10 rank [[1,1],[2,2,2],[0,0,5]]",    "rank", [[1,1],[2,2,2],[0,0,5]])
case("J11 rank [[1,2,3],[1,2]] p=7",        "rank", [[1,2,3],[1,2]], p=7)
case("J12 rank [[2,2,2],[2,2]] p=4",        "rank", [[2,2,2],[2,2]], p=4)

print()
print("cases=%d  divergences=%d" % (N, len(BAD)))
for b in BAD:
    print("  DIVERGE %s\n     args=%r kw=%r\n     py=%r rs=%r" % (b[0], b[1], b[2], b[3], b[4]))
sys.exit(1 if BAD else 0)
