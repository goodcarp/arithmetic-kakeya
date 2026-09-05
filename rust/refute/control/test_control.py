"""Ordering / control-flow refutation battery for fastcore_rs vs fastcore.

Each case is a *factory* returning (args, kwargs), so one-shot iterables are
rebuilt independently for the Python and the Rust side.
"""
from harness import (P, Results, call_py_force, call_rs_force,
                     call_py_rank, call_rs_rank)

R = Results("control-flow")

# ---------------------------------------------------------------- force cases
E1 = [1, -1, 0, 0]          # forces vertex 0 on n=2
E2 = [0, 0, 1, -1]          # forces vertex 1 on n=2
CHAIN3 = [[1, -1, 0, 0, 0, 0], [0, 0, 1, -1, 0, 0], [0, 0, 0, 0, 1, -1]]

FORCE_CASES = [
    # --- baseline ordering -------------------------------------------------
    ("empty rows list, n=2", lambda: (([], 2, set()), {})),
    ("empty rows tuple, n=2", lambda: (((), 2, set()), {})),
    ("n=0 empty T0", lambda: (([], 0, set()), {})),
    ("n=0 nonempty T0", lambda: (([], 0, {3, 7}), {})),
    ("n=-1 nonempty T0", lambda: (([], -1, {3}), {})),
    ("n=1 empty rows", lambda: (([], 1, set()), {})),
    ("n=1 forcing row", lambda: (([[1, -1]], 1, set()), {})),
    ("n=1 row longer than 2n", lambda: (([[1, -1, 9, 9]], 1, set()), {})),
    ("all-zero rows", lambda: (([[0, 0, 0, 0], [0, 0, 0, 0]], 2, set()), {})),
    ("zero row mixed with live row", lambda: (([[0, 0, 0, 0], E2], 2, set()), {})),
    ("rows entries == 0 mod p vanish",
     lambda: (([[P, P, 0, 0], E2], 2, set()), {})),
    ("duplicate rows x40", lambda: (([E1] * 40, 2, set()), {})),
    ("row order swapped A", lambda: (([E1, E2], 2, set()), {})),
    ("row order swapped B", lambda: (([E2, E1], 2, set()), {})),
    ("chain3 ascending pick", lambda: ((CHAIN3, 3, set()), {})),
    ("chain3 reversed rows", lambda: ((CHAIN3[::-1], 3, set()), {})),

    # --- T0 shapes ---------------------------------------------------------
    ("T0 list", lambda: (([E1, E2], 2, [0]), {})),
    ("T0 tuple", lambda: (([E1, E2], 2, (0,)), {})),
    ("T0 frozenset", lambda: (([E1, E2], 2, frozenset({0})), {})),
    ("T0 set", lambda: (([E1, E2], 2, {0}), {})),
    ("T0 generator", lambda: (([E1, E2], 2, (x for x in [0])), {})),
    ("T0 dict (keys)", lambda: (([E1, E2], 2, {0: 'a'}), {})),
    ("T0 range", lambda: (([E1, E2], 2, range(1)), {})),
    ("T0 dup list", lambda: (([E1, E2], 2, [0, 0, 0]), {})),
    ("T0 {True}", lambda: (([E1, E2], 2, {True}), {})),
    ("T0 [True, 1]", lambda: (([E1, E2], 2, [True, 1]), {})),
    ("T0 already full", lambda: (([], 2, {0, 1}), {})),
    ("T0 superset of range(n)", lambda: (([], 2, {0, 1, 2, 3}), {})),

    # --- T0 out of range (contract sec 1.4) --------------------------------
    ("T0 {0,5} n=2 no rows", lambda: (([], 2, {0, 5}), {})),
    ("T0 {5} n=2 one row", lambda: (([E1], 2, {5}), {})),
    ("T0 {9} n=3 chain", lambda: ((CHAIN3, 3, {9}), {})),
    ("T0 {-1,-2} n=3 chain", lambda: ((CHAIN3, 3, {-1, -2}), {})),
    ("T0 [-1,-1,-2] dup extras", lambda: ((CHAIN3, 3, [-1, -1, -2]), {})),
    ("T0 {-1} n=1 no rows", lambda: (([], 1, {-1}), {})),
    ("T0 huge out-of-range", lambda: ((CHAIN3, 3, {10**9}), {})),

    # --- ragged / short rows ------------------------------------------------
    ("row shorter than 2n", lambda: (([[1, -1]], 2, set()), {})),
    ("row len 2n-1 (b read fails)", lambda: (([[1, -1, 0]], 2, set()), {})),
    ("ragged: good row then short row",
     lambda: (([E1, [1, -1]], 2, set()), {})),
    ("ragged: short row then good row",
     lambda: (([[1, -1], E1], 2, set()), {})),
    ("ragged: empty row first", lambda: (([[], E1], 2, set()), {})),
    ("ragged: empty row last", lambda: (([E1, []], 2, set()), {})),
    ("short row unreachable because T0 covers it",
     lambda: (([[0, 0, 1, -1]], 2, {1}), {})),
    ("short row becomes reachable in round 2",
     lambda: (([E1, [0, 0, 1, -1, 0, 0]], 3, set()), {})),

    # --- rows container / row shapes ---------------------------------------
    ("rows tuple of tuples", lambda: (((tuple(E1), tuple(E2)), 2, set()), {})),
    ("rows list of tuples", lambda: (([tuple(E1), tuple(E2)], 2, set()), {})),
    ("rows tuple of lists", lambda: (((E1, E2), 2, set()), {})),
    ("rows with bool entries",
     lambda: (([[True, -1, False, False]], 1, set()), {})),
    ("rows list of ranges", lambda: (([range(0, 4)], 2, set()), {})),

    # --- rows as a one-shot iterator ---------------------------------------
    ("rows generator, 1 round needed",
     lambda: (((r for r in [E1]), 1, set()), {})),
    ("rows generator, 2 rounds needed",
     lambda: (((r for r in [E1, E2]), 2, set()), {})),
    ("rows generator, empty",
     lambda: (((r for r in []), 2, set()), {})),
    ("rows iter(list), 2 rounds needed",
     lambda: ((iter([E1, E2]), 2, set()), {})),
    ("rows generator, 3 rounds needed",
     lambda: (((r for r in CHAIN3), 3, set()), {})),

    # --- entries at positions the reference never reads ---------------------
    ("unread trailing str entry",
     lambda: (([[1, -1, "x", "y"]], 1, set()), {})),
    ("unread trailing float entry",
     lambda: (([[1, -1, 0.5]], 1, set()), {})),
    ("unread trailing huge int",
     lambda: (([[1, -1, 2 ** 64]], 1, set()), {})),
    ("unread trailing None",
     lambda: (([[1, -1, None]], 1, set()), {})),
    ("bad entry at a column already in T0",
     lambda: (([[1, -1, 2 ** 64, 0]], 2, {1}), {})),
    ("bad entry in a row, IndexError comes first in py",
     lambda: (([[1, -1, 2 ** 64]], 2, set()), {})),

    # --- p variations -------------------------------------------------------
    ("p=2 collapses (1,1)",
     lambda: (([[1, 1, 0, 0], [0, 0, 1, 1]], 2, set(), 2), {})),
    ("p=P same rows",
     lambda: (([[1, 1, 0, 0], [0, 0, 1, 1]], 2, set(), P), {})),
    ("p=1", lambda: (([E1, E2], 2, set(), 1), {})),
    ("p=1 with T0 full", lambda: (([E1, E2], 2, {0, 1}, 1), {})),
    ("p=0", lambda: (([E1], 1, set(), 0), {})),
    ("p=0 rows empty", lambda: (([], 1, set(), 0), {})),
    ("p=0 short row (IndexError first)", lambda: (([[]], 1, set(), 0), {})),
    ("p=3 composite-free", lambda: (([[3, 1, 0, 0], [1, 3, 0, 0]], 1, set(), 3), {})),
    ("p=4 composite", lambda: (([[3, 1, 0, 0], [1, 3, 0, 0]], 1, set(), 4), {})),
    ("p keyword", lambda: (([E1, E2], 2, set()), {"p": P})),
]

