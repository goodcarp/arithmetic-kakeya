"""Boundary/coercion differential: reconstructed original fastcore vs fastcore_rs.

Oracle = orig_fastcore.py, which is bytes[0:2976] of src/fastcore.py, i.e. the
file with the appended "Rust drop-in" block stripped.  _INV is cleared before
every reference call (kernel contract sec 2.1).

Each case is a (label, callable-name, args) triple.  We record for each side
either ("val", repr) or ("exc", ExceptionTypeName).  A case is a DIVERGENCE when
the two differ.
"""
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "..", "..", "src"))
sys.path.insert(0, HERE)
sys.path.insert(0, SRC)

import orig_fastcore as PY  # noqa: E402
import fastcore_rs as RS  # noqa: E402

try:
    import numpy as np
except ImportError:
    np = None


class Idx:
    def __init__(self, v):
        self.v = v

    def __index__(self):
        return self.v

    def __repr__(self):
        return "Idx(%r)" % self.v


class BadIter:
    def __iter__(self):
        raise RuntimeError("boom")


def norm(v):
    """Normalise a result so bool/int and set-content differences are visible."""
    if isinstance(v, tuple) and len(v) == 2:
        ok, T = v
        return ("val", "(%s:%r, %s:%s)" % (type(ok).__name__, ok, type(T).__name__,
                                           sorted(T, key=lambda z: (str(type(z)), z))))
    return ("val", "%s:%r" % (type(v).__name__, v))


import resource
import signal

# Safety net: one case (n=2**63) would otherwise eat the machine.
try:
    _soft, _hard = resource.getrlimit(resource.RLIMIT_AS)
    _cap = 2 << 30
    if _hard != resource.RLIM_INFINITY:
        _cap = min(_cap, _hard)
    resource.setrlimit(resource.RLIMIT_AS, (_cap, _hard))
except (ValueError, OSError):
    pass


class _Hang(Exception):
    pass


def _alarm(sig, frm):
    raise _Hang()


signal.signal(signal.SIGALRM, _alarm)


def run(fn, args, kwargs, pure):
    try:
        if pure:
            PY._INV.clear()
        signal.setitimer(signal.ITIMER_REAL, 3.0)
        try:
            r = fn(*args, **kwargs)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
        return norm(r)
    except _Hang:
        return ("hang/OOM", ">3s or >2GB")
    except BaseException as e:  # noqa: BLE001
        return ("exc", type(e).__name__)


CASES = []


def C(label, name, args, kwargs=None):
    """args/kwargs are given as literals; we re-evaluate them per side so that
    one-shot iterables are fresh for both the Python and the Rust call."""
    import copy as _copy
    src = (args, kwargs or {})

    def mk(_src=src):
        return _src

    CASES.append((label, name, mk))


def CL(label, name, thunk):
    """thunk() -> (args, kwargs); use for one-shot iterables."""
    CASES.append((label, name, thunk))


P = 2147483647

# ---------------------------------------------------------------- bools
C("rank bool entries", "rank", ([[True, False], [False, True]],))
C("force bool entries", "force", ([[True, -1, 0, 0]], 1, set()))
C("force n=True", "force", ([[1, -1, 0, 0]], True, set()))
C("force T0={True}", "force", ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, {True}))
C("rank p=True", "rank", ([[3, 1], [1, 3]],), {"p": True})

# ---------------------------------------------------------------- floats
C("rank float non-pivot col", "rank", ([[1, 2.5]],))
C("rank float pivot", "rank", ([[2.0, 0], [0, 1]],))
C("rank int-valued float non-pivot", "rank", ([[1, 2.0]],))
C("rank 2 rows float trailing", "rank", ([[1, 0, 3.5], [0, 1, 0]],))
C("force float entry, zero row", "force", ([[0.0, 0.0]], 1, set()))
C("force float n=0.0", "force", ([], 0.0, set()))
C("force float n=-1.0", "force", ([], -1.0, set()))
C("force float n=0.5", "force", ([], 0.5, set()))
C("force float p=7.0 no pivot", "force", ([[0, 0]], 1, set(), 7.0))
C("rank float p=7.0 all-zero", "rank", ([[0, 0]],), {"p": 7.0})
C("force T0={0.0}", "force", ([[1, -1, 0, 0]], 1, {0.0}))

# ---------------------------------------------------------------- __index__
C("rank entry __index__", "rank", ([[Idx(1), Idx(0)], [Idx(0), Idx(1)]],))
C("force n=Idx(2)", "force", ([[1, -1, 0, 0], [0, 0, 1, -1]], Idx(2), set()))
C("force T0={Idx(0)}", "force", ([[1, -1, 0, 0]], 1, {Idx(0)}))
C("rank p=Idx(7)", "rank", ([[3, 1], [1, 3]],), {"p": Idx(7)})

# ---------------------------------------------------------------- big ints
C("rank entry 2**63", "rank", ([[2 ** 63, 1], [1, 0]],))
C("rank entry -2**63", "rank", ([[-2 ** 63, 1], [1, 0]],))
C("rank entry 2**63-1", "rank", ([[2 ** 63 - 1, 1], [1, 0]],))
C("rank entry 10**30", "rank", ([[10 ** 30, 1], [1, 0]],))
C("force entry 2**64", "force", ([[2 ** 64, -1, 0, 0]], 1, set()))
C("force n=2**63", "force", ([], 2 ** 63, set()))
C("force n=2**21 empty rows", "force", ([], 2 ** 21, set()))
C("force p=2**32", "force", ([[1, -1]], 1, set(), 2 ** 32))
C("force p=2**63", "force", ([[1, -1]], 1, set(), 2 ** 63))
C("rank p=2**40", "rank", ([[3, 1], [1, 3]],), {"p": 2 ** 40})
C("force T0 huge", "force", ([[1, -1, 0, 0]], 1, {2 ** 63}))

