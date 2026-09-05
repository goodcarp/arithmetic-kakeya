# PORT-TRAPS — behaviours of `fastcore.force` / `fastcore.rank` a Rust port can get wrong

Companion to `traps.json` (119 entries; regenerate with `/usr/bin/python3 gen_traps.py`).
Every `expected_repr` in `traps.json` was produced by running the call against
`K/src/fastcore.py` (pure Python; there is no `_force_py`/`_rank_py` split and no
`KAKEYA_PURE_PY` switch in that file) with `fastcore._INV.clear()` before each call.
Entries with a `setup` key run that statement first, *after* the clear, to reproduce
cache poisoning deliberately. `raises X` means the Python raises exception class X.

The 16 entries prefixed `v` are the ones already confirmed in
`K/adversary-external/VERIFIED.md`. Everything below is additional.

## 1. Modular arithmetic (group `a`)

| trap | what the port must do |
|---|---|
| a01/a02/v01 | entries are reduced with Python's floored `%`: `-1 % p == p-1`. Rust `%` gives `-1`; use `rem_euclid` on every load, including inside `force` (`r[2*j] % p`). |
| a03 | entries `>= p` are reduced on load; `P+1 -> 1`, `2P-1 -> P-1`. |
| a04–a06, a33, a34 | with default `P = 2^31-1`, `fac*b` reaches `(P-1)^2 ~ 2^62` and `a - fac*b` reaches `-2^62`. Fits i64, but the subtraction goes negative, so `(a - fac*b) % p` must be floored, or compute `(a + p - (fac*b % p)) % p`. i32 or u32 intermediates are wrong. |
| a07–a10 | `2^31 == 1 (mod P)`, so `2^62 - 1 == 0`, `2^62 == 1`, `-(2^62) == P-1`, `-(2^62)+1 == 0`. A port that reduces with wrapping or truncating casts gets nonzero pivots here. |
| a11/a12 | `1 << 70` is a legal Python entry (`== 256 mod P`). A PyO3 port extracting `i64` raises `OverflowError` where Python returns `1`. Document or reduce big ints Python-side; a differential test must not feed entries beyond i64 unless the port handles them. |
| a13–a15, a31, a32, a35, a36 | caller-supplied `p = 2^32+15` (prime) and `p = 2^61-1` (prime): `(p-1)^2` exceeds u64. Python is correct here; a u64 port silently is not. Either use u128 for the product or state `p < 2^32` as a precondition and reject larger `p`. |
| a16–a18 | `p = 2`: `_inv(0,2) == 1` because `pow(0,0,2) == 1`; not reachable from `rank`/`force` (pivots are nonzero) but a direct `_inv` binding must match. `(1,-1) == (1,1) mod 2`, so `force([[1,1]],1,[],p=2)` succeeds. |
| a19–a21 | `p = 1`: every entry reduces to 0; `rank == 0`, `force` finds nothing; `_inv(3,1) == pow(3,-1,1) == 0` (Python 3.8+ negative-exponent modular pow). |
| a22–a25 | `p = 0`: `x % 0` raises `ZeroDivisionError`, but only when reached. `rank([],p=0) == 0` and `force([[1,-1]],1,[0],p=0) == (True,{0})` do **not** raise because no arithmetic happens. |
| a26/a27 | negative `p`: Python floored `%` yields non-positive residues and `pow` with a negative modulus still returns something (`rank([[3]],p=-5) == 1`, `force([[1,-1]],1,[],p=-7) == (True,{0})`). Nobody calls this; the port may reject it, but then the differential harness must not compare it. |
| a28–a30 | float `p` or float entries: `pow(float, int, int)` raises `TypeError` — but only if a pivot is ever inverted. `rank([[0.0,0.0]]) == 0` with no error. |

## 2. Non-prime `p`: `pow(a, p-2, p)` is not an inverse (group `b`)