for label, fac in FORCE_CASES:
    a1, k1 = fac()
    a2, k2 = fac()
    R.cmp("force: " + label, call_py_force(*a1, **k1), call_rs_force(*a2, **k2))

# ----------------------------------------------------------------- rank cases
RANK_CASES = [
    ("empty list", lambda: (([],), {})),
    ("empty tuple", lambda: ((((),), {}))),
    ("empty set", lambda: ((set(),), {})),
    ("empty dict", lambda: (({},), {})),
    ("empty generator", lambda: (((r for r in []),), {})),
    ("empty iter(list)", lambda: ((iter([]),), {})),
    ("empty range", lambda: ((range(0),), {})),
    ("single empty row", lambda: (([[]],), {})),
    ("two empty rows", lambda: (([[], []],), {})),
    ("empty row then live row", lambda: (([[], [1, 2]],), {})),
    ("live row then empty row", lambda: (([[1, 2], []],), {})),
    ("single row", lambda: (([[1, 2, 3]],), {})),
    ("dup rows x40", lambda: (([[1, 2, 3]] * 40,), {})),
    ("all zero rows", lambda: (([[0, 0], [0, 0]],), {})),
    ("zero row first", lambda: (([[0, 0], [1, 1]],), {})),
    ("zero row last", lambda: (([[1, 1], [0, 0]],), {})),
    ("identity", lambda: (([[1, 0], [0, 1]],), {})),
    ("swap needed", lambda: (([[0, 1], [1, 0]],), {})),
    ("row0 short truncates", lambda: (([[1, 0], [1, 1, 5, 5]],), {})),
    ("row1 short, w from row0", lambda: (([[1, 0, 0, 7], [1, 1]],), {})),
    ("short row raises later", lambda: (([[9, 9, 9], [1, 1], [0, 0, 0, 1]],), {})),
    ("short row raises now", lambda: (([[1], []],), {})),
    ("rows tuple of tuples", lambda: ((((1, 0), (0, 1)),), {})),
    ("rows generator", lambda: (((r for r in [[1, 0], [0, 1]]),), {})),
    ("rows iter(list)", lambda: ((iter([[1, 0], [0, 1]]),), {})),
    ("rows with bools", lambda: (([[True, False], [False, True]],), {})),
    ("p=2", lambda: (([[1, 1], [1, 1]], 2), {})),
    ("p=1", lambda: (([[1, 1], [1, 1]], 1), {})),
    ("p=0", lambda: (([[1, 1]], 0), {})),
    ("p=0 empty rows", lambda: (([], 0), {})),
    ("p=0 single empty row", lambda: (([[]], 0), {})),
    ("p=0 empty-row-first", lambda: (([[], [1]], 0), {})),
    ("p keyword", lambda: (([[1, 0], [0, 1]],), {"p": P})),
    ("7x8 build_rows-shaped", lambda: (([
        [1, 0, 0, 0, -1, 0, 0, 0],
        [0, 1, 0, 0, 0, -1, 0, 0],
        [1, 1, -1, -1, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, -1, 0],
        [0, 0, 0, 1, 0, 0, 0, -1],
        [1, 2, 0, 0, 0, 0, -1, -2],
        [2, 1, 0, 0, -2, -1, 0, 0],
    ],), {})),
]

for label, fac in RANK_CASES:
    a1, k1 = fac()
    a2, k2 = fac()
    R.cmp("rank: " + label, call_py_rank(*a1, **k1), call_rs_rank(*a2, **k2))

nd = R.report()
print("TOTAL DIVERGENCES:", nd)
