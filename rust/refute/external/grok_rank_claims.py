"""Every concrete rank() claim grok-cli made, tested verbatim."""
from probe import check
C = lambda *a, **k: (lambda: (a, k))
res = []
def T(cid, mk, note=""):
    res.append((cid, check(cid, "rank", mk, note)))

# claimed DIVERGENT
T("G1_p2p32",        C([[1]], 4294967296),                "py 1 / rs ValueError")
T("G2_p64prime",     C([[1]], 2305843009213693951),       "py 1 / rs ValueError")
T("G3_zero_p2p32",   C([[0]], 4294967296),                "py 0 / rs ValueError")
T("G4_row0empty_p2p32",C([[],[1]], 4294967296),           "py 0 / rs ValueError")
T("G5_ragged_p2p32", C([[1,2],[3]], 4294967296),          "py IndexError / rs ValueError")
T("G6_2p63",         C([[9223372036854775808]]),          "py 1 / rs OverflowError")
T("G7_neg2p63m1",    C([[-9223372036854775809]]),         "py 1 / rs OverflowError")
T("G8_2p63_p0",      C([[9223372036854775808]], 0),       "py ZeroDivisionError / rs OverflowError")
T("G9_2p63_pneg1",   C([[9223372036854775808]], -1),      "py 0 / rs OverflowError")
T("G10_2p63_p2p32",  C([[9223372036854775808]], 4294967296),"py 0 / rs OverflowError")
T("G11_float0",      C([[0.0]]),                          "py 0 / rs TypeError")
T("G12_float5mod5",  C([[5.0]], 5),                       "py 0 / rs TypeError")
T("G13_float_ragged",C([[0.0],[0.0,2.5]]),                "py 0 / rs TypeError")
T("G14_row0empty_float",C([[],[1.5]]),                    "py 0 / rs TypeError")
T("G15_float1_p0",   C([[1.0]], 0),                       "py ZeroDivisionError / rs TypeError")
T("G16_float0_p0",   C([[0.0]], 0),                       "py ZeroDivisionError / rs TypeError")
T("G17_zero_pneg1",  C([[0]], -1),                        "py 0 / rs ValueError")
T("G18_one_pneg1",   C([[1]], -1),                        "py 0 / rs ValueError")
T("G19_two_pneg2",   C([[2]], -2),                        "py 0 / rs ValueError")
T("G20_pneg5_ragged",C([[0],[0,2]], -5),                  "py 0 / rs ValueError")
T("G21_row0empty_pneg5",C([[],[1]], -5),                  "py 0 / rs ValueError")
T("G22_pneg1_short", C([[0,0],[0]], -1),                  "py IndexError / rs ValueError")
T("G23_iter_empty",  lambda: ((iter([]),), {}),           "py IndexError / rs 0")
T("G24_map_empty",   lambda: ((map(lambda x: x, []),), {}),"py IndexError / rs 0")
T("G25_zip_empty",   lambda: ((zip(),), {}),              "py IndexError / rs 0")
T("G26_genexp_empty",lambda: (((x for x in []),), {}),    "py IndexError / rs 0")
T("G27_iter_empty_p0",lambda: ((iter([]), 0), {}),        "py IndexError / rs 0")

# claimed to AGREE -- these must come back SAME or grok is wrong
T("G28_none",        C(None),                             "claimed agree")
T("G29_emptyrow",    C([[]]),                             "claimed agree")
T("G30_emptyrows_p0",C([[],[]], 0),                       "claimed agree")
T("G31_float1_5",    C([[1.5]]),                          "claimed agree: TypeError both")
T("G32_pneg5_one",   C([[1]], -5),                        "claimed agree: ValueError both")
T("G33_p0_nonempty", C([[1]], 0),                         "claimed agree: ZeroDivisionError both")
T("G34_range0",      C(range(0)),                         "claimed agree: 0")
T("G35_emptystr",    C(""),                               "claimed agree: 0")
T("G36_emptytuple",  C(()),                               "claimed agree: 0")
# grok said "all-empty matrix agrees no matter what p" -- test p outside i64
T("G37_emptyrow_p2p70",C([[]], 1<<70),                    "grok says agree; i64 extraction of p?")
T("G38_emptyrow_pneg",C([[]], -5),                        "claimed agree")

print()
print("claims tested: %d | DIFF: %d | SAME: %d" % (len(res), sum(1 for _,v in res if not v), sum(1 for _,v in res if v)))
