# kakeya-search — progress

State at session resume (task B2, third attempt; first two were interrupted).

## Inherited and verified working
- `cargo build --release -p kakeya-search`: clean.
- `cargo test --release -p kakeya-search`: 12/12 pass.
- `./target/release/kakeya-search check --threads 12`: 11 PASS, 2 SKIP, 0 FAIL.

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
  -D warnings` is now CLEAN.  kakeya-core still 62/62, kakeya-search 12/12.
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
- cycles8 POOL3 vs `oracle_drivers.py cycles8 3`: BYTE-IDENTICAL (this driver
  has no `seconds` field) -- `5 presence patterns are 2-regular with m = 8`
  then `RESULT {"tag": "cycles8", "pool": 3, "best": null, "hits": 0,
  "tested": 29004}`.  The `tested` counter agreeing to the unit is the
  strongest single-number check on the whole pruning chain.
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

## Coverage map (what each comparison actually proves)
| comparison | Python oracle | verdict |
|---|---|---|
| scan n4_p6_t1 (343 exhaustive) | `scan1.py` KAKEYA_PURE_PY=1 | 241/241 lines identical exc. seconds; 120 witnesses |
| scan sampled 500 seed 11 | `scan1.py` | 329/329 identical -> MT19937 port correct |
| scan k=1 box `--d 6` | `scan1.py` | identical |
| scan 3-level sampled `--d 2x2x2` | `scan1.py` | identical |
| rzero x5 sweeps | `rzero.sweep` | all identical exc. seconds |
| g2-tall 2x3 t0/t1 | `g2_tall.run` | identical |
| g2-tall 2x4 (the Tier-3 target) | `g2_tall.run` | identical exc. seconds and `complete` (Python's hardcoded `el < 700`) |
| stacked POOL4 max_t=1 | `stacked.run` | identical exc. elapsed; witness + tie-break reproduced |
| cycles8 POOL3 | `cycles8.main` | BYTE-identical, incl. `tested: 29004` |
| progress-line formats | CPython f-strings | pinned by a unit test |

## Bench (idle machine, 12 logical / 6 physical cores)
n4_p6_t1: pure Python 19.2 s | Rust --threads 1 1.18 s (16.3x) | --threads 6
0.24 s | --threads 12 0.16 s (120x).
g2_tall 2x4: Rust --threads 12 49.6 s (Python with the B1 PyO3 kernel took
1246.6 s on a busy machine; the pure-Python estimate in the S2 contract was
~3073 s).

## 2026-09-06 follow-ups (after the run_targets.sh campaign)

Three changes, all gated: `cargo test --release --workspace` 78/78 (was 75),
`cargo clippy --release --all-targets --workspace -- -D warnings` clean,
`check --threads 1|12` PASS, the refuter's scan sweep 30/30 against the stored
Python norms (s09 is the pre-existing Python-side `ZeroDivisionError`), cycles8
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
   the full run.  The Lemma-C-settled two-4-cycle patterns hold 1,823,760 of
   POOL6's 1,905,420 pairs, so the run that matters is
   `kakeya-search cycles8 --pool 6 --patterns 8cycle` (81,660 pairs; about
   5 h at the 4.6 pairs/s the 2026-09-05 POOL6 run sustained on 8 threads).
