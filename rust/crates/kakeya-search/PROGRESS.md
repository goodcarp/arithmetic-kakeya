# kakeya-search — progress

State at session resume (task B2, third attempt; first two were interrupted).

## Inherited and verified working
- `cargo build --release -p kakeya-search`: clean.
- `cargo test --release -p kakeya-search`: 16/16 pass (measured 2026-09-06; the "12/12" this line carried until then was a stale count from an earlier revision of the suite).
- `./target/release/kakeya-search check --threads 12`: 14 PASS, 2 SKIP, 0 FAIL over 16 fixtures (measured 2026-09-06 at `--threads 1` and `--threads 12`; the earlier "11 PASS" was stale).

## Files
- `src/frac.rs`     exact Fraction semantics (i64 num/den, i128 compare, mul_int_floor = int(target*k))
- `src/graph.rs`    ZERO/pools, domains, slots_of, mult, Graph::{from_labels,fill,vertices,index}, build_rows, gen_row, m_of_labels
- `src/search.rs`   indep_dirs, local_requirement, dir_choices, min_generators (+ extend DFS)
- `src/common.rs`   Worker scratch, combinations, LabelSource (Exhaustive/Sampled), alphabet_of, score
- `src/pyrandom.rs` CPython MT19937 init_by_array + choice
- `src/engine.rs`   rayon outer-loop parallelism, index-ordered merge, Stop deadline
- `src/fmt.rs`      Python repr / json.dumps renderings
- `src/drivers/`    scan, g2_tall, cycles8, stacked, rzero
- `src/check.rs`    the cheap-fixture gate
- `src/main.rs`     CLI

## Remaining work in this session
1. cargo clippy -- -D warnings
2. check --threads 1 vs --threads 12 byte-diff
3. Python n4_p6_t1 vs Rust scan stdout diff (ignoring seconds)
4. bench numbers

