from probe import check
from fractions import Fraction

C = lambda *a, **k: (lambda: (a, k))
ok = []
def T(cid, kind, mk, note=""):
    ok.append((cid, check(cid, kind, mk, note)))

# --- p handling ------------------------------------------------------------
T("p0_rank",        "rank",  C([[1,2],[3,4]], 0))
T("p0_force",       "force", C([[1,-1,0,0]], 2, set(), 0))
T("p0_norows",      "force", C([], 2, set(), 0))
T("p0_emptyrows_rank","rank",C([[],[]], 0))
T("p0_row0empty",   "rank",  C([[],[1,2]], 0))
T("pneg_rank",      "rank",  C([[1,0],[0,1]], -5))
T("pneg_force",     "force", C([[1,-1,0,0]], 2, set(), -5))
T("pneg_norows",    "force", C([], 2, set(), -5))
T("pneg_emptyrows_rank","rank",C([[],[]], -5))
T("pbig_rank",      "rank",  C([[1,0],[0,1]], (1<<32)+1))
T("pbig_force",     "force", C([[1,-1,0,0],[0,0,1,-1]], 2, set(), (1<<32)+1))
T("pbig_row0empty_rank","rank",C([[],[1,2]], (1<<32)+1), "py: w=0 -> 0")
T("pbig_norows",    "force", C([], 2, set(), (1<<32)+1))
T("p1_rank",        "rank",  C([[1,2],[3,4]], 1))
T("p1_force",       "force", C([[1,-1,0,0],[0,0,1,-1]], 2, set(), 1))
T("p2_force",       "force", C([[1,1,0,0],[0,0,1,1]], 2, set(), 2))
T("p2_forceP",      "force", C([[1,1,0,0],[0,0,1,1]], 2, set()))
T("p4_composite",   "force", C([[3,1,0,0],[1,3,0,0]], 1, set(), 4))
T("p6_composite",   "rank",  C([[2,3],[3,2]], 6))
T("p9_composite",   "rank",  C([[3,1],[1,3]], 9))
T("p3_force",       "force", C([[1,2,0,0],[0,0,1,2]], 2, set(), 3))

# --- ordering of p-validation vs IndexError --------------------------------
T("ord_short_p0",   "force", C([[]], 1, set(), 0), "py IndexError before %0")
T("ord_short_p0b",  "force", C([[7]], 1, set(), 0), "py reads r[0]%0 -> ZeroDiv")
T("ord_short_pbig", "force", C([[1,2,3]], 2, set(), (1<<32)+1), "py IndexError at j=1")
T("ord_u0_p0",      "force", C([[9,9,7]], 2, {0}, 0), "U=[1]; r[2] ok -> %0")
T("ord_u0_p0b",     "force", C([[9,9]], 2, {0}, 0), "U=[1]; r[2] IndexError")

# --- ragged / empty rows ---------------------------------------------------
T("rank_ragged_short_later","rank", C([[1,2,3],[1,2]]))
T("rank_ragged_long_later", "rank", C([[1,2],[1,2,3]]))
T("rank_trunc_chain","rank", C([[1,0,0],[1,1,1,1],[0,0,1,1]]))
T("rank_trunc_chain2","rank",C([[1,0,0,0],[1,1],[0,1,1,1]]))
T("rank_all_empty", "rank",  C([[],[],[]]))
T("rank_row0_empty","rank",  C([[],[1,2,3]]))
T("rank_empty",     "rank",  C([]))
T("rank_empty_tuple","rank", C(()))
T("rank_dupe_rows", "rank",  C([[1,2,3]]*40))
T("force_ragged",   "force", C([[1,-1,0,0],[0,0,1]], 2, set()))
T("force_longrow",  "force", C([[1,-1,9,9]], 1, set()))
T("force_norows",   "force", C([], 2, set()))
T("force_zerorows", "force", C([[0,0,0,0],[0,0,0,0]], 2, set()))
T("force_modzero",  "force", C([[2147483647,2147483647,0,0],[0,0,1,-1]], 2, set()))
T("force_modzero2", "force", C([[2147483648,-2147483646]], 1, set()))

