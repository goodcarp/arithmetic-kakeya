# r5 — lens `hitpaths`: end-to-end coverage of the four "found something" paths

Run 2026-09-06, ~16:35–17:10 EDT, by a fresh refuter.  Target of the lens:
r3's stated gap — every end-to-end comparison for `g2_tall`, `cycles8`,
`stacked` and `rzero` has `best: null` / `hits: 0`, so four driver output
shapes are pinned only by Rust unit tests whose expected strings the porter
wrote.

Artifact under test: `rust/target/release/kakeya-search`, sha256
`add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9`
(re-verified at the start of this session).  Python side is `/usr/bin/python3`
(3.9.6), cwd `arithmetic-kakeya/src`.

**Machine was heavily contended throughout** (load average 30–39 on 6 physical
cores: the protected 8-cycle job pid 12158, the pure-Python POOL3 oracle pid
13369, and other agents).  Every wall-clock number below is contended and is
not a benchmark.

**VERDICT: not refuted.**  No in-contract input was found on which Rust and
Python disagree in content.  Two things were established instead:

1. Three of the four hit paths are *unreachable*, not merely unexercised —
   one of them provably so for every possible input.  So r3's gap cannot be
   closed by running the drivers harder; it has to be closed at the formatter
   level (which §4 does) or accepted.
2. A new class of check (§4) replaces the porter-written expected strings with
   strings produced by **CPython executing the Python drivers' own `print`
   statements**, extracted from `src/*.py` with `ast` rather than retyped.
   325 formatted lines, 0 mismatches.

--------------------------------------------------------------------------
## 1. rzero's `generator-free forcing object!` line is DEAD CODE — provably

`rzero.sweep` calls `force(rows, n, set())` where `rows` is `build_rows(G, [])`,
i.e. **edge rows only** (`src/kakeya.py:594-600`).  An edge row for edge
`(u, v, x)` is `+x` at `u` and `-x` at `v`, so for every edge row

    (sum_j row[2j], sum_j row[2j+1]) == (0, 0)

and therefore for every linear combination of them.  The vector `force` must
find in that span is `delta_j (x) (1, -1)`, whose column sums are `(1, -1)`.
Mod `p = 2^31-1` that is `(1, p-1) != (0, 0)`.  So the very first round of
`force` can never find a vertex, `force` returns `False`, `forcing` stays 0,
and the print line is unreachable **for every `d`, every pool, every seed and
every limit** — in both implementations.  `drivers/rzero.rs:76-88` has exactly
the same shape (`force(&w.rows, n, &[], ...)` on `build_rows` output only), so
the argument transfers verbatim.

Empirical corroboration (pure Python, `KAKEYA_PURE_PY=1`):

    /usr/bin/python3 rust/refute/search/r5-hitpaths/reach.py rzero-invariant
    -> rzero-invariant: 84718 graphs, rows violating column-sum-zero: 0

84718 graphs over `d` in {2x2 POOL6, 2x2x2 POOL4, 2x3 POOL4, 3x2 POOL4}: zero
rows violate the invariant and zero forcing objects.  This also matches the
recorded science (`logs/rzero.log`: `forcing_objects: 0` in all six jobs).

Consequence for the record: `rzero`'s hit line is not "untested", it is
untestable.  `drivers/rzero.rs::progress_line` can only ever be checked the
way §4 checks it.

## 2. stacked's `for x in h[:5]` block cannot fire for POOL3/4/5/6

`stacked.py:47` appends to `hits` only when `sc < Fraction(7, 4)`, and that
`7/4` is a **hardcoded literal on both sides** (`src/stacked.py:47`;
`drivers/stacked.rs:135` `if sc < Frac::new(7, 4)`).  `--target` / `run(target=)`
changes only the budget, never the hit threshold — so the parameter that looks
like a lever is not one.  Raising the target can only admit solutions with MORE
generators, i.e. higher scores.