# ---------------------------------------------------------------- p sign/zero
C("rank p=-5", "rank", ([[1, 0], [0, 1]],), {"p": -5})
C("rank p=0", "rank", ([[1, 0]],), {"p": 0})
C("rank p=1", "rank", ([[1, 0], [0, 1]],), {"p": 1})
C("force p=1", "force", ([[1, -1, 0, 0]], 1, set(), 1))
C("force p=2", "force", ([[1, 1, 0, 0], [0, 0, 1, 1]], 2, set(), 2))
C("force p=4 composite", "force", ([[3, 1, 0, 0], [1, 3, 0, 0]], 1, set(), 4))

# ---------------------------------------------------------------- containers
CL("rank generator rows", "rank", lambda: (((r for r in []),), {}))
CL("rank iter([]) rows", "rank", lambda: ((iter([]),), {}))
CL("rank generator nonempty", "rank", lambda: (((r for r in [[1, 0], [0, 1]]),), {}))
CL("force generator rows", "force", lambda: (((r for r in [[1, -1, 0, 0], [0, 0, 1, -1]]), 2, set()), {}))
C("rank tuple of tuples", "rank", (((1, 0), (0, 1)),))
C("rank rows=[[]]", "rank", ([[]],))
C("rank rows=[[],[1,2]]", "rank", ([[], [1, 2]],))
C("rank rows=()", "rank", ((),))
C("rank rows=''", "rank", ("",))
C("rank rows='ab'", "rank", ("ab",))
C("rank rows=0", "rank", (0,))
C("rank rows=None", "rank", (None,))
C("force rows=None", "force", (None, 1, set()))
CL("force T0=generator", "force", lambda: (([[1, -1, 0, 0]], 1, (x for x in [])), {}))
C("force T0=BadIter", "force", ([[1, -1, 0, 0]], 1, BadIter()))
C("force T0=frozenset", "force", ([[1, -1, 0, 0]], 1, frozenset()))
C("force T0=list dup", "force", ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, [0, 0, 0]))
C("force T0=None", "force", ([[1, -1, 0, 0]], 1, None))
C("force T0=int", "force", ([[1, -1, 0, 0]], 1, 3))

# ---------------------------------------------------------------- strings/None
C("rank str entry", "rank", ([["a", 1]],))
C("rank None entry", "rank", ([[None, 1]],))
C("force str entry", "force", ([["a", "b"]], 1, set()))
C("rank Fraction-ish entry", "rank", ([[complex(1, 0), 1]],))

# ---------------------------------------------------------------- ragged
C("rank ragged short", "rank", ([[1, 0, 0], [0, 1]],))
C("rank ragged long", "rank", ([[1, 0], [0, 1, 5]],))
C("force short row", "force", ([[1, -1]], 2, set()))
C("force long row", "force", ([[1, -1, 9, 9]], 1, set()))

# ---------------------------------------------------------------- out-of-range T0
C("force T0 oor", "force", ([], 2, {0, 5}))
C("force T0 oor 2", "force", ([[1, -1, 0, 0]], 2, {5}))
C("force T0 negative", "force",
  ([[1, -1, 0, 0, 0, 0], [0, 0, 1, -1, 0, 0], [0, 0, 0, 0, 1, -1]], 3, {-1, -2}))
C("force n=0", "force", ([], 0, set()))
C("force n=-1", "force", ([], -1, set()))

# ---------------------------------------------------------------- numpy
if np is not None:
    C("rank np.int64 entries", "rank",
      ([[np.int64(1), np.int64(0)], [np.int64(0), np.int64(1)]],))
    C("rank np.int32 entries", "rank",
      ([[np.int32(3), np.int32(1)], [np.int32(1), np.int32(3)]],))
    C("rank np.array rows", "rank", (np.array([[1, 0], [0, 1]]),))
    C("rank np.array 1 row", "rank", (np.array([[1, 0]]),))
    C("rank list of np arrays", "rank", ([np.array([1, 0]), np.array([0, 1])],))
    C("force np.int64 entries", "force",
      ([[np.int64(1), np.int64(-1), np.int64(0), np.int64(0)]], 1, set()))
    C("force n=np.int64(2)", "force",
      ([[1, -1, 0, 0], [0, 0, 1, -1]], np.int64(2), set()))
    C("force T0={np.int64(0)}", "force", ([[1, -1, 0, 0]], 1, {np.int64(0)}))
    C("force p=np.int64(7)", "force", ([[3, 1, 0, 0]], 1, set(), np.int64(7)))
    C("rank np.float64 entry", "rank", ([[np.float64(1.0), 0]],))
    C("rank np.bool_ entries", "rank", ([[np.bool_(True), np.bool_(False)]],))
    C("force np.array row", "force", ([np.array([1, -1, 0, 0])], 1, set()))
    C("rank np.uint64 big", "rank", ([[np.uint64(2 ** 63 + 5), 1], [1, 0]],))


def main():
    div = []
    same = 0
    for label, name, mk in CASES:
        pyf = getattr(PY, name)
        rsf = getattr(RS, name)
        args, kwargs = mk()
        a = run(pyf, args, kwargs, True)
        args, kwargs = mk()
        b = run(rsf, args, kwargs, False)
        if a == b:
            same += 1
        else:
            div.append((label, name, a, b))
    print("cases=%d  agree=%d  diverge=%d" % (len(CASES), same, len(div)))
    for label, name, a, b in div:
        print("DIVERGE  %-32s %-6s py=%-46s rs=%s" % (label, name, "%s %s" % a, "%s %s" % b))
    return div


if __name__ == "__main__":
    d = main()
    sys.exit(1 if d else 0)
