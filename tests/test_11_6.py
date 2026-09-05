import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "objects"))
from fractions import Fraction
from kakeya import score, serialise, ConstructibleGraph, ForcingProblem, verify_answer
import obj_11_6 as O

print("=== certifying the 11/6 object (sums-differences record) ===")
res = score(O.X, O.d, O.f, O.T, O.R, backend="exact", verbose=True)
print(res["errors"] or "no structural errors")
print("n,m,r,t =", res["n"], res["m"], res["r"], res["t"])
print("forcing succeeded:", res["ok"], " score =", res["score"], "=", float(res["score"]))
assert res["ok"] and res["score"] == Fraction(11, 6), res
G = ConstructibleGraph(O.X, O.d, O.f)
verts = G.vertices()
names = {(1,1):"g4", (2,1):"g3", (1,2):"g1", (2,2):"g2", (1,3):"g6", (2,3):"g5"}
fp = ForcingProblem(G, O.R, O.T)
ok, Tf, log = fp.run(backend="exact", use_local=False)
print("forcing order:", end=" ")
import re
order = [names[tuple(eval(m.group(1)))] for l in log if (m := re.match(r"forced (\(.*?\))", l))]
print(" -> ".join(order))
assert order[0] == "g5", "Katz-Tao's identity forces g5 first"
txt = serialise(O.X, O.d, O.f, O.T, O.R, res["score"])
print()
print(txt)
assert verify_answer(txt, bound="11/6")["within_bound"]
print()
print("CERTIFIED 11/6, and the first vertex forced is g5 -- exactly Katz-Tao's identity")