The recorded complete runs (`logs/stacked.log`, and the Rust reproduction
`logs/rust-stacked_pool4.log` / `logs/rust-stacked_pool6.log`) give
`best = 7/4` exactly for POOL4 and POOL6 at `max_t=2`, hits 0.  Because
`POOL3 ⊂ POOL4 ⊂ POOL5 ⊂ POOL6 ⊂ POOL8` and the pool is used both as the
interface alphabet and as the generator-direction set, any stacked solution
over a smaller pool is also a solution over a larger one with the same score.
Hence

    min score(POOL3) >= min score(POOL4) = 7/4
    min score(POOL5) >= min score(POOL6) = 7/4

so `hits` is empty for POOL3, POOL4, POOL5 and POOL6 at every `max_t <= 2`.
Only `--pool 8` is not excluded by this argument, and a POOL8 stacked run is
6561 interfaces x 37 T0 sets with an 8-direction DFS — far outside this
session's budget (the audited binary needs >160 s for POOL4 at `--max-t 0`,
625 interfaces, one T0 each).

I did try to prune POOL8 analytically with the driver's own P3/P4/P6 bounds
(`reach2.py`); they are too weak (POOL8 leaves 13539 (graph,T0) pairs whose
score lower bound is still below 7/4), so POOL8 stays open, not excluded.

    /usr/bin/python3 rust/refute/search/r5-hitpaths/reach2.py 4 2
    -> POOL4 max_t=2 target=7/4: 625 interfaces; pairs surviving P3+P4+P6 that
       could still score < 7/4: 8789; min lower bound = 1

## 3. g2_tall's improvement line and cycles8's HITOBJ: reachable in principle,
##    not reachable in this session

`g2_tall`'s `[2xr] score ...` line fires on **any** new best, so it needs only
one forcing solution inside the strict-improvement-on-11/6 cap.  Exhaustive
runs say there is none for r <= 4:

  - r = 2, `max_t` 0 and 1: `best null hits 0 complete true` (this session,
    both sides — §5).
  - r = 3: `py_g2-tall_3_2.txt` (r3, pure Python, complete).
  - r = 4: `refute/search/rs_g2tall_2x4.txt` — `complete: true`, `best: null`
    (the audited binary, exhaustive over all 4096 label tuples).
  - r = 5, 6: only TIME LIMIT runs exist on either side
    (`logs/g2_tall.log`, `logs/rust-g2_tall_2x5.log`, `..._2x6.log`).

`cycles8`'s HITOBJ needs `sc <= target` with a solution actually found.  There
is none at the shipped target: POOL3 `--target 67/40` gives `best null tested
29004`.  Loosening the target is the documented lever, but it is exactly what
makes the DFS explode.  Measured this session with the audited binary
(`--patterns` used only to make the probe affordable; the flag is Rust-only, so
these are probes, not comparisons):

    kakeya-search cycles8 --pool 3 --target 7/4  --patterns 4 --threads 1
      -> best null, hits 0, tested 624   [28.4 s]
    kakeya-search cycles8 --pool 3 --target 15/8 --patterns 4 --threads 1
      -> best null, hits 0, tested 816   [48.5 s]
    kakeya-search cycles8 --pool 3 --target 2    --patterns 4 --threads 1
      -> did not finish
    kakeya-search cycles8 --pool 3 --target 2 --threads 2 (all 5 patterns)
      -> did not finish (>25 min)

That is 27 of the 1161 POOL3 graphs.  `--target 2` is the first target that
allows the 8 generators a 2-regular m=8 graph could need (budget
`int(2*8)-8 = 8`), and it is also where `min_generators`' DFS over 24
candidates stops terminating.  So the honest statement is: cycles8's HITOBJ
path is not excluded, but no configuration was found that fires it at a cost
this session could pay, and none at all that pure Python could pay.

**Requested deliverable not achieved:** I could not find a configuration of
`g2_tall`, `cycles8`, `stacked` or `rzero` — pure Python or otherwise — that
produces `hits > 0`.  For `rzero` and for `stacked` at pools 3–6 that is
because none exists.  Only `scan`'s HIT/HITOBJ path has a cheap pure-Python
hits>0 comparison, and that was already covered (r3 F5: 1338 hits, 2677 lines,
identical).

## 4. NEW CHECK — the four hit lines against CPython-generated oracle strings

