# Adjudication of finding 2/10 (lens `hitpaths`): rzero's hit line is unreachable

VERDICT: **real = true**. The proof holds as stated for every in-contract input.
One degenerate exception to the stated *mechanism* (not to the conclusion) is
recorded in §4; it is out of contract and both implementations die on it.

Artifacts tested (sha256 re-measured this session):
  rust/target/release/kakeya-search  add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9  (matches the pinned sha)
  src/fastcore_rs.abi3.so            03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b

Machine contended throughout (other sessions running); all wall-clock numbers below are contended.

## 1. Repro, run verbatim

    cd '/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya'
    KAKEYA_PURE_PY=1 /usr/bin/python3 rust/refute/search/r5-hitpaths/reach.py rzero-invariant
    -> rzero-invariant: 84718 graphs, rows violating column-sum-zero: 0
       real 4m17.573s  user 1m01.477s   (contended)

Same script with the PyO3 kernel (KERNEL DISCLOSURE: this second run is a
KERNEL-level check with the Python driver held fixed -- reach.py drives, the
Rust `force` computes):

    /usr/bin/python3 rust/refute/search/r5-hitpaths/reach.py rzero-invariant
    -> rzero-invariant: 84718 graphs, rows violating column-sum-zero: 0
       real 1m16.133s  user 0m22.043s   (contended)

Both kernels agree, and reach.py's `bad += 1000000` FORCING-OBJECT trap never fires.

## 2. The invariant argument, checked line by line

* `src/rzero.py:40` `rows, idx = build_rows(G, [])`. `build_rows`
  (`src/kakeya.py:590-606`) appends generator rows only in its second loop,
  `for (w, x) in R`, and R is `[]`. So `rows` is **edge rows only**. Confirmed.
* An edge row (`kakeya.py:596-600`) sets `row[2iu]+=x0, row[2iu+1]+=x1,
  row[2iv]-=x0, row[2iv+1]-=x1`. Hence exactly
  `sum_j row[2j] = 0` and `sum_j row[2j+1] = 0` as integers, for every edge,
  including the self-loop case `iu == iv` (row is all zeros). Confirmed.
* `src/rzero.py:41` `force(rows, n, set())` -- T0 empty. So on the FIRST round
  of `force` (`src/fastcore.py:22-27`) `U = range(n)`, i.e. no column is
  dropped and the restricted rows are the full rows. (This matters: the
  column-sum invariant is NOT preserved under restriction to a proper U, but
  the argument only ever needs round 1, because round 1 already fails.)
* The map phi(v) = (sum of even entries mod p, sum of odd entries mod p) is
  linear. Every B row has phi = (0,0). The target
  (`fastcore.py:66-68`: `v[i2]=1, v[i2+1]=p-1`) has phi = (1, p-1) = (1,-1).
  Row reduction only subtracts multiples of B rows, so phi(v) is invariant at
  (1,-1) != (0,0) mod p = 2^31-1. Therefore `any(v)` is always true,
  `found is None`, and `force` returns `(False, T)` at `fastcore.py:78`.
* The print at `src/rzero.py:47-48` is guarded by `if ok:` (line 42), so it
  cannot execute. `forcing` (line 43) stays 0.
* Rust side `rust/crates/kakeya-search/src/drivers/rzero.rs:80-95`:
  `build_rows(&w.graph, &mut w.rows)` then
  `force(&w.rows, n as i64, &[], P, ...)` -- same empty R, same empty T0,
  `progress_line` reachable only inside `if ok`. Argument transfers verbatim.

