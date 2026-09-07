"""Re-run every VERIFIED.md row and every traps.json entry against the CURRENT
pure-Python fastcore (KAKEYA_PURE_PY=1), clearing _INV before each call.
Record-lens check: do the documented Python results still hold on this tree?"""
import sys, os, json
SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
sys.path.insert(0, SRC)
import fastcore
assert fastcore.force is fastcore._force_py, "NOT pure python! set KAKEYA_PURE_PY=1"
force, rank, _inv, P = fastcore._force_py, fastcore._rank_py, fastcore._inv, fastcore.P

# --- VERIFIED.md, 16 rows, transcribed by hand from the table ---
V = [
 (1,  "rank([[-1,2]], p=5)",            lambda: rank([[-1,2]], 5),            "1"),
 (2,  "rank([[2,0]], p=4)",             lambda: rank([[2,0]], 4),             "1"),
 (3,  "_inv(0,5)",                      lambda: _inv(0,5),                    "0"),
 (4,  "rank([[1<<62, 1]], p=5)",        lambda: rank([[1<<62,1]], 5),         "1"),
 (5,  "force([[7,7]],1,[],p=7)",        lambda: force([[7,7]],1,[],7),        "(False, set())"),
 (6,  "force([[0,0,1,-1]],2,[])",       lambda: force([[0,0,1,-1]],2,[]),     "(False, {1})"),
 (7,  "force([],1,[99])",               lambda: force([],1,[99]),             "(True, {99})"),
 (8,  "force([[1,-1]],1,[2,2])",        lambda: force([[1,-1]],1,[2,2]),      "(True, {2})"),
 (9,  "force([],2,[0,0,7])",            lambda: force([],2,[0,0,7]),          "(True, {0, 7})"),
 (10, "rank([[2147483647]])",           lambda: rank([[2147483647]]),         "0"),
 (10.5,"rank([[2147483648]])",          lambda: rank([[2147483648]]),         "1"),
 (11, "rank([[]])",                     lambda: rank([[]]),                   "0"),
 (12, "rank([[1,2],[3]])",              lambda: rank([[1,2],[3]]),            "raises IndexError"),
 (13, "force([[1]],1,[])",              lambda: force([[1]],1,[]),            "raises IndexError"),
 (14, "rank([[2,1],[0,2]], p=4)",       lambda: rank([[2,1],[0,2]], 4),       "2"),
 (15, "force([[2,2]],1,[],p=4)",        lambda: force([[2,2]],1,[],4),        "(False, set())"),
]
def run(f):
    fastcore._INV.clear()
    try:
        return repr(f())
    except Exception as e:
        return "raises " + type(e).__name__
bad = 0
for num, desc, f, exp in V:
    got = run(f)
    ok = (got == exp)
    if not ok: bad += 1; print(f"VERIFIED #{num} MISMATCH  {desc}\n   doc={exp!r}\n   got={got!r}")
# row 16 separately: input set not mutated
fastcore._INV.clear()
s = set()
r16 = force([[1,-1]],1,s)
ok16 = (repr(r16) == "(True, {0})" and s == set() and r16[1] is not s)
if not ok16: bad += 1; print("VERIFIED #16 MISMATCH", r16, s)
print(f"VERIFIED.md rows checked: {len(V)+1} call-forms (16 numbered rows), mismatches={bad}")

# --- traps.json ---
T = json.load(open("/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/adversary-fable/traps.json"))
env = {"force": force, "rank": rank, "_inv": _inv, "P": P, "fastcore": fastcore}
nb = 0; nskip = 0
for e in T:
    fastcore._INV.clear()
    if e.get("setup"):
        try: exec(e["setup"], env)
        except Exception: pass
    try:
        got = repr(eval(e["call"], env))
    except Exception as ex:
        got = "raises " + type(ex).__name__
    if got != e["expected_repr"]:
        nb += 1
        print(f"TRAP MISMATCH {e['name']}: call={e['call']}\n   expected={e['expected_repr']!r}\n   got     ={got!r}")
print(f"traps.json entries: {len(T)}, mismatches vs current pure-Python fastcore: {nb}")