Since the paths cannot be made to fire, the porter-written expected strings can
still be replaced by machine-generated ones.  Method:

  a. `improve/r5-hitpaths/` holds a **copy** of `crates/kakeya-core` and
     `crates/kakeya-search`.  `diff -r` against the audited crates: identical
     except for the one file I added (`src/bin/fmtdump.rs`).  Cross-check that
     the copy behaves like the audited artifact: `check --threads 2` output of
     the fresh build is byte-identical to the audited binary's after masking
     the `[Ns]` bracket (14 PASS / 2 SKIP / 0 FAIL both, `out/check_audited_t2.txt`
     vs `out/check_copy_t2.txt`).
  b. `fmtdump` calls only the already-public formatters
     `g2_tall::progress_line`, `cycles8::progress_line`, `stacked::hit_line`,
     `rzero::progress_line` on 65 synthetic cases (5 hand-picked corners — empty
     label tuple, 1-element tuple, empty gens, empty T0, negative label
     `(1,-2)`, denominator 1, score 0 — plus 60 LCG-generated ones) and echoes
     both the inputs and the produced lines.  cycles8's HITOBJ string is an
     inline `format!` inside `cycles8::run`, so that one expression is copied
     character-for-character into `fmtdump` and is marked `HITOBJ_INLINE`; it is
     the only shape here not pinned to a function call.
  c. `fmtcheck.py` reads those echoed inputs, locates each driver's `print(...)`
     call **with `ast` in `src/g2_tall.py`, `src/cycles8.py`, `src/rzero.py`
     and `rust/oracle_drivers.py`**, and `exec`s the extracted source with the
     reconstructed locals, capturing stdout.  No format string is retyped by
     hand anywhere in the harness; the stderr log prints the five statements it
     extracted so the extraction can be audited.

Result:

    /usr/bin/python3 rust/refute/search/r5-hitpaths/fmtcheck.py \
        rust/refute/search/r5-hitpaths/out/fmtdump.rs.txt
    -> fmtcheck: 325 formatted lines compared, 0 mismatches

(65 cases x 5 shapes.)  Covered by that: `Fraction.__str__` vs `Frac::Display`
including denominator 1; `repr(Fraction(n,d))` inside a tuple; the 1-tuple
comma `((0, 0),)`; the empty tuple `()`; `repr` of the generator list
`[(0, (1, -2))]`; `json.dumps(..., default=str)` separators and nested
tuple->array conversion; `f"{float(sc):.4f}"` vs Rust `{:.4}`; the six-space +
`print` separator prefix of stacked's line; the implicit-concatenation seam in
g2_tall's, cycles8's and rzero's f-strings.

One residual gap this does NOT close: it checks the formatters, not the call
sites — that the driver passes `labs` (not `labels`), `sorted(T0)` (not `T0`),
the right `t`, and appends in the right order.  Those remain pinned only by the
Rust unit tests.

Note on `f4`: Rust `{:.4}` and Python `:.4f` could disagree on an exact
half-way case at the 5th decimal.  That needs `2*num*10^4/den` odd with
`gcd(num,den)=1`, i.e. `den` divisible by 32.  Every score in these drivers has
`den = n - t <= 16`, so no reachable score is a tie.  No divergence here.

## 5. End-to-end driver comparisons run this session (all PASS)

All Python runs in this section are `KAKEYA_PURE_PY=1` (**pure-Python kernel**,
no PyO3), so these are kernel-independent.  Rust `--threads 1`.

