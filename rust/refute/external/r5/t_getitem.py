"""r5 follow-up: rows whose __getitem__ and __iter__ disagree.
Python's force uses r[2*j] (getitem); the Rust boundary uses iteration."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import fastcore, fastcore_rs
P = fastcore.P

class Rev(list):
    """iterates forward, but __getitem__ returns the reversed element"""
    def __getitem__(self, i):
        return list.__getitem__(self, len(self) - 1 - i)

class OldSeq:
    """no __iter__; only the legacy getitem sequence protocol"""
    def __init__(self, v): self.v = v
    def __getitem__(self, i):
        if i >= len(self.v): raise IndexError(i)
        return self.v[i]

def go(fn, mk):
    fastcore._INV.clear()
    try:
        v = fn(*mk())
        return ("ok", bool(v[0]), sorted(v[1], key=repr)) if isinstance(v, tuple) else ("ok", int(v))
    except Exception as e:
        return ("raise", type(e).__name__)

CASES = [
 ("R1 force([Rev([P-1,1])], 1, [], P)", "force", lambda: ([Rev([P-1, 1])], 1, [], P)),
 ("R2 rank([Rev([0,1])], P)",           "rank",  lambda: ([Rev([0, 1])], P)),
 ("R3 force([OldSeq([1,P-1])],1,[],P)", "force", lambda: ([OldSeq([1, P-1])], 1, [], P)),
 ("R4 rank([OldSeq([1,2])], P)",        "rank",  lambda: ([OldSeq([1, 2])], P)),
 ("R5 force([{0:1,1:P-1}],1,[],P) again","force", lambda: ([{0: 1, 1: P-1}], 1, [], P)),
]
n = 0
for lbl, kind, mk in CASES:
    a = go(fastcore._force_py if kind == "force" else fastcore._rank_py, mk)
    b = go(fastcore_rs.force if kind == "force" else fastcore_rs.rank, mk)
    same = a == b; n += 0 if same else 1
    print("%-4s %-40s py=%-30r rs=%r" % ("SAME" if same else "DIFF", lbl, a, b))
print("diffs:", n, "of", len(CASES))
