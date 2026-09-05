"""Hand-crafted integer-arithmetic cases: moduli, signs, overflow, bool/int.

Each entry is (kind, args, kwargs). `kind` is "force" or "rank".
"""
P = (1 << 31) - 1
I64MAX = (1 << 63) - 1
I64MIN = -(1 << 63)

# Moduli worth hammering: 1, 2, 3, small composites, primes and composites just
# below the Rust's 2^32 guard, the guard itself, 0 and negatives.
MODULI = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 91, 100, 121, 255, 256, 257,
    65535, 65536, 65537,
    2147483629,            # largest prime < 2^31
    P,                     # 2^31-1, the production modulus
    2147483648,            # 2^31, composite
    2147483649,            # 2^31+1 = 3*715827883
    3000000021,            # 1000000007*3, composite, < 2^32
    4294967291,            # largest prime < 2^32
    4294967294,            # 2^32-2
    4294967295,            # 2^32-1, largest the Rust accepts
    4294967296,            # 2^32, first rejected
    4294967297,
    (1 << 63) - 1,
    1 << 63,               # beyond i64 -> p extraction
    0, -1, -5, -P,
    True, False,
]

# Entry values chosen to sit on every arithmetic boundary.
ENTRIES = [
    0, 1, -1, 2, -2, 3, -3,
    P - 1, P, P + 1, -P, -(P - 1), -(P + 1), 2 * P, -2 * P,
    (1 << 31), (1 << 31) - 1, -(1 << 31),
    (1 << 32) - 1, (1 << 32), -(1 << 32),
    (1 << 62), -(1 << 62),
    I64MAX, I64MIN, I64MAX - 1, I64MIN + 1,
    1 << 63, -(1 << 63) - 1, 1 << 64, -(1 << 64),   # outside i64
    True, False,
]


