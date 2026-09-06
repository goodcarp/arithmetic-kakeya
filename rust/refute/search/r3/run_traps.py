"""Run every adversary trap against BOTH the pure-Python fastcore and the Rust
kernel, in the SAME process but with fastcore._INV cleared before every single
Python call (the documented p-keyed cache quirk).

usage: run_traps.py <traps.json | verified-md-extract.json>
prints one line per trap: NAME | expected | python | rust | verdict
"""
import json, sys, os, traceback

os.environ["KAKEYA_PURE_PY"] = "1"
sys.path.insert(0, "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src")
import fastcore
import fastcore_rs

PY = {"rank": fastcore._rank_py, "force": fastcore._force_py,
      "_inv": fastcore._inv, "P": fastcore.P, "set": set}
RS = {"rank": fastcore_rs.rank, "force": fastcore_rs.force,
      "_inv": None, "P": fastcore_rs.P, "set": set}


def ev(call, ns, clear):
    if clear:
        fastcore._INV.clear()
    try:
        return repr(eval(call, dict(ns)))
    except Exception as e:
        return "raises %s" % type(e).__name__


traps = json.load(open(sys.argv[1]))
npass = nfail = nskip = 0
fails = []
for t in traps:
    call = t["call"]
    exp = t["expected_repr"]
    p = ev(call, PY, True)
    if "_inv" in call:
        r = "SKIP(no _inv in rust module)"
        v = "SKIP"
        nskip += 1
    else:
        r = ev(call, RS, False)
        # normalise set repr ordering: python sets of ints repr deterministically
        if r == p == exp:
            v = "PASS"
            npass += 1
        else:
            v = "FAIL"
            nfail += 1
            fails.append((t["name"], call, exp, p, r))
    print("%-46s | exp=%-22s | py=%-22s | rs=%-22s | %s" % (t["name"], exp, p, r, v))

print()
print("PASS=%d FAIL=%d SKIP=%d TOTAL=%d" % (npass, nfail, nskip, len(traps)))
for f in fails:
    print("FAIL DETAIL:", f)
