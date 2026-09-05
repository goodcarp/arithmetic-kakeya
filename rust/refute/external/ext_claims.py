"""Every concrete divergence claim made by the external reviewers, tested verbatim."""
from probe import check
C = lambda *a, **k: (lambda: (a, k))
res = []
def T(cid, kind, mk, note=""):
    res.append((cid, check(cid, kind, mk, note)))

# ---- antigravity-cli claims (A1..A11) -------------------------------------
T("A1_gen_rows_force","force", lambda: ((iter([[1,2147483646,0,0],[0,0,1,2147483646]]), 2, []), {}),
  "claim py (False,{0}) vs rs (True,{0,1})")
T("A2_gen_empty_rank","rank",  lambda: ((iter([]),), {}), "claim py IndexError vs rs 0")
T("A3_bigint_rank",   "rank",  C([[1<<64]]),              "claim py 1 vs rs OverflowError")
T("A4_bigint_T0",     "force", C([], 1, [1<<64]),         "claim py (True,{2**64}) vs rs OverflowError")
T("A5_pbig_rank",     "rank",  C([[1]], 1<<32),           "claim py 1 vs rs ValueError")
T("A6_pbig_zerorow",  "force", C([[0,0]], 1, [], 1<<32),  "claim py (False,set()) vs rs ValueError")
T("A7_str_T0",        "force", C([], 1, ["label"]),       "claim py (True,{'label'}) vs rs TypeError")
T("A8_float_zero_rank","rank", C([[0.0]]),                "claim py 0 vs rs TypeError")
T("A9_pneg_zerorow_rank","rank",C([[0]], -3),             "claim py 0 vs rs ValueError")
T("A10_pneg_zerorow_force","force",C([[0,0]], 1, [], -3), "claim py (False,set()) vs rs ValueError")
T("A11_maxn",         "force", lambda: (([], 1048577, range(1048577)), {}), "claim py True vs rs ValueError")

print()
print("TOTAL %d claims, %d confirmed divergent, %d NOT divergent" %
      (len(res), sum(1 for _,v in res if not v), sum(1 for _,v in res if v)))
