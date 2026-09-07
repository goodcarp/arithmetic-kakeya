"""r5: test antigravity's claims 1-4 (one-shot iterables as `rows`)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import fastcore, fastcore_rs
PY_F, PY_R = fastcore._force_py, fastcore._rank_py
RS_F, RS_R = fastcore_rs.force, fastcore_rs.rank

def run(lbl, mk, fn, *rest):
    fastcore._INV.clear()
    try:
        v = fn(mk(), *rest)
        v = ("ok", bool(v[0]), sorted(v[1])) if isinstance(v, tuple) else ("ok", int(v))
    except Exception as e:
        v = ("raise", type(e).__name__, str(e))
    print("   %-6s %r" % (lbl, v))
    return v

CASES = [
 ("A1 rank((r for r in []), 5)",      lambda: (r for r in []),                        "rank", (5,)),
 ("A2 rank(iter([]), 5)",             lambda: iter([]),                               "rank", (5,)),
 ("A3 force(gen [[1,2,0,0],[0,0,1,2]], 2, [], 3)",
      lambda: (r for r in [[1,2,0,0],[0,0,1,2]]), "force", (2, [], 3)),
 ("A4 force(iter [[1,-1,0,0],[0,0,1,-1]], 2, [], 5)",
      lambda: iter([[1,-1,0,0],[0,0,1,-1]]), "force", (2, [], 5)),
 # controls: same data as a plain list
 ("C3 force(list [[1,2,0,0],[0,0,1,2]], 2, [], 3)",
      lambda: [[1,2,0,0],[0,0,1,2]], "force", (2, [], 3)),
 ("C4 force(list [[1,-1,0,0],[0,0,1,-1]], 2, [], 5)",
      lambda: [[1,-1,0,0],[0,0,1,-1]], "force", (2, [], 5)),
 ("C1 rank([], 5)",                   lambda: [],                                     "rank", (5,)),
 # extra probes of my own: one-shot ROW (inner iterable), and a tuple-of-tuples
 ("X1 force([gen row], 1, [], 5)",    lambda: [(x for x in [1,-1])],                  "force", (1, [], 5)),
 ("X2 rank([iter([1,2])], 5)",        lambda: [iter([1,2])],                          "rank", (5,)),
 ("X3 force(tuple-of-tuples, 2, [], 5)",
      lambda: (((1,-1,0,0)), ((0,0,1,-1))), "force", (2, [], 5)),
 ("X4 rank(gen 1 row, 5)",            lambda: (r for r in [[1,2]]),                   "rank", (5,)),
 ("X5 force(gen 1 row, 1, [], 5)",    lambda: (r for r in [[1,-1]]),                  "force", (1, [], 5)),
]
ndiff = 0
for lbl, mk, kind, rest in CASES:
    print(lbl)
    a = run("py", mk, PY_F if kind=="force" else PY_R, *rest)
    b = run("rs", mk, RS_F if kind=="force" else RS_R, *rest)
    ax = a[:2] if a[0]=="raise" else a
    bx = b[:2] if b[0]=="raise" else b
    same = ax == bx
    print("   ->", "SAME" if same else "*** DIFF ***")
    if not same: ndiff += 1
print("\ndiffs:", ndiff, "of", len(CASES))
