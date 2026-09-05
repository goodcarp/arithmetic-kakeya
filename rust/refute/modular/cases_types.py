"""Argument-extraction ordering, integer-like types, and input mutation.

Lens note: Python reduces with `%`, which dispatches on __mod__ and therefore
accepts floats, Fractions, Decimals and numpy scalars.  PyO3 extracts i64.
Where the two disagree on *which* objects are integers, the port diverges.
"""
from fractions import Fraction
from decimal import Decimal


class MyInt(int):
    pass


class Idx:
    def __init__(self, v):
        self.v = v

    def __index__(self):
        return self.v


try:
    import numpy as _np
except Exception:
    _np = None

P = (1 << 31) - 1


def cases():
    C = []
    a = C.append

    # ---- argument extraction: p and n outside i64 -------------------------
    a(("rank", ([],), {"p": 1 << 64}))          # Python short-circuits to 0
    a(("rank", ([],), {"p": -(1 << 64)}))
    a(("rank", ((),), {"p": 1 << 64}))
    a(("rank", ([[1, 2]],), {"p": 1 << 64}))
    a(("rank", ([[1, 2]],), {"p": (1 << 63) - 1}))
    a(("rank", ([[1, 2]],), {"p": 1 << 63}))
    a(("force", ([], 0, set()), {"p": 1 << 64}))
    a(("force", ([], 0, set()), {"p": -(1 << 64)}))
    # force([], 2**64, {0}) is omitted: the reference would build a
    # range(2**64) closure loop and never return.  Rust answers OverflowError
    # immediately; recorded separately in run_types.py.
    a(("force", ([], -(1 << 64), {0}), {}))
    a(("force", ([[1, -1, 0, 0]], 2, set(), 1 << 64), {}))   # positional p

    # ---- integer-like entry types -----------------------------------------
    a(("rank", ([[MyInt(1), MyInt(2)], [MyInt(2), MyInt(4)]],), {}))
    a(("rank", ([[MyInt(3), 1], [1, 3]],), {"p": 7}))
    a(("force", ([[MyInt(1), MyInt(-1), 0, 0]], 1, set()), {}))
    a(("rank", ([[Idx(1), Idx(2)]],), {}))
    a(("force", ([[Idx(1), Idx(-1), 0, 0]], 1, set()), {}))
    a(("rank", ([[0.0, 0.0]],), {}))        # Python: 0 (falsy floats, no pow)
    a(("rank", ([[1.0, 2.0]],), {}))        # Python: TypeError inside pow
    a(("rank", ([[1.5, 2.5]],), {}))
    a(("force", ([[0.0, 0.0]], 1, set()), {}))
    a(("force", ([[1.0, -1.0, 0.0, 0.0]], 1, set()), {}))
    a(("rank", ([[Fraction(1), Fraction(2)]],), {}))
    a(("rank", ([[Fraction(0), Fraction(0)]],), {}))
    a(("rank", ([[Decimal(0), Decimal(0)]],), {}))
    a(("rank", ([[Decimal(1), Decimal(2)]],), {}))
    a(("rank", ([[None, 1]],), {}))
    a(("rank", ([["1", 2]],), {}))
    a(("rank", ([[complex(1, 0), 1]],), {}))
    if _np is not None:
        a(("rank", ([[_np.int64(1), _np.int64(2)], [_np.int64(2), _np.int64(4)]],), {}))
        a(("rank", ([[_np.int64(0), _np.int64(0)]],), {}))
        a(("rank", ([[_np.int32(3), _np.int32(1)], [_np.int32(1), _np.int32(3)]],), {"p": 7}))
        a(("force", ([[_np.int64(1), _np.int64(-1), 0, 0]], 1, set()), {}))
        a(("rank", (_np.array([[1, 2], [2, 4]]),), {}))
        a(("rank", (_np.array([[0, 0], [0, 0]]),), {}))
        a(("rank", (_np.zeros((0, 2), dtype=_np.int64),), {}))

    # ---- T0 element types --------------------------------------------------
    a(("force", ([[1, -1, 0, 0]], 1, {0.0}), {}))
    a(("force", ([[1, -1, 0, 0]], 1, {MyInt(0)}), {}))
    a(("force", ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, {Idx(0)}), {}))
    a(("force", ([[1, -1, 0, 0]], 1, "0"), {}))
    a(("force", ([[1, -1, 0, 0]], 1, range(0)), {}))
    a(("force", ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, range(1)), {}))
    a(("force", ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, {0: "a"}), {}))

    # ---- rows container types ---------------------------------------------
    a(("rank", (((1, 2), (2, 4)),), {}))
    a(("rank", ([(1, 2), [2, 4]],), {}))
    a(("rank", ({(1, 2), (2, 4)},), {}))
    a(("rank", ({(1, 2): 0, (2, 4): 0},), {}))
    a(("rank", (range(0),), {}))
    a(("rank", (0,), {}))
    a(("rank", ("",), {}))
    a(("rank", (None,), {}))
    a(("force", (((1, -1, 0, 0), (0, 0, 1, -1)), 2, set()), {}))
    a(("force", ([], 1, iter([])), {}))

    # ---- n type ------------------------------------------------------------
    a(("force", ([[1, -1, 0, 0]], 1.0, set()), {}))
    a(("force", ([[1, -1, 0, 0]], MyInt(1), set()), {}))
    a(("force", ([[1, -1, 0, 0]], Idx(1), set()), {}))
    a(("force", ([[1, -1, 0, 0]], None, set()), {}))
    a(("rank", ([[1, 2]],), {"p": 1.0}))
    a(("rank", ([[1, 2]],), {"p": MyInt(7)}))
    a(("rank", ([[1, 2]],), {"p": Idx(7)}))

    return C
