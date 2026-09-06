"""Run every recorded trap against the CURRENT fastcore binding.

Each trap is evaluated in isolation-ish: fastcore._INV is cleared before every
call so the documented pure-Python cache quirk never fires.
Usage: python3 run_traps.py            (Rust binding, KAKEYA_PURE_PY unset)
       KAKEYA_PURE_PY=1 python3 ...    (pure Python)
"""
import json, os, sys, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import fastcore

MODE = "PURE_PY" if os.environ.get("KAKEYA_PURE_PY") == "1" else "RUST"

def norm(v):
    # sets have unstable repr order; canonicalise
    if isinstance(v, tuple) and len(v) == 2 and isinstance(v[1], (set, frozenset)):
        return "(%s, %s)" % (repr(v[0]), "{" + ", ".join(repr(x) for x in sorted(v[1], key=lambda z:(str(type(z)),z))) + "}" if v[1] else "set()")
    if isinstance(v, (set, frozenset)):
        return "{" + ", ".join(repr(x) for x in sorted(v)) + "}" if v else "set()"
    return repr(v)

def canon(s):
    """canonicalise an expected_repr string that may contain a set literal"""
    s = s.strip()
    try:
        val = eval(s, {"set": set, "frozenset": frozenset})
    except Exception:
        return s
    return norm(val)

env = {"force": None, "rank": None, "_inv": None, "P": fastcore.P,
       "fastcore": fastcore, "set": set, "frozenset": frozenset, "range": range,
       "list": list, "tuple": tuple, "len": len, "iter": iter}

traps = []
V = os.path.join(ROOT, "adversary-fable", "traps.json")
traps += [(t["name"], t["call"], t["expected_repr"], t.get("note","")) for t in json.load(open(V))]

# the 16 from VERIFIED.md, transcribed
ext = [
 ("x01","rank([[-1,2]], p=5)","1"),
 ("x02","rank([[2,0]], p=4)","1"),
 ("x03","_inv(0,5)","0"),
 ("x04","rank([[1<<62, 1]], p=5)","1"),
 ("x05","force([[7,7]],1,[],p=7)","(False, set())"),
 ("x06","force([[0,0,1,-1]],2,[])","(False, {1})"),
 ("x07","force([],1,[99])","(True, {99})"),
 ("x08","force([[1,-1]],1,[2,2])","(True, {2})"),
 ("x09","force([],2,[0,0,7])","(True, {0, 7})"),
 ("x10","rank([[2147483647]])","0"),
 ("x10b","rank([[2147483648]])","1"),
 ("x11","rank([[]])","0"),
 ("x12","rank([[1,2],[3]])","IndexError"),
 ("x13","force([[1]],1,[])","IndexError"),
 ("x14","rank([[2,1],[0,2]], p=4)","2"),
 ("x15","force([[2,2]],1,[],p=4)","(False, set())"),
 ("x16","force([[1,-1]],1,set())","(True, {0})"),
]
traps += [(n,c,e,"VERIFIED.md") for n,c,e in ext]

npass = nfail = nskip = 0
fails = []
for name, call, exp, note in traps:
    fastcore._INV.clear()
    env["force"] = fastcore.force
    env["rank"] = fastcore.rank
    env["_inv"] = fastcore._inv
    if "_inv(" in call and MODE == "RUST":
        # _inv is Python-only; the Rust module exposes no such symbol
        pass
    try:
        got = norm(eval(call, dict(env)))
    except Exception as e:
        got = type(e).__name__
    want = canon(exp)
    # allow bare exception-name expectations
    if want == exp.strip() and exp.strip().endswith("Error"):
        want = exp.strip()
    if got == want:
        npass += 1
    else:
        nfail += 1
        fails.append((name, call, want, got, note))
print("%s: pass=%d fail=%d of %d" % (MODE, npass, nfail, len(traps)))
for f in fails:
    print("  FAIL %-34s %s\n        want=%s\n        got =%s\n        note=%s" % f)