The argument is the workbench's own **P7** specialised to r = 0
(`KAKEYA-WORKBENCH.md:140-147`: "A = V with T_0 empty gives P7 ... a
generator-free object with T empty can never force a single vertex ... r = 0
forces |T| >= 1", and line 382 already calls `src/rzero.py` "a direct check of
P7"). So the lens is not asserting new mathematics; it is correctly connecting
an existing project theorem to a coverage row. That does not make the finding
wrong -- the coverage consequence is the new part.

## 3. Attempts to construct a counterexample (all failed)

The only free parameters of the rzero path are `d`, `pool`, `limit`, `seed`.
None of them can put a non-edge row into `rows` or a vertex into T0. Runs of
the audited binary on configurations reach.py never covered, incl. POOL8:

    ./rust/target/release/kakeya-search rzero --d 1        --pool 8 --threads 2 --verbose 1
      -> "forcing_objects": 0, scanned 1,    complete true
    ./rust/target/release/kakeya-search rzero --d 4        --pool 8 --threads 2 --verbose 1
      -> "forcing_objects": 0, scanned 729,  complete true
    ./rust/target/release/kakeya-search rzero --d 2x2      --pool 8 --threads 2 --verbose 1
      -> "forcing_objects": 0, scanned 729,  complete true
    ./rust/target/release/kakeya-search rzero --d 3x3      --pool 8 --limit 3000 --seed 7 --threads 2 --verbose 1
      -> "forcing_objects": 0, scanned 3000
    ./rust/target/release/kakeya-search rzero --d 2x2x2    --pool 8 --limit 5000 --seed 3 --threads 2 --verbose 1
      -> "forcing_objects": 0, scanned 5000
    ./rust/target/release/kakeya-search rzero --d 2x2x2x2  --pool 6 --limit 5000 --seed 1 --threads 2 --verbose 1
      -> "forcing_objects": 0, scanned 5000

(raw in rs_rzero_sweep.txt). Note `--verbose` takes a value in this CLI
(`--verbose 1`); without it the binary exits with
"kakeya-search: option --verbose needs a value".

## 4. The one gap in the stated mechanism (does not change the verdict)

The finding says `force` "returns False on the first round for every d, pool,
seed and limit, forcing_objects stays 0". That is false in exactly one
degenerate case: `n == 0`, where the `while len(T) < n` loop is never entered
and `force` returns True with no work. Both kernels:

    pure-py force([],0,set()) -> (True, set())      rust force([],0,[]) -> (True, set())
    pure-py force([],1,set()) -> (False, set())     rust force([],1,[]) -> (False, set())

`n = prod(d)` is 0 whenever `d` contains a 0, and both CLIs accept it
(`parse_dims` in main.rs:125 parses "0"; rzero_one.py does `int(x)`), so
`if ok:` is entered and `forcing += 1` executes. The print line still does not,
because the next statement dies first, on both sides:

    cd src && KAKEYA_PURE_PY=1 /usr/bin/python3 ../rust/refute/search/rzero_one.py 0 3 - 0
      -> ZeroDivisionError: Fraction(0, 0)   (src/rzero.py:44)
    ./rust/target/release/kakeya-search rzero --d 0 --pool 3 --seed 0 --threads 1
      -> thread panicked at crates/kakeya-search/src/frac.rs:29:9: zero denominator

So the CONCLUSION ("the print line is unreachable for every input, in both
implementations") survives; the intermediate claim "forcing_objects stays 0 for
every input" does not, for a degenerate out-of-contract `d`. Both sides fail on
it, in the same place, so it is not a divergence -- it is one more instance of
the already-recorded d/max_t degenerate class (s09 / `g2-tall --rows 1 --max-t 2`).

## 5. Is the correction now on disk right?

* `rust/crates/kakeya-search/PROGRESS.md:147` -- "rzero: unreachable for every
  input by the edge-row column-sum invariant, = P7". Correct, correctly
  attributed to P7, not overstated (it says the *line* is unreachable).
* `rust/refute/SWEEP-2026-09-06.md` §B -- same wording plus the 84,718-graph
  corroboration and the workbench cross-reference. Correct.
* Neither text mentions the n = 0 case. Optional one-line addendum, low value:
  "(`--d` containing 0 makes n = 0, where `force` returns True vacuously; both
  sides then die on the zero denominator before the line prints.)"

## 6. Shim check

No shim was written for this adjudication; reach.py takes no constants of its
own beyond the four (d, pool) pairs it hardcodes, and it imports `force`/`rank`
from `src/fastcore.py` rather than reimplementing them. Its `SRC` path is
absolute and correct. Its FORCING-OBJECT trap (line 36-37) makes the reported 0
a real 0 for the forcing claim, not only for the column-sum claim.

Nothing outside rust/refute/adjudicate/r5/ was written. No process was signalled.
