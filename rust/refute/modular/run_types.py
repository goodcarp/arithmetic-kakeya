import sys
sys.path.insert(0, ".")
import harness, cases_types

variant = sys.argv[1] if len(sys.argv) > 1 else "shipped"
mod = harness.load_rs(variant)
r = harness.Runner(mod, variant + "/types")
for kind, args, kwargs in cases_types.cases():
    r.check(kind, *args, **kwargs)
r.report()

# --- input mutation / aliasing (contract sec 5.2) --------------------------
import copy
print("--- n outside i64 (reference intractable, Rust only) ---")
for nn in (1 << 64, -(1 << 64), (1 << 63), (1 << 63) - 1):
    try:
        v = mod.force([], nn, {0})
        print(f"  rust force([], {nn}, {{0}}) -> {v[0]} {sorted(v[1])}")
    except BaseException as e:
        print(f"  rust force([], {nn}, {{0}}) -> {type(e).__name__}: {e}")
print("--- mutation checks ---")
rows = [[1, -1, 0, 0], [0, 0, 1, -1]]
snap = copy.deepcopy(rows)
T0 = {0}
tsnap = set(T0)
ok, T2 = mod.force(rows, 2, T0)
print("rows unchanged:", rows == snap, "| T0 unchanged:", T0 == tsnap,
      "| fresh object:", T2 is not T0, "| result:", ok, sorted(T2))
T2.add(99)
print("mutating result leaves T0 alone:", T0 == tsnap)
ok2, T3 = mod.force(rows, 2, T2)
print("second call independent:", sorted(T2), "->", ok2, sorted(T3), "T3 is not T2:", T3 is not T2)
rr = [[1, 2, 3], [1, 2]]
rsnap = copy.deepcopy(rr)
try:
    mod.rank(rr)
except BaseException as e:
    print("rank ragged:", type(e).__name__)
print("rank did not mutate rows:", rr == rsnap)
rr2 = [[1, 1], [1, 0, 5]]
r2snap = copy.deepcopy(rr2)
print("rank truncating case:", mod.rank(rr2), harness.PY_RANK(rr2), "rows unchanged:", rr2 == r2snap)