def cases():
    C = []
    a = C.append

    # ---- 1. p == 1: every entry vanishes, but force's target vector keeps a
    #         literal 1, so nothing is ever forced.
    a(("force", ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, set()), {"p": 1}))
    a(("force", ([[1, -1]], 1, set()), {"p": 1}))
    a(("force", ([], 1, set()), {"p": 1}))
    a(("force", ([[0, 0]], 1, {0}), {"p": 1}))
    a(("rank", ([[1, 2], [3, 4]],), {"p": 1}))
    a(("rank", ([[0]],), {"p": 1}))
    a(("rank", ([[P, -P]],), {"p": 1}))

    # ---- 2. p == 2: (1,1) collapses onto (1,-1); exponent p-2 == 0.
    a(("force", ([[1, 1, 0, 0], [0, 0, 1, 1]], 2, set()), {"p": 2}))
    a(("force", ([[1, 1, 0, 0], [0, 0, 1, 1]], 2, set()), {}))
    a(("force", ([[3, 1, 0, 0], [0, 0, 5, 7]], 2, set()), {"p": 2}))
    a(("rank", ([[1, 1], [1, 1]],), {"p": 2}))
    a(("rank", ([[2, 2], [1, 3]],), {"p": 2}))
    a(("rank", ([[1, 0], [1, 1], [0, 1]],), {"p": 2}))

    # ---- 3. p == 3: exponent 1, pow(a,1,3) == a.
    a(("rank", ([[2, 1], [1, 2]],), {"p": 3}))
    a(("force", ([[2, 1, 0, 0], [0, 0, 1, 2]], 2, set()), {"p": 3}))

    # ---- 4. composite p: pow(a,p-2,p) is deterministic garbage, not an inverse.
    a(("force", ([[3, 1, 0, 0], [1, 3, 0, 0]], 1, set()), {"p": 4}))
    a(("rank", ([[3, 1], [1, 3]],), {"p": 4}))
    a(("rank", ([[2, 2], [2, 2]],), {"p": 4}))
    a(("rank", ([[6, 3], [2, 4]],), {"p": 9}))
    a(("rank", ([[7, 14], [13, 26]],), {"p": 91}))
    a(("rank", ([[7, 1], [13, 1], [1, 1]],), {"p": 91}))
    a(("force", ([[7, 13, 0, 0], [0, 0, 13, 7]], 2, set()), {"p": 91}))
    a(("rank", ([[1000000007, 3], [3, 1000000007]],), {"p": 3000000021}))
    a(("force", ([[1000000007, -1000000007, 0, 0], [0, 0, 3, -3]], 2, set()),
      {"p": 3000000021}))
    a(("rank", ([[2, 4], [4, 8]],), {"p": 2147483648}))
    a(("rank", ([[715827883, 3], [3, 715827883]],), {"p": 2147483649}))

    # ---- 5. p at the Rust's 2^32 boundary, with entries that stress a*b mod p.
    for pp in (4294967291, 4294967294, 4294967295, 4294967296):
        a(("rank", ([[pp - 1, pp - 2], [pp - 3, pp - 1]],), {"p": pp}))
        a(("rank", ([[I64MAX, I64MIN], [I64MIN + 1, I64MAX - 1]],), {"p": pp}))
        a(("force", ([[pp - 1, 1, 0, 0], [0, 0, pp - 2, 2]], 2, set()), {"p": pp}))
        a(("force", ([[I64MAX, I64MIN, 0, 0], [0, 0, I64MIN, I64MAX]], 2, set()),
          {"p": pp}))

    # ---- 6. inverse of zero must stay unreachable: pivot columns that are
    #         entirely 0 mod p, so the column is skipped rather than inverted.
    a(("rank", ([[91, 1], [182, 1]],), {"p": 91}))
    a(("rank", ([[P, 1], [2 * P, 1], [-P, 1]],), {"p": P}))
    a(("rank", ([[0, 0], [0, 0]],), {}))
    a(("force", ([[P, P, 0, 0], [0, 0, 1, -1]], 2, set()), {}))
    a(("force", ([[2147483648, -2147483646]], 1, set()), {}))

    # ---- 7. entries at / beyond the i64 boundary.
    for e in (I64MAX, I64MIN, I64MAX - 1, I64MIN + 1, 1 << 62, -(1 << 62)):
        a(("rank", ([[e, 1], [1, e]],), {}))
        a(("force", ([[e, -e, 0, 0], [0, 0, 1, -1]], 2, set()), {}))
    for e in (1 << 63, -(1 << 63) - 1, 1 << 64, -(1 << 64), 1 << 200):
        a(("rank", ([[e, 1], [1, 0]],), {}))
        a(("force", ([[e, 1, 0, 0], [0, 0, 1, -1]], 2, set()), {}))
    a(("rank", ([[I64MIN]],), {"p": 2}))
    a(("rank", ([[I64MIN]],), {"p": 1}))
    a(("rank", ([[I64MIN]],), {"p": 4294967295}))

    # ---- 8. bool where an int is expected.
    a(("rank", ([[True, False], [False, True]],), {}))
    a(("force", ([[True, False, False, False], [False, False, True, False]], 2, set()), {}))
    a(("force", ([[1, -1, 0, 0]], 1, {True}), {}))
    a(("force", ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, {False}), {}))
    a(("force", ([[1, -1, 0, 0], [0, 0, 1, -1]], 2, {True, 1}), {}))
    a(("rank", ([[1, 2], [2, 4]],), {"p": True}))
    a(("force", ([[1, -1, 0, 0]], 1, set()), {"p": True}))
    a(("rank", ([[1, 2]],), {"p": False}))
    a(("force", ([[1, -1, 0, 0]], 1, set()), {"p": False}))
    a(("force", ([[1, -1, 0, 0]], True, set()), {}))

    # ---- 9. p <= 0 with and without rows / long-enough rows: the reference
    #         raises IndexError before ZeroDivisionError when the row is short.
    a(("force", ([], 1, set()), {"p": 0}))
    a(("force", ([], 1, set()), {"p": -5}))
    a(("force", ([], 3, {0, 9}), {"p": 0}))
    a(("force", ([[1, 2]], 2, {0}), {"p": 0}))
    a(("force", ([[1, 2, 3, 4]], 2, {0}), {"p": 0}))
    a(("force", ([[1, 2]], 1, set()), {"p": 0}))
    a(("rank", ([],), {"p": 0}))
    a(("rank", ([[]],), {"p": 0}))
    a(("rank", ([[], []],), {"p": 0}))
    a(("rank", ([[], [1]],), {"p": 0}))
    a(("rank", ([[1], []],), {"p": 0}))
    a(("rank", ([[]],), {"p": -5}))
    a(("rank", ([[], [1, 2]],), {"p": -5}))
    a(("rank", ([[], [1, 2]],), {"p": 1 << 32}))
    a(("rank", ([[1, 2]],), {"p": -5}))
    a(("rank", ([[1, 0], [0, 1]],), {"p": -5}))
    a(("force", ([[1, -1, 0, 0]], 1, set()), {"p": -5}))
    a(("force", ([[1, -1, 0, 0]], 1, {0}), {"p": -5}))
    a(("force", ([[1, -1, 0, 0]], 0, set()), {"p": -5}))
    a(("force", ([[1, -1, 0, 0]], 0, set()), {"p": 0}))
    a(("force", ([[1, -1, 0, 0]], 0, set()), {"p": 1 << 32}))

    # ---- 10. ragged rows: IndexError ordering and the zip truncation.
    a(("rank", ([[1, 2, 3], [1, 2]],), {}))
    a(("rank", ([[1, 2], [1, 2, 3]],), {}))
    a(("rank", ([[1, 0, 0], [1, 1]],), {}))
    a(("rank", ([[1, 1], [1, 0, 5]],), {}))
    a(("rank", ([[0, 1, 1], [1, 0], [0, 0, 1]],), {}))
    a(("rank", ([[1, 2, 3], [1, 2]],), {"p": 2}))
    a(("rank", ([[1, 2, 3], [1, 2]],), {"p": 4294967295}))
    a(("force", ([[1, -1, 0]], 2, set()), {}))
    a(("force", ([[1, -1, 0, 0], [1, -1]], 2, set()), {}))
    a(("force", ([[1, -1], [0, 0, 1, -1]], 2, {0}), {}))

    # ---- 11. T0 outside range(n) (contract sec 1.4) at odd moduli.
    a(("force", ([], 2, {0, 5}), {}))
    a(("force", ([[1, -1, 0, 0]], 2, {5}), {}))
    a(("force", ([[1, -1, 0, 0, 0, 0], [0, 0, 1, -1, 0, 0], [0, 0, 0, 0, 1, -1]],
                 3, {-1, -2}), {}))
    a(("force", ([[1, -1, 0, 0]], 2, {I64MAX}), {}))
    a(("force", ([[1, -1, 0, 0]], 2, {I64MIN}), {}))
    a(("force", ([[1, -1, 0, 0]], 2, [5, 5, 5]), {}))
    a(("force", ([[1, -1, 0, 0]], 2, (0, 0, 0)), {}))
    a(("force", ([[1, -1, 0, 0]], 2, frozenset({0})), {}))
    a(("force", ([[1, -1, 0, 0]], 2, {1 << 63}), {}))

    # ---- 12. n boundaries.
    a(("force", ([], 0, set()), {}))
    a(("force", ([], -1, {7}), {}))
    a(("force", ([[1, -1, 0, 0]], -3, set()), {}))
    # n at / above the Rust's MAX_N guard.  T0 is pre-filled so the reference
    # short-circuits instead of running an O(n^2) closure loop.
    a(("force", ([], 1 << 20, set(range(1 << 20))), {}))
    a(("force", ([], (1 << 20) + 1, set(range((1 << 20) + 1))), {}))
    # (force([], 2**20+1, {-1}) is deliberately absent: the pure-Python
    # reference is O(n^2) there and never returns, so it cannot be compared.)

    # ---- 13. entries exactly on multiples of p at every modulus.
    for pp in (2, 3, 7, 91, P, 4294967295):
        a(("rank", ([[pp, 2 * pp], [3 * pp, -pp]],), {"p": pp}))
        a(("rank", ([[pp + 1, pp - 1], [-pp - 1, -pp + 1]],), {"p": pp}))
        a(("force", ([[pp, pp, 0, 0], [0, 0, 1, -1]], 2, set()), {"p": pp}))
        a(("force", ([[pp + 1, -(pp + 1), 0, 0], [0, 0, pp - 1, -(pp - 1)]], 2, set()),
          {"p": pp}))

    # ---- 14. single-entry sweep: every entry against every modulus.
    for e in ENTRIES:
        for pp in MODULI:
            a(("rank", ([[e, 1], [1, 1]],), {"p": pp}))

    # ---- 15. production-shaped rows (entries in -3..3) at every modulus.
    prod_rows = [[1, 0, -1, 0], [0, 1, 0, -1], [1, 2, -1, -2],
                 [2, 1, -2, -1], [1, -2, -1, 2], [3, 1, -3, -1]]
    for pp in MODULI:
        a(("rank", (prod_rows,), {"p": pp}))
        a(("force", (prod_rows, 2, set()), {"p": pp}))
        a(("force", (prod_rows, 2, {0}), {"p": pp}))

    return C
