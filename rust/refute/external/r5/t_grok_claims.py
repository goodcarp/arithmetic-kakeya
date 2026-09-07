"""r5: test grok-cli's kernel claims (only the ones not already in the
documented-divergence list), plus my own follow-ups in the same class."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import fastcore, fastcore_rs
PY_F, PY_R = fastcore._force_py, fastcore._rank_py
RS_F, RS_R = fastcore_rs.force, fastcore_rs.rank
P = fastcore.P

def go(fn, mk):
    fastcore._INV.clear()
    try:
        v = fn(*mk())
        return ("ok", bool(v[0]), sorted(v[1], key=repr)) if isinstance(v, tuple) else ("ok", int(v))
    except Exception as e:
        return ("raise", type(e).__name__)

CASES = [
 ("G8  rank([[0.0]], P)",            "rank",  lambda: ([[0.0]], P)),
 ("G10 rank([[1,'x']], 0)",          "rank",  lambda: ([[1, "x"]], 0)),
 ("G11 force([dict row], 1, [], P)", "force", lambda: ([{0: 1, 1: P - 1}], 1, [], P)),
 ("G12 force([[1]], 1, [], -5)",     "force", lambda: ([[1]], 1, [], -5)),
 ("G13 rank([[0]], 2.5)",            "rank",  lambda: ([[0]], 2.5)),
 ("G14 force([], 1, '0', P)",        "force", lambda: ([], 1, "0", P)),
 ("G15 rank([[1]], 2**63)",          "rank",  lambda: ([[1]], 2**63)),
 # my own follow-ups in the same class
 ("M1  rank([dict row], P)",         "rank",  lambda: ([{0: 1, 1: P - 1}], P)),
 ("M2  force([dict row], 1, [], P) k=[1,0]", "force", lambda: ([{1: 1, 0: P - 1}], 1, [], P)),
 ("M3  force(dict-of-rows, 1, [], P)", "force", lambda: ({0: [1, P - 1]}, 1, [], P)),
 ("M4  rank(dict-of-rows, P)",       "rank",  lambda: ({0: [1, 2]}, P)),
 ("M5  force([str row '12'],1,[],P)","force", lambda: (["12"], 1, [], P)),
 ("M6  force([[1,-1]], 1, {0:'a'}, P) T0=dict", "force", lambda: ([[1, -1]], 1, {0: "a"}, P)),
 ("M7  force([bytearray], 1, [], P)","force", lambda: ([bytearray([1, 2])], 1, [], P)),
 ("M8  rank([range(2)], P)",         "rank",  lambda: ([range(2)], P)),
 ("M9  force([range(2)], 1, [], P)", "force", lambda: ([range(2)], 1, [], P)),
]
ndiff = 0
for lbl, kind, mk in CASES:
    a = go(PY_F if kind == "force" else PY_R, mk)
    b = go(RS_F if kind == "force" else RS_R, mk)
    same = a == b
    ndiff += 0 if same else 1
    print("%-4s %-46s py=%-34r rs=%r" % ("SAME" if same else "DIFF", lbl, a, b))
print("\ndiffs:", ndiff, "of", len(CASES))