| id | command pair | verdict |
|---|---|---|
| G1 | `oracle_drivers.py g2-tall 1 0` vs `g2-tall --rows 1 --max-t 0` | RESULT identical after masking `seconds` and stripping the 3 documented Rust-only keys |
| G2 | `oracle_drivers.py g2-tall 1 1` vs `g2-tall --rows 1 --max-t 1` | same |
| D1 | `cycles8_one.py 3 67/40 1` vs `cycles8 --pool 3 --target 67/40 --deg 1` | **byte-identical**, `0 presence patterns are 1-regular with m = 8` + RESULT |
| D3 | `cycles8_one.py 3 67/40 3` vs `... --deg 3` | byte-identical |
| D4 | `cycles8_one.py 3 67/40 4` vs `... --deg 4` | byte-identical |
| Z1 | `rzero_one.py 2 4 - 0` vs `rzero --d 2 --pool 4 --seed 0` | identical (n=2, 1 slot, 5 labels) |
| Z2 | `rzero_one.py 3 3 - 0` vs `rzero --d 3 --pool 3 --seed 0` | identical (16 labels) |
| Z3 | `rzero_one.py 4 6 - 0` vs `rzero --d 4 --pool 6 --seed 0` | identical (343 labels) |
| Z4 | `rzero_one.py 2x2 8 - 0` vs `rzero --d 2x2 --pool 8 --seed 0` | identical (POOL8, 729 labels — POOL8 was not in the coverage map) |
| Z5 | `rzero_one.py 1 4 - 0` vs `rzero --d 1 --pool 4 --seed 0` | identical (n=1, 1 label tuple) |
| Z6 | `rzero_one.py 2x2x2 8 200 5` vs `rzero --d 2x2x2 --pool 8 --limit 200 --seed 5` | identical (MT19937 sampler over a **9-element** alphabet — POOL8 sampling was not in the coverage map) |
| Z7 | `rzero_one.py 2x2x2x2 8 300 3` vs `--d 2x2x2x2 --pool 8 --limit 300 --seed 3` | identical |
| Z8 | `rzero_one.py 2x3 5 150 7` vs `--d 2x3 --pool 5 --limit 150 --seed 7` | identical (POOL5) |
| Z9 | `rzero_one.py 3x3 8 120 11` vs `--d 3x3 --pool 8 --limit 120 --seed 11` | identical |