# --- T0 semantics ----------------------------------------------------------
T("t0_out_of_range","force", C([], 2, {0,5}))
T("t0_oor2",        "force", C([[1,-1,0,0]], 2, {5}))
T("t0_oor3",        "force", C([[1,-1,0,0,0,0],[0,0,1,-1,0,0],[0,0,0,0,1,-1]], 3, {9}))
T("t0_neg",         "force", C([[1,-1,0,0,0,0],[0,0,1,-1,0,0],[0,0,0,0,1,-1]], 3, {-1,-2}))
T("t0_dup_list",    "force", C([[1,-1,0,0]], 2, [0,0,0]))
T("t0_frozenset",   "force", C([[1,-1,0,0],[0,0,1,-1]], 2, frozenset()))
T("t0_bool",        "force", C([[1,-1,0,0],[0,0,1,-1]], 2, {True}))
T("t0_tuple",       "force", C([[1,-1,0,0],[0,0,1,-1]], 2, (0,)))
T("n_zero",         "force", C([[1,-1]], 0, {7}))
T("n_neg",          "force", C([[1,-1]], -3, set()))
T("n_bool",         "force", C([[1,-1]], True, set()))
T("n_covered",      "force", C([[9,9,9,9]], 2, {0,1}))
#T("n_maxn",         "force", C([], (1<<20)+1, set()), "MAX_N guard")
#T("n_maxn_exact",   "force", C([], (1<<20), set()))

# --- iterators / containers ------------------------------------------------
T("rank_gen_empty", "rank",  lambda: ((iter([]),), {}), "py: len(B[0]) IndexError")
T("rank_gen",       "rank",  lambda: ((iter([[1,0],[0,1]]),), {}))
T("force_gen_rows_1round","force", lambda: ((iter([[1,-1,0,0],[0,0,1,-1]]),), {}) if False else ((iter([[1,-1,0,0],[0,0,1,-1]]), 2, set()), {}))
T("force_gen_t0",   "force", lambda: (([[1,-1,0,0],[0,0,1,-1]], 2, iter([0])), {}))
T("rows_tuple_tuple","rank", C(((1,0),(0,1))))
T("rows_list_tuple","force", C([(1,-1,0,0),(0,0,1,-1)], 2, set()))
T("rows_bool_entries","rank",C([[True,False],[False,True]]))
T("rows_set_of_tuples","rank",lambda: ((frozenset([(1,0,0),(0,1,0),(0,0,1)]),), {}))

# --- entry magnitudes ------------------------------------------------------
T("entry_2p63",     "rank",  C([[1<<63,1],[1,0]]))
T("entry_neg2p63",  "rank",  C([[-(1<<63),1],[1,0]]))
T("entry_2p64neg",  "rank",  C([[-(1<<64),1],[1,0]]))
T("entry_float",    "rank",  C([[1.0,0],[0,1]]))
T("entry_frac",     "rank",  C([[Fraction(1),0],[0,1]]))
T("entry_none",     "rank",  C([[None,0],[0,1]]))
T("entry_str",      "rank",  C([["a",0],[0,1]]))
T("t0_float",       "force", C([[1,-1,0,0]], 2, {0.0}))

# --- aliasing --------------------------------------------------------------
def alias_case():
    s = {0}
    r = None
    return s
print("--- aliasing checks ---")
import fastcore, fastcore_rs
for name, fn in (("py", fastcore._force_py), ("rs", fastcore_rs.force)):
    fastcore._INV.clear()
    s = {0}
    okv, T2 = fn([[1,-1,0,0],[0,0,1,-1]], 2, s)
    print("  %s: T0 after=%r  identity(T0 is result)=%r  type=%r  ok_type=%r" % (name, s, T2 is s, type(T2).__name__, type(okv).__name__))

print()
n_diff = sum(1 for _, v in ok if not v)
print("TOTAL %d cases, %d DIFF" % (len(ok), n_diff))
