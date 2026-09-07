"""Decisive witness: a *list subclass* whose __getitem__ disagrees with its
iterator.  Python's force subscripts (r[2*j]); the Rust boundary iterates."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "src")))
import fastcore, fastcore_rs
P = fastcore.P
class Rev(list):
    def __getitem__(self, i): return list.__getitem__(self, len(self) - 1 - i)
def go(fn, *a):
    fastcore._INV.clear()
    try:
        v = fn(*a)
        return ("ok", bool(v[0]), sorted(v[1])) if isinstance(v, tuple) else ("ok", int(v))
    except Exception as e: return ("raise", type(e).__name__)
raw = [1, P - 1, 0, 0]
print("row (raw storage) =", raw, " isinstance(row, list) =", isinstance(Rev(raw), list))
a = go(fastcore._force_py,  [Rev(raw)], 2, [], P)
b = go(fastcore_rs.force,   [Rev(raw)], 2, [], P)
print("py:", a); print("rs:", b); print("->", "SAME" if a == b else "*** DIFF ***")
