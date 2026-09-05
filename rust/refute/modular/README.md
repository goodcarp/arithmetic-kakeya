# refute/modular — integer-arithmetic attack on fastcore_rs.force / .rank

Reference is always `fastcore._force_py` / `fastcore._rank_py` with
`fastcore._INV.clear()` immediately before each call (kernel contract sec 2.1).
Both `.so` builds were tested: the one shipped in `src/` and a fresh
`maturin build --release` of the current tree (they agree on every case).

Run (one variant per process; the extension's init symbol is fixed):

    /usr/bin/python3 run_hand.py          shipped|fresh
    /usr/bin/python3 run_types.py         shipped|fresh
    /usr/bin/python3 fuzz.py              shipped|fresh [count] [seed]
    /usr/bin/python3 deep_fuzz.py         shipped|fresh [count] [seed]
    /usr/bin/python3 ragged_fuzz.py       shipped|fresh [count] [seed]
    /usr/bin/python3 exhaustive_small.py  shipped|fresh
    /usr/bin/python3 threads_check.py     shipped|fresh
    /usr/bin/python3 minimal_repros.py    shipped|fresh
    /usr/bin/python3 extra_repros.py

Totals: 633,484 differential comparisons. Zero value-level divergences on any
input the reference and the port both accept. The only divergences found are
argument-admissibility ones, listed in minimal_repros.py, all unreachable from
every driver and test (no call site passes `p`; every row entry is in -3..3).

Two cases are deliberately absent because the *reference* is intractable there,
not because the port is right: `force([], 2**20+1, {-1})` and
`force([], 2**64, {0})` make Python run an O(n^2) closure loop that never
returns. The Rust answers ValueError / OverflowError immediately.
