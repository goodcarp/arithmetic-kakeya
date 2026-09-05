import sys
sys.path.insert(0, ".")
import harness
mod = harness.load_rs("shipped")
r = harness.Runner(mod, "externally-suggested")
CASES = [
    ("rank", ([[4294967290, 4294967290], [4294967290, 1]],), {"p": 4294967291}),
    ("rank", ([[2, 1], [4, 3]],), {"p": 9}),
    ("rank", ([[4, 2], [2, 1]],), {"p": 8}),
    ("force", ([[1, 0, 0, 1]], 2, [0, 0]), {"p": 2147483647}),
    ("force", ([[1, 0, 0, 1]], 2, [-1]), {"p": 2147483647}),
]
for k, a, kw in CASES:
    harness.INV.clear()
    py = (harness.PY_FORCE if k == "force" else harness.PY_RANK)(*a, **kw)
    ok = r.check(k, *a, **kw)
    print(("SAME " if ok else "DIVERGES "), k, a, kw, "->", py)
print("pow(4,6,8) =", pow(4, 6, 8), " (a zeroing pivot inverse)")
r.report()