One further comparison, **driver-level only — the Python side ran the PyO3
(Rust) kernel**, i.e. the kernel is held fixed and only the driver port is
tested (I had no cheaper way: the pure-Python cost of this configuration is
well past this session's budget):

| id | command pair | verdict |
|---|---|---|
| S3 | `r3/stacked_one.py 3 0 7/4` (PyO3 kernel) vs `stacked --pool 3 --max-t 0 --threads 1` | identical after masking the `[Ns]` bracket: `best 7/4 (1.75)`, witness `((0, 0), (0, 0), (0, 0), (0, 0)) m=8 r=6 t=0 T0=[]`, `hits: 0`.  112.1 s py / 95.2 s rs, both contended. |

S3 is also the empirical confirmation of §2's monotonicity argument: POOL3's
minimum is exactly 7/4, as predicted, so its hit list is empty.

`cycles8_one.py` is a shim exposing `deg`.  Shim audit: `deg` occurs in
`src/cycles8.py` only at lines 36 (the `main` signature), 48 (`v == deg`) and
50 (the printed message); all three read the parameter, there is no separate
literal, so nothing else had to change.  `tlimit` is left at `oracle_drivers`'
own `BIG = 1e9`, and the print block is copied from `oracle_drivers.py`'s
cycles8 branch unchanged.  `rows=1` for g2-tall (`d = [2,1]`, zero free level-2
slots) is a genuinely new configuration on both sides.

## 6. Minor: `g2-tall --rows 1 --max-t 2` — Python raises, Rust returns 0

`max_t = n` is a known out-of-contract edge (recorded for `scan` as
"Python ZeroDivisionError exit 1 vs Rust panic exit 101").  The g2-tall
instance behaves differently from the recorded scan instance and is worth one
line in the record: here Rust does not error at all.

    cd src && KAKEYA_PURE_PY=1 /usr/bin/python3 ../rust/oracle_drivers.py g2-tall 1 2
      ZeroDivisionError: Fraction(0, 0)                 (src/g2_tall.py:37)   EXIT=1
    kakeya-search g2-tall --rows 1 --max-t 2 --threads 1
      RESULT {"tag": "g2_tall_2x1", ..., "best": null, "hits": 0, "complete": true, ...}
      EXIT=0

Cause: at `t = n` the denominator `q = n - t` is 0.  Python evaluates
`Fraction(cap, q)` and dies; `g2_tall.rs::cap_for(0)` computes `cap = -1`, the
`budget < 0` guard fires and the loop simply skips that `t`.  Rust's behaviour
is arguably the more useful one, but it is a behavioural difference on an input
both CLIs accept, so it belongs in the known-limits list next to the scan case.
Files: `out/g2t_r1_mt2.py.txt`, `out/g2t_r1_mt2.rs1.txt`.


## 7. Negative control for the §4 harness

Injecting three mutations into the Rust dump (`Fraction(13, 8)` -> `Fraction(13,8)`,
`"2"` -> `"2/1"` in a HITOBJ, and dropping the 1-tuple comma in
`((0, 0),)`) makes `fmtcheck.py` report **11 mismatches** instead of 0, naming
each case and tag.  So the 0 in §4 is a real 0, not a harness that compares
nothing.

    sed 's/Fraction(13, 8)/Fraction(13,8)/; s/^C8H \["2",/C8H ["2\/1",/; \
         s/labels=((0, 0),)/labels=((0, 0))/' out/fmtdump.rs.txt > out/fmtdump.mutated.txt
    /usr/bin/python3 fmtcheck.py out/fmtdump.mutated.txt
    -> fmtcheck: 325 formatted lines compared, 11 mismatches

## 8. Hit ORDER and tie-breaks

The lens asks for order, not just counts.  Ordering is not per-driver: all five
drivers push `HitRec { index, .. }` into `ChunkOut` and the merge in
`engine.rs::absorb` (lines 112-138) re-orders by enumeration index, which is
what makes output thread-independent.  `scan` uses the same `engine::run` and
the same `HitRec`, and r3's F5 compared 1338 HIT + 1338 HITOBJ lines in order
against pure Python.  So the ordering machinery *is* covered end to end; what
is not covered for the other four drivers is only which object each pushes.
I found no way to separate those two with the drivers as shipped.

## 9. Machine note (not a finding, but it belongs in the record)

I signalled no process at any point (no `kill`, `pkill`, `killall`, or any
signal-sending command appears in this session's history).  For the record:
`ps` at 16:42 EDT showed pid 12158 (`./target/release/ks8run cycles8 --pool 6
--target 67/40 --deg 2 --patterns 8cycle --threads 10 --tlimit 36000`) alive at
59.2% CPU with ELAPSED 01:40:22; `ps -eo pid,command` at ~16:58 EDT no longer
listed it.  pid 13369 (the pure-Python POOL3 oracle) was still alive at 16:58,
ELAPSED 01:47:30.  At 16:58 the machine was also running four other agents'
`kakeya-search` jobs plus a `rustc` build under `improve/perf/kperf`, load
average 47.  I could not locate a stdout file for 12158 to say whether it
completed or died.

--------------------------------------------------------------------------
## Files

    reach.py            rzero column-sum invariant + a rank-bound scan
    reach2.py           stacked reachability under the driver's own P3/P4/P6
    cycles8_one.py      oracle shim exposing cycles8.main's `deg`
    fmtcheck.py         ast-extracted Python print statements vs Rust formatters
    tmo.py              wall-clock cap helper (no `timeout(1)` on this machine)
    out/fmtdump.rs.txt  the Rust formatter dump (65 cases x 5 shapes)
    out/fmtcheck.txt    "325 formatted lines compared, 0 mismatches"
    out/fmtcheck.stderr.txt   the five extracted Python print statements
    out/check_audited_t2.txt / out/check_copy_t2.txt
    out/g2t_r1_mt{0,1,2}.{py,rs1}.txt
    out/c8_deg{1,3,4}.{py,rs1}.txt
    out/rz_*.{py,rs1}.txt, out/rzs_*.{py,rs1}.txt (+ .norm)
    out/st_p3_mt0.{rs1,py_rskernel}.txt
    out/fmtdump.mutated.txt   the negative control input
    ../../improve/r5-hitpaths/   copied crates + src/bin/fmtdump.rs (build only)

Nothing under `crates/`, `src/`, `logs/`, `tests/`, `results.json`,
`RESULTS-RUST.json`, `PROGRESS.md`, `REPORT.md` or `KAKEYA-WORKBENCH.md` was
modified.  No process was signalled.
