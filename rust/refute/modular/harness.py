"""Differential harness: pure-Python fastcore vs the Rust fastcore_rs.

Lens: integer arithmetic (moduli, signs, overflow, bool/int mixing).

Reference is ALWAYS fastcore._force_py / fastcore._rank_py with
fastcore._INV.clear() immediately before the call (kernel contract sec 2.1).
"""
import importlib.util
import os
import sys
import traceback

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
sys.path.insert(0, SRC)

# --- reference (pure Python) ------------------------------------------------
os.environ["KAKEYA_PURE_PY"] = "1"
import fastcore as _fc  # noqa: E402

PY_FORCE = _fc._force_py
PY_RANK = _fc._rank_py
INV = _fc._INV


HERE = os.path.dirname(os.path.abspath(__file__))
SO_DIRS = {
    "shipped": SRC,                                   # src/fastcore_rs.abi3.so
    "fresh": os.path.join(HERE, "fresh", "fastcore_rs"),
}


def load_rs(variant):
    """Import fastcore_rs from the chosen directory.

    Only one variant per process: the extension's init symbol is fixed.
    """
    d = SO_DIRS[variant]
    so = os.path.join(d, "fastcore_rs.abi3.so")
    if not os.path.exists(so):
        raise SystemExit("missing " + so)
    sys.path.insert(0, d)
    for m in list(sys.modules):
        if m == "fastcore_rs":
            del sys.modules[m]
    import fastcore_rs
    if os.path.realpath(fastcore_rs.__file__) != os.path.realpath(so):
        raise SystemExit("loaded wrong .so: " + fastcore_rs.__file__)
    return fastcore_rs


def _call(fn, args, kwargs):
    try:
        v = fn(*args, **kwargs)
        return ("ok", v)
    except BaseException as e:  # PanicException is a BaseException subclass
        return ("exc", type(e).__name__, str(e)[:160])


def norm(res, kind):
    """Canonical form so `(True, {True,0})` == `(True, {1,0})` etc."""
    if res[0] == "exc":
        return ("exc", res[1])
    v = res[1]
    if kind == "force":
        ok, T = v
        return ("ok", bool(ok), tuple(sorted(int(x) for x in T)))
    return ("ok", int(v))


def ref(kind, args, kwargs):
    INV.clear()
    return _call(PY_FORCE if kind == "force" else PY_RANK, args, kwargs)


def rs(mod, kind, args, kwargs):
    return _call(getattr(mod, kind), args, kwargs)


# Divergences the S1 contract explicitly sanctions (sec 5.4). Classified, not
# hidden: a case landing here is reported as KNOWN, everything else as NEW.
def classify(kind, args, kwargs, r_ref, r_rs):
    p = kwargs.get("p", args[3] if (kind == "force" and len(args) > 3)
                   else (args[1] if (kind == "rank" and len(args) > 1) else None))
    n = args[1] if kind == "force" else None
    rs_exc = r_rs[1] if r_rs[0] == "exc" else None
    ref_exc = r_ref[1] if r_ref[0] == "exc" else None
    if rs_exc == "OverflowError" and ref_exc is None:
        return "KNOWN-D1-entry-outside-i64"
    if rs_exc == "ValueError" and isinstance(p, int) and not isinstance(p, bool):
        if p < 0:
            return "KNOWN-D2-negative-p"
        if p >= (1 << 32):
            return "KNOWN-D3-p-ge-2^32"
    if rs_exc == "ValueError" and isinstance(n, int) and n > (1 << 20):
        return "KNOWN-D4-n-too-large"
    if rs_exc == "TypeError" and ref_exc == "TypeError":
        return None  # same type, different message: not a divergence
    if rs_exc == "TypeError" and ref_exc is None:
        return "KNOWN-D5/6-nonint-passthrough"
    return "NEW"


class Runner:
    def __init__(self, mod, label):
        self.mod = mod
        self.label = label
        self.n = 0
        self.new = []
        self.known = {}

    def check(self, kind, *args, **kwargs):
        self.n += 1
        r_ref = ref(kind, args, kwargs)
        r_rs = rs(self.mod, kind, args, kwargs)
        try:
            a, b = norm(r_ref, kind), norm(r_rs, kind)
        except Exception:
            a, b = r_ref, r_rs
        if a == b:
            return True
        cls = classify(kind, args, kwargs, r_ref, r_rs)
        if cls is None:
            return True
        if cls == "NEW":
            self.new.append((kind, args, kwargs, r_ref, r_rs))
        else:
            self.known[cls] = self.known.get(cls, 0) + 1
        return False

    def report(self):
        print(f"[{self.label}] cases={self.n}  NEW divergences={len(self.new)}  "
              f"known={self.known}")
        for kind, args, kwargs, rr, rz in self.new[:80]:
            sa = repr(args)
            if len(sa) > 400:
                sa = sa[:400] + "...<truncated>"
            print(f"  NEW {kind}(*{sa}, **{kwargs!r})")
            print(f"      python: {rr!r}")
            print(f"      rust  : {rz!r}")
        if len(self.new) > 80:
            print(f"  ... and {len(self.new)-80} more")
        return len(self.new)