The Python never checks primality. With composite `p` the "inverse" is sometimes 0,
sometimes a wrong unit. **The port must reproduce the wrong answers**, or refuse
composite `p` up front and exclude it from the differential test. Do not "fix" with
extended GCD: that changes results (VERIFIED.md #2, #14, #15 and below).

* `b01`: `p=6`, row `(5,1)`. True inverse of 5 is 5 and `(5,1)*5 == (1,-1)`, so a
  correct port says `True`; Python computes `pow(5,4,6) == 1`, leaves the row
  unnormalised and says `(False, set())`.
* `b02`: `p=9`, row `(2,7)`: correct answer `True`, Python `(False, set())`
  (`pow(2,7,9) == 2`, but `2*2 == 4`).
* `b06`: `p=4`, row `(3,1)`: 3 is a unit, `pow(3,2,4) == 1 != 3`; Python `False`,
  correct `True`.
* `b05`: `p=4`, `[[2,1],[2,3]]`: first pivot row is zeroed by `iv=0`, `rk` still
  increments, the second row is *untouched* (`fac*0`), and column 1 then supplies a
  second pivot: `rank == 2`.
* `b07/b08`: `p=8` rank and force values, same mechanism.
* `b09`: `_inv(2,1) == 0`.

## 3. The `_INV` cache is keyed on `a` alone (group `c`)

`c01`: after `_inv(2,5)`, `_inv(2,7)` returns 3 (fresh value 4). `c02`: after any
`p=4` call, `force([[2,0],[0,2]],1,[])` returns `(False, set())` (fresh: `(True,{0})`).
`c03`: the key is the *raw* `a` — `_inv(P+2)` is cached under `2147483649`, not `2`,
value `1073741824`. `c04/c05`: `_inv(-1) == P-1`, `_inv(2) == (P+1)/2`.

VERIFIED.md's ruling stands: do not reproduce the cache. But the harness must clear
`fastcore._INV` between Python calls with different `p`, or every `p`-varying trap
above will produce phantom mismatches that are Python's fault.

## 4. `force`: `T0` and `n` semantics (group `d`)

* `T0` may be any iterable: tuple, frozenset, generator, `range` (`d01–d04`). The
  returned set is always a fresh `set` (never the input object, never a frozenset).
* `len(set(T0)) >= n` short-circuits before any row is read. Out-of-range and
  negative indices count toward `n` (`d05`: `force([[1,-1,0,0]],2,[5]) == (True,{0,5})`
  although vertex 1 was never forced; `d06`: `-1` counts and is not in `U`). A port that
  validates `0 <= t < n` or uses `usize` diverges on these. The drivers never pass
  out-of-range `T0`, so "reject" is defensible — but say so.
* `T0` elements are compared with `j not in T`: `True` collides with `1` (`d08`, repr
  `{True}`).
* `n <= 0` returns `(True, set())` immediately (`d09–d11`); `n` is never validated.
* When `len(T0) >= n` the rows are never touched: `force([[1]],1,[0])` and even
  `force(None,1,[0])` succeed (`d12/d13`), `force(None,0,[])` too (`d15`), but
  `force(None,1,[])` raises `TypeError` (`d14`).
* **Rows are re-iterated on every restart.** A generator passed as `rows` is consumed
  in round 1; on the restart after the first found vertex it is empty (`d17`:
  `(False,{0})` vs `(True,{0,1})` for the equivalent list). A port that materialises
  rows once (the sane thing) diverges from Python on generator input. Document.
* `force([],1,[])` (no rows at all) is `(False, set())`, not an error (`d16`).

## 5. `force`: row shape and the scan/restart structure (group `e`)

* Only `r[2*j]`, `r[2*j+1]` for `j in U` are read. Rows longer than `2n` are fine
  (`e01`); rows shorter than `2n` are fine as long as the missing coordinates belong to
  vertices in `T` (`e02`: `force([[1,-1]],2,[1]) == (True,{0,1})`); an empty row raises
  `IndexError` when read (`e04`). Up-front shape validation in the port changes
  `e02/d12` from success to error.
* Entries at forced coordinates are ignored, whatever they are (`e03`).
* A row that is all-zero *on `U`* is dropped before elimination (`e05/e06`, VERIFIED #5).
* Found-vertex scan is ascending `j` over `U`, and after each found vertex the loop
  **restarts from scratch** (new `U`, new `B`, new elimination). Because forcing is
  monotone the final closure is unique, so the order does not change the returned set —
  but a port that scans `U` once and stops (no restart) returns `(False,{1})` on `e11`
  where Python returns `(True,{0,1})`; `e12` needs three restarts; `e15` checks that a
  warm start equals a cold start.
* The membership test reduces `v = e_{2i} + (p-1) e_{2i+1}` by the pivot rows in
  pivot order. Python's elimination is full Gauss–Jordan (rows above and below). A
  forward-only echelon also gives the right membership answer, so that is not a trap;
  what *is* a trap is reducing `v` by pivots in a different order than ascending column,
  or not reducing `v` modulo `p` after each step.
* `rank` uses forward elimination only (rows below `rk`), `force` uses full elimination
  (`i != rk`). Same rank, different intermediate matrices; only matters if the port
  exposes intermediates.

## 6. `rank`: shape and input types (group `f`)

* `w = len(B[0])`. A first row shorter than the others silently truncates every other
  row through `zip` (`f02`: `rank([[1],[2,3]]) == 1`; `f03`: `[[1,2,3],[4,5]] == 2`,
  no error). A later row shorter than `w` raises `IndexError` **only if it is indexed at
  a column beyond its length** — which depends on pivot swaps: `rank([[0,2],[1]]) == 2`
  (the short row is swapped into pivot position 0 and never indexed again, `f01`) while
  `rank([[1,2],[3]])` and `rank([[1,2],[0]])` raise (`v12`, `f04`). A port with a
  rectangular matrix type cannot reproduce this; pick "raise on ragged" and exclude
  ragged inputs from the differential set, or match Python exactly.
* `rank([[],[1,2]]) == 0` (`f05`): width comes from the first row.
* `not rows` is the emptiness test: `rank(None) == rank(()) == rank([]) == 0` (`f06/f07`),
  but a non-empty iterator works (`f08`) and an **empty iterator raises `IndexError`**
  (`f09`) because iterators are truthy.
* Rows may be tuples; entries may be bools (`f10`, `f15`, `e16`).
* `rank([[1,1]]*1000) == 1` (`f14`): 1000 aliased rows; `B` is rebuilt per row so aliasing
  is harmless. A port that reduces in place on the caller's buffer would corrupt the
  aliased rows — see also `f17/f18`: inputs are never mutated and entries are **not**
  reduced in place (`[[2147483648, -1]]` comes back unchanged).
* Return type is a Python `int`; `force` returns `(bool, set)`.

## 7. Things that are *not* traps (checked)

* Pivot choice (first nonzero row from `rk`) never changes `rank` or the membership
  answer; only intermediate matrices differ.
* Which vertex is found first never changes the returned closure (monotonicity).
* `(p-1)^2 < 2^63` for the default `P`, so i64 products are safe there; only the sign
  of `a - fac*b` and caller-supplied `p >= 2^32` need care.
* No driver in `K/src` passes a non-default `p`, and none passes ragged rows,
  out-of-range `T0`, generators as `rows`, or `n <= 0`. All those traps are about
  matching the *reference*, not about production results. The production-relevant
  ones are groups 1 (sign/overflow), 5 (restart, zero-row drop, forced-coordinate
  ignore) and the `d17` "rows re-iterated" note if the port streams rows.
