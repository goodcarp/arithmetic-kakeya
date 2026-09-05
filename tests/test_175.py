import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "objects"))
from fractions import Fraction
from kakeya import score, serialise
import obj_175 as O

print("=== certifying the 1.75 object (exact rational backend) ===")
res = score(O.X, O.d, O.f, O.T, O.R, backend="exact", verbose=True)
print(res["errors"] or "no structural errors")
print("n,m,r,t =", res["n"], res["m"], res["r"], res["t"])
print("forcing succeeded:", res["ok"])
print("score =", res["score"], "=", float(res["score"]))
assert res["ok"], "forcing failed"
assert res["score"] == Fraction(7, 4), res["score"]
print("\n=== same, with the local rule disabled (pure module closure) ===")
from kakeya import ConstructibleGraph, ForcingProblem
G = ConstructibleGraph(O.X, O.d, O.f)
fp = ForcingProblem(G, O.R, O.T)
ok, Tf, log = fp.run(backend="exact", use_local=False)
for l in log: print("   ", l)
assert ok
print("\n=== mod-p backend cross-check ===")
res2 = score(O.X, O.d, O.f, O.T, O.R, backend="modp")
assert res2["ok"] and res2["score"] == Fraction(7,4)
print("agrees")
print("\n=== answer in Epoch's six-line format ===")
print(serialise(O.X, O.d, O.f, O.T, O.R, res["score"]))
print("\nCERTIFIED 7/4")
