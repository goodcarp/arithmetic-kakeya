"""Minimal repros for the divergence class this lens found:

PyO3's i64 extraction goes through __index__ (PyNumber_Index), so the Rust
ACCEPTS objects the pure-Python reference REJECTS with TypeError -- and in the
T0 case returns a numerically different set.  The S1 contract sec 5.4 sanctions
the opposite direction only (Rust raises where Python works).
"""
import sys
sys.path.insert(0, ".")
import harness

mod = harness.load_rs(sys.argv[1] if len(sys.argv) > 1 else "shipped")
PYF, PYR, INV = harness.PY_FORCE, harness.PY_RANK, harness.INV


class Idx:
    """Anything with __index__ and no __mod__: numpy scalars are the real-world
    instance of this shape."""
    def __init__(self, v):
        self.v = v

    def __index__(self):
        return self.v

    def __repr__(self):
        return f"Idx({self.v})"


def show(label, fn_py, fn_rs):
    INV.clear()
    try:
        a = ("value", fn_py())
    except BaseException as e:
        a = ("raises", type(e).__name__, str(e))
    try:
        b = ("value", fn_rs())
    except BaseException as e:
        b = ("raises", type(e).__name__, str(e))
    verdict = "SAME" if a == b else "DIVERGES"
    print(f"[{verdict}] {label}")
    print(f"    python: {a}")
    print(f"    rust  : {b}")
    return a != b


n = 0
print("== R1: entry with __index__ (numpy integer scalar is the real case) ==")
n += show("rank([[Idx(1), Idx(2)]])",
          lambda: PYR([[Idx(1), Idx(2)]]), lambda: mod.rank([[Idx(1), Idx(2)]]))
n += show("force([[Idx(1), Idx(-1), 0, 0]], 1, set())",
          lambda: PYF([[Idx(1), Idx(-1), 0, 0]], 1, set()),
          lambda: mod.force([[Idx(1), Idx(-1), 0, 0]], 1, set()))

try:
    import numpy as np
    print(f"\n== R2: numpy {np.__version__} integer scalars ==")
    n += show("rank([[np.int64(1), np.int64(2)], [np.int64(2), np.int64(4)]])",
              lambda: PYR([[np.int64(1), np.int64(2)], [np.int64(2), np.int64(4)]]),
              lambda: mod.rank([[np.int64(1), np.int64(2)], [np.int64(2), np.int64(4)]]))
    n += show("force([[np.int64(1), np.int64(-1), 0, 0]], 1, set())",
              lambda: PYF([[np.int64(1), np.int64(-1), 0, 0]], 1, set()),
              lambda: mod.force([[np.int64(1), np.int64(-1), 0, 0]], 1, set()))
except ImportError:
    print("\n(numpy not importable)")

print("\n== R3: T0 element with __index__ -> two different sets, both ok=True ==")
rows = [[1, -1, 0, 0], [0, 0, 1, -1]]
n += show("force([[1,-1,0,0],[0,0,1,-1]], 2, {Idx(0)})",
          lambda: PYF(rows, 2, {Idx(0)}), lambda: mod.force(rows, 2, {Idx(0)}))

print("\n== R4: n with __index__ ==")
n += show("force([[1,-1,0,0]], Idx(1), set())",
          lambda: PYF([[1, -1, 0, 0]], Idx(1), set()),
          lambda: mod.force([[1, -1, 0, 0]], Idx(1), set()))

print("\n== R5: p with __index__ ==")
n += show("rank([[1,2]], p=Idx(7))",
          lambda: PYR([[1, 2]], Idx(7)), lambda: mod.rank([[1, 2]], Idx(7)))

print("\n== R6: two documented divergences colliding (entry>i64 AND p==0) ==")
n += show("rank([[2**63, 1], [1, 1]], p=0)",
          lambda: PYR([[2**63, 1], [1, 1]], 0),
          lambda: mod.rank([[2**63, 1], [1, 1]], 0))

print(f"\ndiverging repros: {n}")
