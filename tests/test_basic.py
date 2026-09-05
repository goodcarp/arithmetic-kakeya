import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from fractions import Fraction
from kakeya import score, serialise, check_X

FAIL = []
def chk(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("  " + str(extra) if extra else ""))
    if not cond: FAIL.append(name)

# ---- T1: X validity --------------------------------------------------
chk("X-validity accepts {(0,0),(1,0),(0,1)}", check_X([(0,0),(1,0),(0,1)]) == [])
chk("X-validity rejects (1,-1)", check_X([(0,0),(1,-1)]) != [])
chk("X-validity rejects missing (0,0)", check_X([(1,0),(0,1)]) != [])

# ---- T2: the trivial AK(2) object ------------------------------------
X = [(0,0),(1,0),(0,1)]
d  = []                      # k = 0: a single vertex
f  = []
T  = []
R  = [((), (1,0)), ((), (0,1))]
res = score(X, d, f, T, R, backend="exact")
chk("AK(2): forcing succeeds", res["ok"], res.get("log"))
chk("AK(2): n=1,m=0,r=2,t=0", (res["n"],res["m"],res["r"],res["t"])==(1,0,2,0), res)
chk("AK(2): score == 2", res["score"] == Fraction(2), res["score"])
print(serialise(X,d,f,T,R,res["score"]))
print()

# ---- T3: one generator is NOT enough ---------------------------------
res = score(X, d, f, [], [((), (1,0))], backend="exact")
chk("single generator fails to force", not res["ok"])

# ---- T4: two parallel generators are NOT enough -----------------------
res = score([(0,0),(1,0),(2,0)], d, f, [], [((), (1,0)), ((), (2,0))], backend="exact")
chk("two parallel generators fail", not res["ok"])

# ---- T5: an edge alone cannot bootstrap -------------------------------
# two vertices joined by one edge, no generators, T empty
X2 = [(0,0),(1,0),(0,1)]
res = score(X2, [2], [{(1,): (1,0)}], [], [], backend="exact")
chk("bare edge cannot bootstrap", not res["ok"])
chk("bare edge counts m=1,n=2", (res["m"],res["n"])==(1,2), res)

# ---- T6: seeded edge -> a 2-vertex object with score 2 ----------------
# T = {(1,)} free; edge (1)-(2) labelled (1,0); generator (0,1) at (2,)
res = score(X2, [2], [{(1,): (1,0)}], [(1,)], [((2,), (0,1))], backend="exact")
chk("seeded edge forces", res["ok"], res.get("log"))
chk("seeded edge score = (1+1)/(2-1) = 2", res["score"] == Fraction(2), res["score"])

# ---- T7: m(G) multiplicity -------------------------------------------
# d = [2,3]; f_1 has a single key (1,) -> mult d_2 = 3 edges
res = score(X2, [2,3], [{(1,): (1,0)}, {}], [], [], backend="exact")
chk("m multiplicity: f_1 bundle = d_2 = 3 edges", res["m"] == 3, res)
chk("n = 6", res["n"] == 6, res)
# f_2 keys are (e1,e2) with e2 in 1..d_2-1 = 1..2 ; mult 1
res = score(X2, [2,3], [{}, {(1,1):(1,0),(1,2):(0,1),(2,1):(1,0),(2,2):(0,1)}], [], [], backend="exact")
chk("m multiplicity: four f_2 bundles = 4 edges", res["m"] == 4, res)

# ---- T8: mod-p backend agrees with exact on the AK(2) object ----------
res_p = score(X, [], [], [], [((), (1,0)), ((), (0,1))], backend="modp")
chk("modp backend agrees on AK(2)", res_p["ok"] and res_p["score"] == Fraction(2))

print()
print("FAILURES:", FAIL if FAIL else "none")
