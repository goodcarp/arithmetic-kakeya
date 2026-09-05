"""Exception-message fidelity, exotic container protocols, and .so drift.

Run under both /usr/bin/python3 (3.9.6) and /usr/local/bin/python3.12.
Pass a directory as argv[1] to prepend to sys.path (used to load a freshly
built .so instead of the deployed src/fastcore_rs.abi3.so).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "..", "..", "src"))
sys.path.insert(0, HERE)
sys.path.insert(0, SRC)
if len(sys.argv) > 1:
    sys.path.insert(0, os.path.abspath(sys.argv[1]))

import orig_fastcore as PY  # noqa: E402
import fastcore_rs as RS  # noqa: E402

print("python", sys.version.split()[0], "| fastcore_rs from", RS.__file__)


def ex(fn, *a, **k):
    try:
        PY._INV.clear()
    except Exception:
        pass
    try:
        v = fn(*a, **k)
        return ("val", repr(v) if not isinstance(v, tuple) else
                "(%r, %s)" % (v[0], sorted(v[1])))
    except BaseException as e:  # noqa: BLE001
        return ("exc", type(e).__name__, str(e))


CASES = [
    ("rank ragged IndexError", "rank", ([[1, 0, 0], [0, 1]],), {}),
    ("force short row IndexError", "force", ([[1, -1]], 2, set()), {}),
    ("rank p=0 ZeroDivisionError", "rank", ([[1, 0]],), {"p": 0}),
    ("force p=0 ZeroDivisionError", "force", ([[1, -1]], 1, set(), 0), {}),
    ("rank str entry TypeError", "rank", ([["a", 1]],), {}),
    ("force T0 float TypeError", "force", ([[1, -1]], 1, {0.5}), {}),
]

print("\n--- exception type AND message ---")
diffs = 0
for label, name, a, k in CASES:
    pa = ex(getattr(PY, name), *a, **k)
    pb = ex(getattr(RS, name), *a, **k)
    same_type = pa[:2] == pb[:2]
    same_msg = pa == pb
    flag = "SAME " if same_msg else ("TYPE-ONLY" if same_type else "DIVERGE ")
    if not same_msg:
        diffs += 1
    print("%-10s %-32s py=%s | rs=%s" % (flag, label, pa, pb))

print("\n--- exotic containers ---")
class SeqOnly:
    """old-style sequence protocol: __getitem__ but no __iter__"""

    def __init__(self, items):
        self.items = items

    def __getitem__(self, i):
        return self.items[i]

    def __len__(self):
        return len(self.items)


class LyingLen:
    def __len__(self):
        return 0

    def __iter__(self):
        return iter([[1, 0], [0, 1]])


EX = [
    ("rows = dict of tuples", "rank", ({(1, 0): 'a', (0, 1): 'b'},), {}),
    ("rows = set of tuples", "rank", ({(1, 0), (0, 1)},), {}),
    ("rows = SeqOnly", "rank", (SeqOnly([[1, 0], [0, 1]]),), {}),
    ("rows = LyingLen(__len__=0)", "rank", (LyingLen(),), {}),
    ("row = SeqOnly", "rank", ([SeqOnly([1, 0]), SeqOnly([0, 1])],), {}),
    ("row = dict", "rank", ([{1: 'x', 0: 'y'}, {0: 'a', 1: 'b'}],), {}),
    ("row = range", "rank", ([range(1, 3), range(0, 2)],), {}),
    ("rows = bytes", "rank", (b"\x01\x00",), {}),
    ("rows = bytearray", "rank", (bytearray(b"\x01\x00"),), {}),
    ("T0 = dict", "force", ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, {0: 'a'}), {}),
    ("T0 = str", "force", ([[1, -1, 0, 0]], 1, "0"), {}),
    ("T0 = bytes", "force", ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, b"\x00"), {}),
    ("T0 = range(1)", "force", ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, range(1)), {}),
]
for label, name, a, k in EX:
    pa = ex(getattr(PY, name), *a, **k)
    pb = ex(getattr(RS, name), *a, **k)
    print("%-9s %-30s py=%-40s rs=%s" % ("SAME" if pa[:2] == pb[:2] else "DIVERGE",
                                         label, str(pa)[:40], pb))
    if pa[:2] != pb[:2]:
        diffs += 1

print("\n--- introspection ---")
import inspect  # noqa: E402
for f in (RS.force, RS.rank):
    try:
        print("  signature(%s) = %s" % (f.__name__, inspect.signature(f)))
    except Exception as e:  # noqa: BLE001
        print("  signature(%s) raises %r" % (f.__name__, e))
print("  type(fastcore_rs.force) =", type(RS.force))
print("  PY force defaults =", PY.force.__defaults__)

print("\ndiff-count:", diffs)