## Done this session (2026-09-05)
- clippy: kakeya-search had 7 lints (needless_range_loop x3 in the drivers'
  `for t in 0..=max_t` / `combos[t]`, unnecessary_map_or x2 in search.rs,
  needless_late_init in engine.rs, bool_assert_comparison in tests.rs) -> all
  fixed by hand.  kakeya-core had 2 lib lints (incompatible_msrv on div_ceil ->
  rust-version bumped 1.70 -> 1.73; needless_range_loop on the pivot search ->
  #[allow] with a comment, the indexing is deliberate) and 38 test lints ->
  `cargo clippy --fix`.  `cargo clippy --release --all-targets --workspace --
  -D warnings` is now CLEAN.  kakeya-core still 62/62, kakeya-search 16/16 (12/12 as of that clippy pass; the suite has since grown).
- check --threads 1 vs --threads 12: identical modulo the per-fixture [Ns].
- scan n4_p6_t1: Rust --threads 1 vs --threads 12 byte-identical except
  "seconds"; Rust vs KAKEYA_PURE_PY=1 Python scan1.py: 241/241 lines identical
  except "seconds" (120 HIT + RESULT + 120 HITOBJ).
- scan sampled path (--limit 500 --seed 11, d=2x2 POOL6): 329/329 lines
  identical except "seconds" -> the MT19937 port is right end to end.
- rzero: all 5 sweeps ([2,2]/P6, [2,3]/P4, [3,2]/P4, [2,2,2]/P4,
  [2,2,2]/P6 lim 60000) identical except "seconds".
- g2-tall rows=3 max_t=0 and max_t=1 vs oracle_drivers.py: identical
  (best null, hits 0 -- weak, the cap excludes 11/6 itself).
- --tlimit smoke: g2-tall prints "  [2x5] TIME LIMIT" + complete:false;
  cycles8 prints "TIME LIMIT"; scan reports scanned<total + complete:false.

## In flight
- Python oracles running (with the Rust fastcore kernel, which B1 proved
  bit-identical, so they finish in minutes not hours):
  g2-tall 4 1, cycles8 3, stacked 4 1.  Compare when they land, then embed
  the results as extra `check` fixtures.

## Landed after the in-flight oracles came back
- stacked POOL4 max_t=1 vs `oracle_drivers.py stacked 4 1`: identical except
  the `[Ns]` elapsed.  best 7/4, witness `((0,0),(0,0),(0,0),(0,0)) m=8 r=6
  t=0 T0=[]`, 0 strict hits -- the SAME witness the recorded max_t=2 fixture
  reports, and it is a genuine TIE-BREAK test: many interfaces reach 7/4 and
  Python reports the first (enumeration index 0); the 12-thread Rust run
  reproduces exactly that.
  **Disclosure, added 2026-09-06 (record lens R2, upheld on adjudication).**
  The Python side of this comparison ran on the PyO3 kernel AND both Python
  artifacts named for it are 0 bytes (`refute/search/py_stacked_p4_t1_rskernel.txt`,
  `py_stacked_p4_t0.txt`, Sep 5 18:07).  No Python stacked max_t=1 output
  exists anywhere in the tree.  So the sentence above records a comparison
  whose Python side does not exist on disk.  Every number in it IS supported,
  by the max_t=2 comparison: the concatenation `logs/rust-stacked_pool4.log`
  + `logs/rust-stacked_pool6.log` vs the pure-Python `logs/stacked.log`,
  md5-equal with `[Ns]` masked (r3 sec 1; the two files are not md5-equal
  individually).  And max_t is degenerate here: the witness is at t = 0 and
  `best` updates only on strict improvement, so max_t = 0/1/2 give the same
  output (adjudication FINDING-08 measured it at POOL3).  See the coverage-map
  row.
- cycles8 POOL3 vs `oracle_drivers.py cycles8 3`: BYTE-IDENTICAL (this driver
  has no `seconds` field) -- `5 presence patterns are 2-regular with m = 8`
  then `RESULT {"tag": "cycles8", "pool": 3, "best": null, "hits": 0,
  "tested": 29004}`.  The `tested` counter agreeing to the unit is the
  strongest single-number check on the whole pruning chain.
  **Kernel disclosure, added 2026-09-06 (corrected the same evening, record
  lens R1).**  The Python side of this comparison did not run pure Python --
  and it was NOT the only such row, as the first version of this paragraph
  wrongly said: the "In flight" section above already states that three
  oracles (g2-tall 4 1, cycles8 3, stacked 4 1) ran on the Rust kernel, and
  all three became coverage-map rows without the map saying so.  The map now
  says so, row by row.
  The completed oracle is `refute/search/py_cycles8_p3_rskernel.txt` -- the
  filename says so -- i.e. `cycles8.main` driven by the PyO3 (Rust) kernel.
  The pure-Python attempt of the same run, `refute/search/py_cycles8_p3.txt`,
  is 45 bytes: the header line only, killed before it printed a RESULT.  So
  what this row establishes is that the Rust cycles8 DRIVER reproduces the
  Python cycles8 driver with the kernel held fixed; it is not an independent
  check of the kernel.  That is not a hole -- the kernel is covered separately
  and directly by `difftest.py` (54,406 pure-Python-vs-Rust comparisons) and
  by the 119 trap cases (`traps.json`, which already contains VERIFIED.md's
  17 `v`-prefixed entries; the "135" written here earlier double-counted
  them -- record lens R6) -- but "byte-identical to the Python driver" reads
  stronger than what was run, and the map did not say which kernel was under
  it.  Two refuters brushed against this (the `_rskernel` filename, and r3's
  own opening sentence in its section 6) and neither closed it; r3 then
  titled that section "re-verified against a PURE-PYTHON oracle" while its
  own `out/C8.py.txt` was again 45 bytes and its Python side never returned.
  A pure-Python POOL3 oracle IS feasible: measured 2026-09-06 at 5.22 pairs/s
  on a contended machine (779 pairs in 149 s, `refute/search/r4/rate_c8.py`),
  so 29,004 pairs needs about 93 minutes of CPU -- not the ~36 h that a naive
  extrapolation from the POOL6 rate (0.22 pairs/s) suggests, because POOL6
  pairs are far more expensive.
  **CLOSED 2026-09-06 17:38 EDT.**  r3's orphaned pure-Python run
  (`py_drv.sh C8 cycles8 3`, `KAKEYA_PURE_PY=1`, started 15:10) finished:
  `refute/search/r3/out/C8.py.txt` =
  `5 presence patterns are 2-regular with m = 8` /
  `RESULT {"tag": "cycles8", "pool": 3, "best": null, "hits": 0, "tested": 29004}` /
  `EXIT=0` -- byte-identical to `C8.rs1.txt` and `C8.rs12.txt`.  The cycles8
  POOL3 row is now a genuine pure-Python-vs-Rust end-to-end comparison.
- New `check` gates: an FNV-1a-64 digest over the whole 120-line n4_p6_t1
  HITOBJ stream (not just first/last), and the two g2_tall 2x3 runs.
- The five driver progress lines that NO recorded run exercises (every logged
  run has `best null`) are now pinned by `driver_progress_lines_match_python`,
  whose expected strings were produced by evaluating the drivers' own
  f-strings under /usr/bin/python3.  The builders were extracted into
  `progress_line` / `hit_line` fns so the test calls the same code the driver
  does, not a second copy of the format string.

## Known limits (report these)
- `--tlimit` makes output thread-count dependent (which item trips the
  deadline is a wall-clock race, exactly as in Python).  Without `--tlimit`
  output is byte-identical for any `--threads`.
- With `--tlimit` set, progress lines are buffered and printed after the run
  instead of streaming, because a line can only be published once the global
  cut-off index is known.
- `g2_tall` RESULT emits `complete: !time_limit_tripped`; the Python emits the
  hardcoded `(el < 700)`.  They agree except for a run given `--tlimit > 700`
  that finishes between 700 s and the limit.
  Scope, added 2026-09-06: the shipped `g2_tall.py` `__main__` calls
  `run(rows_, max_t=1, tlimit=700)` with the 700 hardcoded in BOTH places, so
  for every run that driver can actually perform, `el < 700` is a correct
  completeness test and the only disagreement is the `--tlimit > 700` case
  above.  A refuter (r3) reported the opposite -- "they disagree for every
  tripped run whose elapsed is under 700 s" -- but that came from its own
  `g2tall_tl.py` shim, which makes `tlimit` settable while copying the literal
  `(el < 700)` verbatim.  Lowering the limit without lowering the constant
  manufactures the divergence.  Same harness-artefact class as that refuter's
  own retracted seed-11 finding: when you parameterise a value, parameterise
  every constant that refers to it.

## Coverage map (what each comparison actually proves)
| comparison | Python oracle | verdict |
|---|---|---|
| scan n4_p6_t1 (343 exhaustive) | `scan1.py` KAKEYA_PURE_PY=1 | 241/241 lines identical exc. seconds; 120 witnesses |
| scan sampled 500 seed 11 | `scan1.py` | 329/329 identical -> MT19937 port correct |
| scan k=1 box `--d 6` | `scan1.py` | **UNSUPPORTED ON DISK** (record lens R3, 2026-09-06): the sweep config that would produce it, `configs.txt` `c12 6 6 1 2 -`, has a 0-byte Python output (`sweep/c12.py.txt`); the only `--d 6` RESULT lines in the tree are Aug-24 incomplete Python prefixes with no Rust counterpart.  Re-run before citing. |
| scan 3-level sampled `--d 2x2x2` | `scan1.py` | **UNSUPPORTED ON DISK** (R3): configs `s17b`/`s18`/`s19` were listed and never run; no scan-driver `--d 2x2x2` RESULT exists under `refute/`.  Re-run before citing. |
| rzero x5 sweeps | `rzero.sweep` | all identical exc. seconds |
| g2-tall 2x3 t0/t1 | `g2_tall.run` | identical |
| g2-tall 2x4 (the Tier-3 target) | `g2_tall.run` **on the PyO3 kernel** (`py_g2tall_2x4_rskernel.txt`; disclosed 2026-09-06, R1) | driver-level identical exc. seconds and `complete` (Python's hardcoded `el < 700`); kernel held fixed, so this row does not independently check the kernel |
| stacked POOL4 max_t=1 | `stacked.run` on the PyO3 kernel -- **Python-side artifact is 0 bytes** (`py_stacked_p4_t1_rskernel.txt`; R2) | as a SEPARATE max_t=1 comparison, UNSUPPORTED on disk.  The substance (best 7/4, all-ZERO witness, 0 strict hits, tie-break) IS supported by the max_t=2 comparison: the CONCATENATION `logs/rust-stacked_pool4.log` + `logs/rust-stacked_pool6.log` vs the pure-Python `logs/stacked.log`, md5-equal with `[Ns]` masked (r3 sec 1; not equal file-by-file). |
| cycles8 POOL3 | `cycles8.main` -- PyO3-kernel oracle on 09-05, **pure-Python oracle landed 2026-09-06 17:38** (`refute/search/r3/out/C8.py.txt`, `KAKEYA_PURE_PY=1`) | BYTE-identical at `--threads 1` and `12`, incl. `tested: 29004`.  A genuine end-to-end pure-Python-vs-Rust comparison as of 09-06. |
| progress-line formats | CPython f-strings | pinned by a unit test |
| the four never-fired hit paths (g2_tall improvement line, cycles8 HITOBJ, stacked `h[:5]`, rzero forcing-object line) | CPython executing the drivers' OWN print statements, extracted with `ast` (r5-hitpaths `fmtcheck.py`) | 325 formatted lines, 0 mismatches; negative control with 3 injected mutations catches 11.  No configuration of these four drivers produces hits > 0 (rzero: unreachable for every input by the edge-row column-sum invariant, = P7; stacked: empty for POOL3-6 at EVERY max_t -- pool monotonicity on the complete POOL4/6 runs for t <= 2, and for t >= 3 because m >= 8 makes t >= 4 budget-infeasible while t = 3 forces m = 8, r = 0, which 0 of the 56 3-subsets achieve (adjudication FINDING-03); POOL8 is the one open arm, run 2026-09-06 late evening, see below; g2_tall: nothing beats the 11/6 cap **at t <= 1, the only range any run ever searched** -- t = 2, 3, 4 are inside the cap with large budgets and were never searched, see Known limits), so formatter-level is the strongest check available for those paths. |
| scan `--seed` at 9 seeds (0, 1, 11, 123, 2^32-1, 2^32, 2^32+1, 1.23e19, 2^64-1) | `scan_seed.py` (self-checked byte-identical to `scan1.py` at seed 11 first) + `rzero_one.py` | 9/9 identical at `--threads 1` and `2`, 63-78 HITOBJ per run (external r5).  Before this, `--seed` had no oracle at any value but 11. |
| kernel wide sweep | pure-Python `force`/`rank` | 557,055 in-contract comparisons, 0 mismatches, entries to +-2^63, moduli to 2^32+-1 (external r5) -- ~10x difftest.py |
| 15 new end-to-end driver comparisons (g2-tall rows 1-4, cycles8 deg 1/3/4 and targets 7/4, 15/8, 2 via `--patterns 4`, stacked POOL3, rzero d=1..4) | 14 of 15 pure-Python | all identical (r5-hitpaths) |

## Bench (idle machine, 12 logical / 6 physical cores)
n4_p6_t1: pure Python 19.2 s | Rust --threads 1 1.18 s (16.3x) | --threads 6
0.24 s | --threads 12 0.16 s (120x).
g2_tall 2x4: Rust --threads 12 49.6 s (Python with the B1 PyO3 kernel took
1246.6 s on a busy machine; the pure-Python estimate in the S2 contract was
~3073 s).

## 2026-09-06 follow-ups (after the run_targets.sh campaign)

Three changes, all gated: `cargo test --release --workspace` 78/78 (was 75),
`cargo clippy --release --all-targets --workspace -- -D warnings` clean,
`check --threads 1|12` PASS, the refuter's scan sweep against the stored Python
norms (the "30/30" first written here is not an on-disk count: 29 configs have
artifacts, 28 with a non-empty Python side, and a 2026-09-06 recount gives
25 PASS / 1 FAIL -- record lens R4/R5) (s09 is the pre-existing Python-side `ZeroDivisionError`), cycles8
POOL3 stdout byte-identical to the pre-change binary, g2_tall 2x3/2x4
byte-identical up to and including `seconds`.

1. `min_generators` (search.rs): the base rows are materialised ONCE per call
   into buffers recycled from `row_pool`; the old per-combo pop-all + clone was
   the row_pool free-list leak (`refute/search/finding_rowpool_leak.txt`).
   Refuter mem config (`scan --d 2x2x2 --pool 8 --max-t 0 --target 2 --threads 1
   --tlimit 25`): max RSS 1,634,877,440 -> 995,328 bytes at the same `scanned`
   822; sys time 12.3 s -> 1.0 s.  (The 2x6 target run on 2026-09-06 peaked at
   6.3 GB on 8 threads under the old code.)  CPU time is UNCHANGED: cycles8
   POOL3 `--threads 4` = 200.1 s user before, 199.3 s after.  A 20 s `sample`
   of cycles8 POOL3 at `--threads 1` puts 95% of working samples inside
   `kakeya_core::force` itself (13,969 of ~14,700; malloc/free/bzero/memmove
   ~500 together; `search::extend` 74), so the ~2.6x-per-core gap against the
   pure-Python driver is the kernel's per-call cost on these tiny matrices
   (full B-matrix rebuild + RREF per call in the fixpoint loop), not the DFS
   bookkeeping.  The next lever is inside `force` (incremental elimination
   over the unchanged base rows), which is a kernel change and needs its own
   differential gate.
2. `g2_tall` RESULT carries three Rust-only trailing keys after `seconds`:
   `walked`/`total` (label tuples, `scan`'s `count` semantics) and `pairs`
   ((graph, T0) pairs handed to `min_generators`, counted where cycles8 counts
   `tested`).  Gated against Fable's independent
   `adversary-fable/count_pairs.py`: 2x3 = 1587 (t = 0 buckets 237), 2x4 =
   31718; a complete 2x5 should read 672719 and 2x6 13183980.  Diff against a
   Python log by stripping the tail.
3. `cycles8 --patterns 8cycle|4+4|i,j,...`: restricts the outer enumeration to a
   subset of the five presence patterns (product order kept), prints a pattern
   table with cycle types (indices 0, 1, 4 = two 4-cycles; 2, 3 = single
   8-cycles, cross-checked against `cycles8.build` in Python) and records the
   selection as a trailing `"patterns"` key.  Default output is byte-identical
   to the Python.  POOL3: `8cycle` tested 3948 + `4+4` tested 25056 = 29004 =
   the full run.  The two-4-cycle patterns (settled by the direct-sum / mediant argument on the complete `n4_p6_t1` scan, PREDICTIONS sec 2.2 -- NOT by Lemma C, which is the prune on the 8-cycle side; record lens R10) hold 1,823,760 of
   POOL6's 1,905,420 pairs, so the run that matters is
   `kakeya-search cycles8 --pool 6 --patterns 8cycle` (81,660 pairs; about
   5 h at the 4.6 pairs/s the 2026-09-05 POOL6 run sustained on 8 threads).

## Known limits — additions from the closing audit (C6, 2026-09-06)
- FIXED and REBUILT 2026-09-06 (binary sha256 add55418…, `check` 14/0; `--d 65` now refuses with "exceeds u64"): `LabelSource::total` used an unchecked `pow`; on a box with >= 65 vertices it wrapped and a RESULT line could say `complete: true` for an index space never scanned. Now `checked_pow` with a loud panic.
- OPEN (still live against the rebuilt binary; re-measured 2026-09-06 after the `checked_pow` fix): `--tlimit` on a very large index space aborts with a memory allocation failure instead of returning a RESULT (chunk list proportional to the index space, `engine.rs:213-220` collects all `total/4096` chunks eagerly).  The C6 fix changed the boundary but did not close this: a config whose `total` exceeds u64 now refuses loudly, while a config whose `total` fits u64 and whose chunk count is still astronomic aborts as before.  Measured on `--d 2x2x2x2x2 --max-t 0 --target 7/4 --tlimit 2 --threads 1`: `--pool 4` (5^31 > u64) panics "exceeds u64; refusing to run (audit C6)", exit 101; `--pool 3` (4^31 = 4611686018427387904, fits u64) still fails to allocate 81064793292668928 bytes, exit 134.  The smallest live repro is therefore `--pool 3`, not `--pool 8`.  Python returns normally on both (its `total` is a bigint and enumeration is lazy).  Needs streaming chunk enumeration.
- OPEN: `--tlimit` is not a bound on wall time below the threshold — chunk enumeration cost is proportional to the whole index space (5 s limit -> 120 s wall on `2x2x2x2 POOL4`).
- Recorded: progress lines are buffered under `--tlimit`; `g2-tall` prints an honest `complete` where Python hardcodes `el < 700`; a run killed by SIGTERM (e.g. a stray `pkill -f kakeya-search`) leaves no RESULT line — run long jobs under a distinct binary name.

## 2026-09-06 evening — sweep r5 (seven lenses) and the two long runs

Triage record with every verdict: `rust/refute/SWEEP-2026-09-06.md`.  Lens
reports: `refute/search/r5-hitpaths/`, `refute/external/r5/`,
`refute/record/r5/`, `refute/kernel/r5/`, `refute/science/r5/`,
`improve/perf/`, `improve/robustness/`.

### The 8-cycle cross-check is COMPLETE
`ks8run cycles8 --pool 6 --target 67/40 --deg 2 --patterns 8cycle --threads 10
--tlimit 36000`, 19:02:26Z -> 20:46:00Z, exit 0:
`RESULT {"tag": "cycles8", "pool": 6, "best": null, "hits": 0, "tested": 81660, "patterns": [2, 3]}`.
81,660 = 1,905,420 - 1,823,760, the full 8-cycle pair count; no TIME LIMIT.
6,214 s at 10 threads = 13.1 pairs/s; the "about 5 h" estimate above was ~3x
high (8-cycle patterns carry 1,296 labels each, not 46,656).  This confirms
Fable's `cycle8_cheap` + `cycle8_r5` side computation by a different route (no
Lemma C prune).  Ran on the 15:02 `ks8run` copy, which predates the
`checked_pow` rebuild -- irrelevant to this input (no overflow path), but it is
not the audited sha.  Recorded in `RESULTS-RUST.json` as run 6.

### cycles8 searches t <= 2 only; the t = 3 phase was inside the target (science r5, F1)
Both implementations hardcode the phase loop (`src/cycles8.py:62` `for t in
(0, 1, 2)`; `drivers/cycles8.rs:195` `(0..=2)`).  At POOL6 / 67/40 / n = 8,
`t = 3` gives den 5, budget `int(67/40*5) - 8 = 0`, so `r = 0` and the score
would be **8/5 = 1.600 <= 1.675** -- a hit, never searched.  `t = 4` is
budget-infeasible.  So every "cycles8 POOL6 closed" sentence before today was
silently scoped to `t <= 2`.
**Closed 2026-09-06** by `refute/science/r5/t3_check.py` (pure Python,
`KAKEYA_PURE_PY=1`; r = 0 so no DFS, just `force` on every (graph, 3-subset T0)
with the P4 prune): 8-cycle patterns 2,3 -- 2,592 graphs, 87,600 pairs, 0 hits;
two-4-cycle patterns 1,4 -- 7,992 graphs, 236,400 pairs, 0 hits.  Both
reproduced independently the same evening -- first at 13.6 s / 33.2 s wall, which adjudication FINDING-01 showed is below the pure-Python CPU floor, i.e. those two reproductions had the PyO3 kernel loaded despite the env var (cause unexplained; the switch was verified working afterwards); re-run with `assert fastcore.force is fastcore._force_py` inside the same process: 23.9 s / 62.6 s wall, 22.3 s / 56.9 s CPU, identical counts.  Pattern 0 (46,656 graphs): 1,368,000 pairs, 0 hits, 567 s pure Python (`refute/science/r5/t3_idx0_purepy.txt`). t = 3 total: 1,692,000 (graph, T0) pairs over all five patterns, 0 hits -- closed by computation, the component-split argument is no longer load-bearing. (The lens's component-split argument -- any split of t = 3 over two
4-cycle components leaves one with t_i <= 1 -- reached the same conclusion first.)
Net: cycles8 POOL6 is closed at every t -- 8-cycles at t <= 2 twice (Lemma-C
side computation + the Lemma-C-free complete Rust run), at t = 3 exhaustively;
two-4-cycles at every t by mediant + t3_check.  It does NOT mean "n = 8
closed": cycles8 covers 6.95% of the 2x2x2 POOL6 label space (only m = n = 8
with every degree exactly 2), and `--deg` is vacuous for every value but 2.

### Known limits -- additions
- `scan --tlimit 0`: Rust treats it as a 0 s limit (stops after one item);
  Python's `if tlimit and ...` (`search.py:209`) treats 0 as no limit.  An
  in-contract CLI input no driver passes.  OPEN; fix = treat 0 as none at the
  next rebuild.  (external r5)
- `g2-tall --rows 1 --max-t 2` (max_t = n): Python raises `ZeroDivisionError`
  (den = 0), Rust prints a clean RESULT.  Outside the driver's contract (rows
  in {4,5,6}); same class as sweep s09.  (r5-hitpaths)
