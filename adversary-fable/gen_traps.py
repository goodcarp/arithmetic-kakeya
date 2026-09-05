#!/usr/bin/env python3
"""Generate traps.json: each trap is evaluated against K/src/fastcore.py in a
fresh module state (fastcore._INV cleared before every call).  Run with
/usr/bin/python3.  Output is the exact repr of the result, or
'raises <ExcName>' when the call raises."""
import os, sys, json, importlib
os.environ["KAKEYA_PURE_PY"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import fastcore

force = getattr(fastcore, "_force_py", fastcore.force)
rank = getattr(fastcore, "_rank_py", fastcore.rank)
_inv = fastcore._inv
P = fastcore.P

TRAPS = []
def trap(name, call, note="", setup=None):
    TRAPS.append((name, call, note, setup))

# ---- the 16 already verified in adversary-external/VERIFIED.md ----
trap("v01_negative_entry_floored_mod", "rank([[-1,2]], p=5)", "Python % floors; Rust % keeps sign -> use rem_euclid")
trap("v02_nonprime_p_pivot_zeroed_rank_still_counts", "rank([[2,0]], p=4)", "pow(2,2,4)==0 zeroes pivot row, rk still increments")
trap("v03_inv_of_zero_is_zero", "_inv(0,5)", "pow(0,p-2,p)==0, no error")
trap("v04_entry_2pow62_reduced_on_load", "rank([[1<<62, 1]], p=5)", "bigint entries reduced before use")
trap("v05_multiples_of_p_are_zero_rows", "force([[7,7]],1,[],p=7)", "zero rows dropped -> no found vertex")
trap("v06_partial_T_on_failure_ascending_scan", "force([[0,0,1,-1]],2,[])", "found scan ascending j in U; partial T returned on failure")
trap("v07_T0_len_short_circuit_out_of_range", "force([],1,[99])", "len(set(T0))>=n short-circuits; out-of-range index kept")
trap("v08_T0_duplicates_collapse", "force([[1,-1]],1,[2,2])", "set(T0)")
trap("v09_T0_duplicates_collapse_n2", "force([],2,[0,0,7])", "set(T0)")
trap("v10_entry_equal_P_is_zero", "rank([[2147483647]])", "P % P == 0")
trap("v10b_entry_P_plus_1_is_one", "rank([[2147483648]])", "")
trap("v11_empty_row_rank_zero", "rank([[]])", "w=0, loop never runs")
trap("v12_ragged_rows_raise", "rank([[1,2],[3]])", "IndexError on short second row")
trap("v13_short_row_force_raises", "force([[1]],1,[])", "r[2*j+1] out of range")
trap("v14_nonprime_p_two_pivots", "rank([[2,1],[0,2]], p=4)", "")
trap("v15_nonprime_p_force_false", "force([[2,2]],1,[],p=4)", "")
trap("v16_input_set_not_mutated", "(lambda s: (force([[1,-1]],1,s), s))(set())", "returned set fresh, input untouched")

# ---- new traps (Fable, 2026-09-04) ----
# A. modular arithmetic / sign / overflow
trap("a01_negative_entry_force_found", "force([[-1, 1]],1,[])", "row (-1,1) ~ (p-1,1); Rust % would keep -1")
trap("a02_negative_entry_force_notfound", "force([[-1, -1]],1,[])", "(-1,-1)~(p-1,p-1) is NOT a multiple of (1,-1)")
trap("a03_entries_above_p_force", "force([[P+1, 2*P-1]],1,[])", "reduced on load: (1, P-1)")
trap("a04_p_minus_1_squared_products", "rank([[P-1,P-1],[P-1,1]])", "fac*b ~ 2^62, a-fac*b negative ~ -2^62: needs floored/rem_euclid or reduce first")
trap("a05_p_minus_1_products_force", "force([[P-1,1,P-1,1],[1,P-1,1,2]],2,[])", "same, in force")
trap("a06_p_minus_1_products_force2", "force([[P-1,1,P-1,2],[P-2,P-3,P-1,1]],2,[])", "")
trap("a07_2pow62_minus_1_is_zero_mod_P", "rank([[(1<<62)-1]])", "2^31 = 1 mod P so 2^62-1 = 0 mod P; entry is 4611686018427387903")
trap("a08_2pow62_is_one_mod_P", "rank([[1<<62]])", "")
trap("a09_neg_2pow62_plus_1_is_zero", "rank([[-(1<<62)+1]])", "-(2^62)+1 = -1+1 = 0 mod P")
trap("a10_neg_2pow62_is_P_minus_1", "rank([[-(1<<62)]])", "")
trap("a11_entry_2pow70_beyond_i64", "rank([[1<<70]])", "Python bigint; i64 extraction would overflow (2^70 = 2^8 = 256 mod P)")
trap("a12_entry_2pow70_minus_256_zero", "rank([[(1<<70)-256]])", "")
trap("a13_p_above_2pow32_needs_u128", "rank([[4294967310,4294967310],[4294967310,1]], p=4294967311)", "p=2^32+15 (prime); (p-1)^2 > 2^64")
trap("a14_mersenne61_p_needs_u128", "force([[(1<<61)-2, 1, 5, 7],[3, (1<<61)-4, 11, 13]],2,[], p=(1<<61)-1)", "p=2^61-1: products ~2^122")
trap("a15_mersenne61_rank", "rank([[(1<<63)-1, 1<<63],[3,5]], p=(1<<61)-1)", "entries above p and above i64")
trap("a16_p2_inv_of_zero_is_one", "_inv(0,2)", "pow(0,0,2)==1; never reached by rank/force since pivots are nonzero")
trap("a17_p2_rank", "rank([[3,1],[1,3],[2,4]],p=2)", "")
trap("a18_p2_force", "force([[1,1]],1,[],p=2)", "(1,-1)=(1,1) mod 2")
trap("a19_p1_everything_zero", "rank([[5,3]],p=1)", "x%1==0")
trap("a20_p1_force_false", "force([[1,-1]],1,[],p=1)", "all rows vanish")
trap("a21_p1_inv", "_inv(3,1)", "pow(3,-1,1)")
trap("a22_p0_rank_raises", "rank([[1]],p=0)", "ZeroDivisionError from %")
trap("a23_p0_rank_empty_ok", "rank([],p=0)", "returns before any % ")
trap("a24_p0_force_shortcircuit_ok", "force([[1,-1]],1,[0],p=0)", "len(T)>=n before any arithmetic")
trap("a25_p0_force_raises", "force([[1,-1]],1,[],p=0)", "")
trap("a26_negative_p", "rank([[3]],p=-5)", "3 % -5 == -2 in Python; then pow(-2,-7,-5)")
trap("a27_negative_p_force", "force([[1,-1]],1,[],p=-7)", "")
trap("a28_float_p_raises", "rank([[1]],p=5.0)", "pow() 3-arg needs ints")
trap("a29_float_zero_entries_no_raise", "rank([[0.0,0.0]])", "0.0 % p == 0.0 falsy; pow never called")
trap("a30_float_entry_raises", "rank([[2.0]])", "")
# B. non-prime p: pow(a,p-2,p) is NOT an inverse
trap("b01_p6_wrong_inverse_force_false", "force([[5,1]],1,[],p=6)", "true inverse of 5 mod 6 is 5, pow(5,4,6)=1; (5,1)*5=(1,5)=(1,-1) so a correct port says True, Python says False")
trap("b02_p9_wrong_inverse_force_false", "force([[2,7]],1,[],p=9)", "pow(2,7,9)=2 but 2*2=4; (2,7)*5=(1,8)=(1,-1) mod 9 -> correct port True, Python False")
trap("b03_p9_inv_value", "_inv(2,9)", "")
trap("b04_p6_inv_value", "_inv(5,6)", "")
trap("b05_p4_rank_zeroed_pivot_then_second", "rank([[2,1],[2,3]], p=4)", "first pivot row zeroed by iv=0, rk still 1; row1 untouched (fac*0)")
trap("b06_p4_wrong_inverse_of_unit", "force([[3,1]],1,[],p=4)", "3 IS a unit mod 4 (3*3=9=1) but pow(3,2,4)=1 != 3, so the pivot row is not normalised; (3,1)*3=(1,3)=(1,-1) so a correct port says True, Python says False")
trap("b07_p8_rank", "rank([[2,4],[4,2],[6,6]], p=8)", "")
trap("b08_p8_force", "force([[3,5,0,0],[2,2,7,1]],2,[],p=8)", "")
trap("b09_p1_p_minus_2_negative_exponent_inv", "_inv(2,1)", "pow(2,-1,1)")
# C. _INV cache keyed on a only (documented divergence: VERIFIED.md says do NOT reproduce; listed so the harness clears the cache)
trap("c01_cache_poison_inv", "_inv(2,7)", "poisoned by earlier _inv(2,5)=3; fresh value is 4", setup="_inv(2,5)")
trap("c02_cache_poison_force", "force([[2,0],[0,2]],1,[])", "fresh process gives (True, {0}); after a p=4 call the cached inv(2)=0", setup="force([[2,2]],1,[],p=4)")
trap("c03_cache_key_is_raw_a", "(_inv(P+2), sorted(fastcore._INV.keys()))", "key is P+2 not 2; value is inv(2)=(P+1)/2")
trap("c04_inv_of_minus_one", "_inv(-1)", "P-1")
trap("c05_inv_of_two_default_p", "_inv(2)", "(P+1)/2 = 1073741824")
# D. force: T0 semantics, n semantics
trap("d01_T0_tuple", "force([[1,-1,0,0],[0,0,1,-1]],2,(1,))", "")
trap("d02_T0_frozenset_returns_plain_set", "type(force([],1,frozenset([5]))[1]).__name__", "returned object is a set, not frozenset")
trap("d03_T0_generator", "force([[1,-1,0,0],[0,0,1,-1]],2,(j for j in [1]))", "")
trap("d04_T0_range", "force([],3,range(3))", "")
trap("d05_T0_out_of_range_pads_count", "force([[1,-1,0,0]],2,[5])", "vertex 1 never forced yet True: len(T) counts 5")
trap("d06_T0_negative_index", "force([[1,-1,0,0]],2,[-1])", "-1 is not in range(n) so U=[0,1]; -1 still counts toward n")
trap("d07_T0_superset_of_range", "force([[1,-1]],1,[0,1])", "")
trap("d08_T0_bool_element", "force([],1,[True])", "set([True]) has len 1; repr is {True}; a port extracting ints returns {1}")
trap("d09_n_zero", "force([[1,2]],0,[])", "")
trap("d10_n_negative", "force([[1,-1]],-1,[])", "len(T) < -1 is False -> (True, set()); a usize port cannot represent this")
trap("d11_n_zero_empty_rows", "force([],0,[])", "")
trap("d12_all_vertices_in_T0_rows_never_read", "force([[1]],1,[0])", "short row not validated because loop never runs")
trap("d13_rows_none_shortcircuit", "force(None,1,[0])", "rows never iterated")
trap("d14_rows_none_raises", "force(None,1,[])", "")
trap("d15_rows_none_n0", "force(None,0,[])", "")
trap("d16_empty_rows_n1", "force([],1,[])", "B empty -> nothing forced")
trap("d17_rows_generator_consumed_after_round1", "force((r for r in [[1,-1,0,0],[0,0,1,-1]]),2,[])", "list gives (True,{0,1}); generator is exhausted on the restart after the first found vertex")
trap("d18_rows_tuple_of_tuples", "force(((1,-1,0,0),(0,0,1,-1)),2,[])", "")
# E. force: row shape
trap("e01_row_longer_than_2n_ignored", "force([[1,-1,9,9,9]],1,[])", "only r[0],r[1] read")
trap("e02_short_row_ok_when_index_never_read", "force([[1,-1]],2,[1])", "j=1 forced so r[2],r[3] never read; pre-validation would raise")
trap("e03_forced_coords_ignored", "force([[1,-1,1,1]],2,[1])", "")
trap("e04_empty_row_force_raises", "force([[]],1,[])", "r[0]")
trap("e05_all_zero_row", "force([[0,0]],1,[])", "")
trap("e06_zero_row_plus_good_row", "force([[0,0],[1,-1]],1,[])", "")
trap("e07_scaled_pair_found", "force([[2,-2]],1,[])", "(2,-2) spans (1,-1)")
trap("e08_scaled_pair_notfound", "force([[2,3]],1,[])", "")
trap("e09_plain_success", "force([[1,-1]],1,[])", "")
trap("e10_plain_failure", "force([[1,1]],1,[])", "")
trap("e11_restart_needed_vertex0_after_vertex1", "force([[1,-1,1,0],[0,0,1,-1]],2,[])", "0 is not forced in round 1 (scanned first, fails); 1 is; after restart 0 is forced. A single-pass port returns (False,{1})")
trap("e12_chain_of_three", "force([[1,-1,1,0,0,0],[0,0,1,-1,1,0],[0,0,0,0,1,-1]],3,[])", "forced order 2,1,0 - three restarts")
trap("e13_chain_partial", "force([[1,-1,1,0,0,0],[0,0,1,-1,1,0],[0,0,0,0,1,1]],3,[])", "nothing forced")
trap("e14_two_found_first_round_closure_unique", "force([[1,-1,0,0],[0,0,1,-1],[1,0,1,0]],2,[])", "")
trap("e15_warm_start_equals_cold", "force([[1,-1,1,0],[0,0,1,-1]],2,[1]) == force([[1,-1,1,0],[0,0,1,-1]],2,[])", "")
trap("e16_rows_with_bools", "force([[True,-1]],1,[])", "")
# F. rank: shape
trap("f01_ragged_second_row_shorter_no_raise", "rank([[0,2],[1]])", "short row swapped into pivot position 0; only rows >= rk are indexed later")
trap("f02_ragged_second_row_longer_truncated_by_zip", "rank([[1],[2,3]])", "w=len(B[0])=1; zip truncates row 1")
trap("f03_ragged_3_2_no_raise", "rank([[1,2,3],[4,5]])", "zip truncation, then pivot at column 1")
trap("f04_ragged_raises_when_short_row_scanned", "rank([[1,2],[0]])", "")
trap("f05_first_row_empty_others_not", "rank([[],[1,2]])", "w=0")
trap("f06_rows_none", "rank(None)", "`not rows` is True")
trap("f07_rows_empty_tuple", "rank(())", "")
trap("f08_rows_iterator_nonempty", "rank(iter([[1,2],[2,4]]))", "")
trap("f09_rows_empty_iterator_raises", "rank(iter([]))", "iterator is truthy, B=[] then B[0]")
trap("f10_tuple_rows", "rank([(1,2),(2,4),(3,7)])", "")
trap("f11_single_zero_row", "rank([[0]])", "")
trap("f12_zero_then_nonzero_swap", "rank([[0],[1]])", "")
trap("f13_swap_after_elimination", "rank([[1,2],[2,4],[0,1]])", "")
trap("f14_identical_rows_many", "rank([[1,1]]*1000)", "")
trap("f15_bool_entries", "rank([[True,False],[False,True]])", "")
trap("f16_more_columns_than_rows_break", "rank([[1,2,3,4],[0,0,5,6]])", "rk>=nB break")
trap("f17_rank_no_mutation", "(lambda r: (rank(r), r))([[2,4],[-1,3]])", "input rows untouched (entries not reduced in place)")
trap("f18_force_no_row_mutation", "(lambda r: (force(r,1,[]), r))([[P+1,-1]])", "")

trap("a31_mersenne61_force_found", "force([[2*((1<<61)-1)-3, 3]],1,[],p=(1<<61)-1)", "(-3,3) spans (1,-1); products ~2^122 in the normalisation step")
trap("a32_mersenne61_rank_dense", "rank([[(1<<61)-2,(1<<61)-3],[(1<<61)-3,(1<<61)-2]], p=(1<<61)-1)", "")
trap("a33_default_p_dense_near_p", "rank([[P-1,P-2,P-3],[P-2,P-1,1],[5,P-1,P-1]])", "every product near 2^62, every difference negative")
trap("a34_default_p_force_found_near_p", "force([[P-1,1,P-2,2],[P-3,3,P-5,5]],2,[])", "both rows are multiples of (1,-1) blocks -> both vertices forced")
trap("a35_p_2pow32_plus_15_force", "force([[4294967310,1,2,3],[7,11,4294967309,2]],2,[],p=4294967311)", "")
trap("a36_p_2pow32_plus_15_force_found", "force([[4294967310,1]],1,[],p=4294967311)", "(p-1,1) = -(1,-1)")

def run(name, call, note, setup):
    fastcore._INV.clear()
    if setup:
        exec(setup, globals())
    try:
        val = eval(call, globals())
        rep = repr(val)
    except Exception as e:  # noqa
        rep = "raises %s" % type(e).__name__
    return {"name": name, "call": call, "expected_repr": rep, "note": note, **({"setup": setup} if setup else {})}

if __name__ == "__main__":
    out = [run(*t) for t in TRAPS]
    with open(os.path.join(HERE, "traps.json"), "w") as f:
        json.dump(out, f, indent=1)
    for o in out:
        print("%-55s %-60s -> %s" % (o["name"], o["call"], o["expected_repr"]))
    print(len(out), "traps")
