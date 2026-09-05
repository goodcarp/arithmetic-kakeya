"""Differential probe: pure-Python fastcore vs fastcore_rs, one case at a time.

Usage: /usr/bin/python3 probe.py cases.py
Each case is a dict {"id":..., "kind":"force"|"rank", "args": callable->tuple, "kwargs": callable->dict}
We use callables so a fresh generator/object is built for each side.
"""
import sys, os, traceback
sys.path.insert(0, "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src")
import fastcore
import fastcore_rs

def run(fn, mk):
    args, kwargs = mk()
    try:
        r = fn(*args, **kwargs)
        return ("ok", r)
    except BaseException as e:
        return ("raise", type(e).__name__, str(e))

def norm(res, kind):
    if res[0] != "ok":
        return res[:2]  # (raise, TypeName) -- messages differ by design
    v = res[1]
    if kind == "force":
        ok, T = v
        return ("ok", bool(ok), tuple(sorted(T, key=lambda x: (isinstance(x,float), x))), set(T))
    return ("ok", v)

def check(cid, kind, mk, note=""):
    pyfn = fastcore._force_py if kind == "force" else fastcore._rank_py
    rsfn = fastcore_rs.force if kind == "force" else fastcore_rs.rank
    fastcore._INV.clear()
    a = run(pyfn, mk)
    fastcore._INV.clear()
    b = run(rsfn, mk)
    na, nb = norm(a, kind), norm(b, kind)
    same = na == nb
    print(("SAME " if same else "DIFF ") + cid + ("  # " + note if note else ""))
    print("      py: %r" % (a,))
    print("      rs: %r" % (b,))
    return same