- `fastcore_rs.force` reads `rows` by iteration where the Python subscripts:
  a `dict` or list-subclass `rows` gives a silent wrong value.  No driver
  passes such rows.  Scope note on the bit-exactness claim, not a recorded-run
  issue.  (external r5)
- The shipped `src/fastcore_rs.abi3.so` (sha256
  `03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b`, built
  2026-09-04 16:10) predates the last `kakeya-core` source edit (09-05 17:32)
  by 25 h.  A fresh build after that edit (`refute/boundary/fresh/`,
  `04d848f8...`) shows no behavioural drift (kernel r5).  Rebuild, re-copy and
  re-pin the sha at the next kernel change.
- `boundary/t_wiring.py` exits 1 on a stale assertion encoding an
  already-fixed defect; `control/` and `boundary/` never wrote a verdict file.
  (kernel r5)

### Improvements PROPOSED (built and gated in copies; NOT adopted -- adoption = rebuild + full regate)
- `improve/perf/`: kernel prototype **4.7x faster** than the audited `force`
  with byte-identical stdout on scan n4_p6_t1 and cycles8 POOL3/POOL4 8cycle.
  Levers: p = 2^31-1 is a Mersenne prime so `% p` is shift-and-add (2.55x
  alone); the pivot inverse `pow(a, p-2, p)` is ~80% of the modular multiplies
  and memoising it gives a further 1.7-1.9x.  Differential: 27,951 cases vs
  the PURE-PYTHON `force` (moduli 2^31-1, 1e9+7, 91, 97, 7; exceptions
  included), 0 mismatches in every kernel mode; the audited kernel replayed on
  the same corpus also 0.  Lever C (carry the RREF across warm-started calls)
  unspent, est. 2-3x more.  Correction to the record: step-4 membership is
  already O(|U|*2*w), so that shortcut is worth ~8%, not 1.6x.
- `improve/robustness/`: streaming chunk enumeration in `engine.rs`
  (+58 -14): `check` identical to the audited binary at 1 and 12 threads; r3
  fixtures 15/15 byte-identical; workspace 78/78 + clippy clean; the
  `--d 2x2x2x2x2 --pool 3` abort now RETURNS a RESULT (2.03 s, 1.26 MB RSS);
  `--tlimit 5` honoured at 5.01-5.02 s on every index space tested.  Residual
  overshoot is per-item DFS cost, present identically in Python.  Proposal for
  g2_tall: keep the three Rust-only keys, add `--python-compat` rather than
  flipping the default.

## Known limits and closures — additions from the adjudication + critic (2026-09-06 late evening)
Source: `refute/adjudicate/r5/` (ten second-opinion refuters, one critic; all
ten lens findings upheld in substance except record R11, which was REFUTED --
see PREDICTIONS.md sec 7 and `refute/SWEEP-2026-09-06.md` sec G).

- **g2_tall searches t in {0, 1} only, and t = 2, 3, 4 are inside the 11/6 cap
  with large budgets** (critic item 1 -- the exact analogue of the cycles8
  t = 3 gap, one driver over).  `src/g2_tall.py:61` calls `run(rows_, max_t=1,
  tlimit=700)`; `rust/run_targets.sh` passes `--max-t 1`.  From the driver's own
  cap rule: rows=4 t=2 budget <= 6, t=3 <= 5, t=4 <= 3; rows=5 t=2 <= 9, t=3
  <= 7, t=4 <= 5; rows=6 t=2 <= 12, t=3 <= 10, t=4 <= 8.  Unlike cycles8's
  t = 3 (budget exactly 0), these are wide-open regions.  **Every g2_tall
  negative in this tree (2x4 complete, 2x5 and 2x6 time-limited) is a t <= 1
  statement.**  **2x4 CLOSED at every t, 2026-09-06 23:29-23:36 EDT**, on the audited
  binary: `g2-tall --rows 4 --max-t 4 --threads 4` -> complete, walked
  4096/4096, **139,050 pairs** (vs 31,718 at t <= 1), 0 hits, 305 s
  (`logs/rust-g2_tall_2x4_maxt4.log`); then `--max-t 6` -> complete, 0 hits,
  **the same 139,050 pairs**, 266 s (`logs/rust-g2_tall_2x4_maxt6.log`).  The
  feasible-t table computed from the driver's own cap + rank rule
  (`refute/adjudicate/r5/g2t4_feasible_t.txt`, m ranges 4..10 over the 4,096
  label tuples): t=0,1,2 all 4,096 tuples feasible; t=3 3,367; t=4 694;
  **t=5 19 (the critic's "t = 2, 3, 4" list missed it)**; t>=6 none.  The 19
  t=5 tuples all fell to the `mt > budget` local-requirement prune before any
  DFS (hence the unchanged pairs count), which is the driver's own logic and
  counts as searched.  2x5/2x6 at t >= 2 are out of reach at measured rates
  and stay scoped to t <= 1.
- **The g2_tall RESULT line hardcodes `"max_t": 1` on BOTH sides**
  (`src/g2_tall.py:63`, `drivers/g2_tall.rs:184`), so a `--max-t 2+` run
  mislabels itself.  Faithful port, not a divergence, but trust the log header
  (which records the real command), never the field.  Fix when the Python is
  next touched, or have Rust emit the real value alongside the three
  Rust-only keys.
- **stacked at every max_t**: POOL3-6 hit block provably empty at every t
  (FINDING-03, argument in the coverage map row).  **POOL8 at t <= 2 was the
  one open arm**; `stacked --pool 8 --max-t 2 --target 7/4 --threads 4` started
  2026-09-06 ~23:35 EDT -> `logs/rust-stacked_pool8.log`.
- **The matching-suffix reading is the right one -- the largest conditional on
  the campaign is DISPOSED** (FINDING-04).  The two readings do separate (456 of
  8,320 configurations on d=[2,2] are invalid under matching-suffix and valid
  under permissive at identical score), so 0-hit results do not transfer
  between them, as the science lens said.  But the smallest separating object
  (`f=[{(1,):(1,0)},{(1,1):(0,1),(2,1):(0,1)}]`, `T=[(2,1)]`,
  `R=[((1,1),(0,1))]`) is permissive-valid at score **5/3 = 1.6667 on FOUR
  vertices** -- below the Epoch target 1.675 and below gamma.  If permissive
  were the intended reading, the Epoch problem would be solved by a 2x2 box and
  Katz-Tao would not be a record.  So the campaign's reading is the only one
  consistent with the problem being open.  `KAKEYA-WORKBENCH.md` sec 1 still
  argues only hit-transfer; this is the missing negative-side sentence.
- **The cycles8 closure is target-specific**: at `--target 2` the same budget
  arithmetic makes t = 4 feasible (den 4, int(8) - 8 = 0, score 8/4), and
  `--target` is user-settable, so the hardcoded `t in (0,1,2)` is a scope
  defect for any target, not only 67/40 (FINDING-01).  cycles8 POOL8 (303,616
  tuples) and slope-modulus variation at n > 4 are unrun and are separate
  tasks, not part of this close-out.
- **Robustness adoption recipe** (critic item 4; adopt this one FIRST, perf
  second as its own task): apply `improve/robustness/engine.diff` to
  `engine.rs` ONLY and rewrite its line-219 comment ("a real wall-clock bound"
  is false -- the per-item DFS granularity floor remains, shared with Python);
  fold in `--tlimit 0` = no limit (matches Python) with a `check` fixture;
  rebuild, record the new sha; `check` 1|12 = 14/2/0 byte-identical after
  `[Ns]` masking; workspace 78; clippy clean; replay the 15 r3 fixtures through
  `r3/mynorm.py` (15/15); `scan n4_p6_t1` 241 lines; cycles8 POOL3 unmasked;
  stacked POOL4+POOL6 vs `logs/stacked.log` as a CONCATENATION; never-trip
  identity on >= 4 configs x {1,12} threads; the two closure gates (2x2x2x2x2
  pool 3 tlimit 2 returns; 2x2x2x2 pool 4 tlimit 5 honoured); state that
  difftest/traps need no re-run (kernel untouched); re-pin the sha in README
  (both places), here, RESULTS-RUST.json and the handoff; note that runs 3/4/5
  are time-limited prefixes that will NOT reproduce byte-for-byte under the new
  binary.  Provenance is already proven: FINDING-06 rebuilt from a different
  absolute path and got the audited sha from `engine.rs.orig` and `0a152c93...`
  from the shipped `engine.rs` -- the diff is necessary and sufficient.
- **Perf adoption** (second): changes `kakeya_core::force`, so it needs a new
  `.so` + difftest + the 119 traps re-run; take levers A + C' + D only (the
  membership shortcut B is invalid for composite p); the prototype's own REPORT
  sec 8 provenance sentence was false and is corrected.
