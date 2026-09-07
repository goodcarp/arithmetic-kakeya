# r5 / record lens — documentation vs reality

Run 2026-09-06 16:35–17:35 EDT.  Lens: re-measure every concrete number, count,
command, filename, hash and "X reproduces Y" claim in the record against the tree
as it stands, and check each coverage-map row for which kernel was actually under
the Python side.  Nothing outside `rust/refute/record/r5/` was written.  No process
was signalled.

Machine contended throughout (pid 12158 held ~5 cores until 16:46; pid 13369 still
holds ~0.5 core).  Every wall-clock number below is contended and is labelled so.

Artifacts written by this pass, all under `rust/refute/record/r5/`:
`pattern_order.py`, `verify_traps.py`, `resweep.sh`, `configs_s01_s07.txt`,
`allconfigs.txt`, `resweep/` (26 Rust stdouts + norms).

---

## VERDICT: REFUTED

Five load-bearing claims are false as written: a kernel disclosure that names one
row when at least two more are affected; a coverage-map row whose Python side left
a 0-byte file; two coverage-map rows with no artifact anywhere in the tree; and two
sweep counts (`30/30`, `37 configurations`) that count configs *listed*, not
configs *run*.  All five err in the direction of overclaim.

---

## R1 — MAJOR.  The kernel disclosure names one row; at least two more rows had the PyO3 kernel on the Python side

`crates/kakeya-search/PROGRESS.md:68-72`:

> **Kernel disclosure, added 2026-09-06.**  Unlike every other row of the
> coverage map, the Python side of THIS comparison did not run pure Python.

The same file, 15 lines earlier (`PROGRESS.md:50-54`), says the opposite:

> ## In flight
> - Python oracles running (with the Rust fastcore kernel, which B1 proved
>   bit-identical, so they finish in minutes not hours):
>   g2-tall 4 1, cycles8 3, stacked 4 1.

and the "Landed after the in-flight oracles came back" section then turns all three
into coverage-map rows.  The surviving artifacts carry the same tell that r4 used
to catch the cycles8 row — an `_rskernel` filename:

    $ ls -l rust/refute/search/*rskernel*
    -rw-r--r--  124  Sep  5 18:22  py_cycles8_p3_rskernel.txt      <- disclosed
    -rw-r--r--  148  Sep  5 18:48  py_g2tall_2x4_rskernel.txt      <- NOT disclosed
    -rw-r--r--    0  Sep  5 18:07  py_stacked_p4_t1_rskernel.txt   <- NOT disclosed (and empty, see R2)

    $ cat rust/refute/search/py_g2tall_2x4_rskernel.txt
    RESULT {"tag": "g2_tall_2x4", ..., "complete": false, "seconds": 1968.2}
    $ cat rust/refute/search/rs_g2tall_2x4.txt
    RESULT {"tag": "g2_tall_2x4", ..., "complete": true,  "seconds": 319.0}

So coverage-map row `| g2-tall 2x4 (the Tier-3 target) | g2_tall.run | identical
exc. seconds and complete |` is, like the cycles8 row, a DRIVER-level check with
the kernel held fixed.  The map does not say so, and the disclosure paragraph
explicitly asserts it is the only one.  A third `_rskernel` artifact exists in a
concurrent lens's directory (`refute/search/r5-hitpaths/out/st_p3_mt0.py_rskernel.txt`),
so the pattern is not confined to these three.

Measured value: **at least 2 of the 10 coverage-map rows** (cycles8 POOL3,
g2-tall 2x4) ran the PyO3 kernel on the Python side; the record discloses 1.
The g2-tall 2x4 row is the one the map labels "the Tier-3 target".

## R2 — MAJOR.  `stacked POOL4 max_t=1` — the Python side of that comparison left a 0-byte file

`PROGRESS.md:57-62` and coverage-map row
`| stacked POOL4 max_t=1 | stacked.run | identical exc. elapsed; witness + tie-break reproduced |`
claim a completed comparison against `oracle_drivers.py stacked 4 1`, including
"it is a genuine TIE-BREAK test ... the 12-thread Rust run reproduces exactly that".

Both files on disk named for that Python side are empty:

    $ ls -l rust/refute/search/py_stacked_p4_t1_rskernel.txt rust/refute/search/py_stacked_p4_t0.txt
    -rw-r--r--  0  Sep  5 18:07  py_stacked_p4_t1_rskernel.txt
    -rw-r--r--  0  Sep  5 18:07  py_stacked_p4_t0.txt

The Rust sides are present and non-empty (`rs_stacked_p46_t1.txt`,
`rs_stacked_p4_t0.txt`).  A whole-tree search for the driver's own output line
finds no Python `max_t=1` stacked result anywhere:

    $ grep -rl "best score over all interfaces" . | xargs ls -l
    ... only: oracle_drivers.py, stacked.rs, rs_stacked_*.txt, logs/stacked.log (max_t=2),
        logs/rust-stacked_pool{4,6}.log, r3's max_t=2 norms, r5-hitpaths' own files

This is the same signature r4 flagged for cycles8 (`py_cycles8_p3.txt`, 45 bytes,
killed before RESULT).  Scope note in the record's favour: the *substance* — best
7/4, witness `((0,0),(0,0),(0,0),(0,0)) m=8 r=6 t=0 T0=[]`, 0 strict hits — is
independently supported by the `max_t=2` comparison (`logs/stacked.log` vs
`logs/rust-stacked_pool4.log`, md5-equal per r3 §1).  What is unsupported is the
`max_t=1` row as a separate comparison, which is exactly what the map counts it as.

## R3 — MAJOR.  Two coverage-map rows have no artifact anywhere in the tree

    | scan k=1 box `--d 6`          | scan1.py | identical |
    | scan 3-level sampled `--d 2x2x2` | scan1.py | identical |

Whole-tree search for scan-driver RESULT lines (a scan RESULT always carries
`"max_t"`):

    $ grep -rh '"max_t"' . | grep -E '"d": \[2, 2, 2\]|"d": \[6\]' | sort -u
    RESULT {"tag": "g2_222_t1", "d": [2,2,2], ..., "scanned": 864,  "total": 16384, "complete": false, "seconds": 3305.6}
    RESULT {"tag": "n6c2_6_t1", "d": [6],     ..., "scanned": 1619, "total": 3125,  "complete": false, "seconds": 2400.8}
    RESULT {"tag": "n6c_6_t1",  "d": [6],     ..., "scanned": 1700, "total": 3125,  "complete": false, "seconds": 3005.8}
    RESULT {"tag": "n8a_222_t0","d": [2,2,2], ..., "scanned": 207,  "total": 40000, "complete": false, "seconds": 3059.9}
    RESULT {"tag": "n8b_222_t1","d": [2,2,2], ..., "scanned": 173,  "total": 15000, "complete": false, "seconds": 3060.3}

All five are Aug-24 *Python* logs and all five are INCOMPLETE time-limited
prefixes with differing `scanned` — none of them is even in principle reproducible
byte-for-byte, and there is no Rust counterpart for any of them.  Under
`rust/refute/` there is no `--d 6` RESULT at all and no scan-driver `--d 2x2x2`
RESULT at all (`d=[2,2,2]` appears there only under the `rzero` driver, which is a
different coverage row).  The sweep config that would have produced the `--d 6`
row is `configs.txt` line `c12 6 6 1 2 -`, whose Python output file
`refute/search/sweep/c12.py.txt` is **0 bytes**; the 2x2x2 configs `s17b`, `s18`,
`s19` were listed and never run (no artifacts).

## R4 — MAJOR.  "scan sweep 30/30 against the stored Python norms" — there are 26 stored norms, and the count is 25/26

`PROGRESS.md:143-148` (the 2026-09-06 follow-ups gate):

> `check --threads 1|12` PASS, the refuter's scan sweep 30/30 against the stored
> Python norms (s09 is the pre-existing Python-side `ZeroDivisionError`)

Measured.  Stored norms:

    $ ls rust/refute/search/sweep/*.py.norm | wc -l
    26

Re-ran the CURRENT binary (sha `add55418…`) against every one of them,
`--threads 2`, normalised with the record's own `refute/search/norm.py`
(`rust/refute/record/r5/resweep.sh`, output in `resweep/`):

    RESWEEP stored_norms=26 pass=25 fail=1 noconfig=0
    (the one FAIL is s09: stored Python ZeroDivisionError traceback vs Rust panic — the known row)

There is no 30 available: 26 is the ceiling, 25 is the pass count.  `30/30`
overstates by 4–5.

Self-check, per the shim rule: my first version of `resweep.sh` used `declare -A`
under `/bin/bash` 3.2, which silently made every lookup return the LAST config and
produced 25 fabricated FAILs.  Caught by noticing every Rust stdout was 669 lines
(= s06's length), rewritten without associative arrays, re-run.  Only the corrected
run is reported.

## R5 — MAJOR.  COMMANDS.md "sweep over 37 scan configurations" counts configs listed, not run

`refute/search/COMMANDS.md:37-43`:

> ## 4. Differential sweep over 37 scan configurations
> Covers d in {2,3,4,5,6,2x2,2x3,3x2,2x4,1x3,3x1,2x1x3,2x2x2,3x3,2x2x2x2},
> pools 3/4/5/6/8, max_t 0/1/2, targets 13/8 7/4 15/8 9/5 11/6 2 3, ...

Measured.  37 = `configs.txt` (31 lines) + the 6 configs of `sweep1-out.txt`
(s01–s06) — the configs *listed*.  What was actually compared:

    verdicts on disk: sweep1-out.txt 6 PASS, sweep2-out.txt 8 PASS + 1 FAIL(s09),
                      sweepC-out.txt 11 PASS   -> 26 verdicts, 25 PASS
    neither sweep2-out.txt nor sweepC-out.txt has its "SWEEP pass=.. fail=.." trailer:
    both runs were cut off (sweep2 ends at s15b, sweepC ends at c11)
    ids ever touched in sweep/: 29 (c12, s07, s16b have only a .py.txt, no norms)
    stored .py.norm: 26

The d/pool/target actually present in the 26 completed comparisons (read out of the
stored `.py.txt` RESULT lines):

    d: [2,2] [2] [3] [4] [2,3] [3,2] [1,3] [3,1] [2,1,3]
    pool: 3 4 5 6 8          targets: 13/8 7/4 15/8 9/5 2 3

Missing from the claimed list, with no completed comparison anywhere:
**d = 5, 6, 2x4, 2x2x2, 3x3, 2x2x2x2** (6 of the 15 claimed shapes) and
**target 11/6** (its only configs are `s22`, `c13`, neither run).  11/6 is the
target that matters to the Goal-2 record.

## R6 — MAJOR.  "the 135 trap cases" double-counts; the corpus is 119

`PROGRESS.md:78` argues the kernel is covered "by `difftest.py` (54,406 …) and by
the 135 trap cases".  Measured:

    $ python3 -c "import json;print(len(json.load(open('adversary-fable/traps.json'))))"
    119
    prefix histogram: v 17, a 36, b 9, c 5, d 18, e 16, f 18

`PORT-TRAPS.md:10` states the `v`-prefixed entries "are the ones already confirmed
in `VERIFIED.md`", i.e. the 16 VERIFIED rows are *inside* the 119.  135 = 119 + 16
counts them twice.  Distinct trap cases: **119**.

Positive result from the same run (`record/r5/verify_traps.py`, pure Python,
`_INV` cleared before every call, `assert fastcore.force is fastcore._force_py`):

    VERIFIED.md rows checked: 17 call-forms (16 numbered rows), mismatches=0
    traps.json entries: 119, mismatches vs current pure-Python fastcore: 0

So the corpus itself is intact and still reproduces; only the count in PROGRESS is
inflated.

## R7 — MINOR.  PORT-TRAPS "The 16 entries prefixed `v`" — there are 17

`v01…v16` plus `v10b_entry_P_plus_1_is_one`; VERIFIED row #10 carries two calls
(`rank([[2147483647]])` and `rank([[2147483648]])`), which is where the 17th comes
from.  Measured count of `v`-prefixed names in `traps.json`: **17**.

## R8 — MAJOR (live trap).  PORT-TRAPS's statement about `fastcore.py` is now false, in the direction that reintroduces kernel substitution

`PORT-TRAPS.md:4-6`:

> Every `expected_repr` in `traps.json` was produced by running the call against
> `K/src/fastcore.py` (pure Python; there is no `_force_py`/`_rank_py` split and
> no `KAKEYA_PURE_PY` switch in that file)

Measured against the tree as it stands (`src/fastcore.py`, mtime 2026-09-06 15:10):

    $ grep -n "_force_py\|_rank_py\|KAKEYA_PURE_PY" src/fastcore.py
    114:# the differential harness (rust/difftest.py) and KAKEYA_PURE_PY=1 runs can
    116:_force_py = force
    117:_rank_py = rank
    121:if _os.environ.get("KAKEYA_PURE_PY") != "1":

Both exist.  The sentence was true when written (2026-09-04 16:20) and is false
now.  It matters because it tells a reader that calling `fastcore.force` in that
file *is* the pure Python — today, without `KAKEYA_PURE_PY=1`, it is the Rust
kernel.  That is precisely the substitution the record was corrected for today.
(Also: `K/` is not a path in this tree; PORT-TRAPS and PREDICTIONS both address
the repo as `K/`.)

## R9 — MAJOR.  PREDICTIONS §2.2 has the cycles8 presence patterns in the wrong product order

`PREDICTIONS.md:77-82` — "`cycles8.main` finds 5 presence patterns (computed;
product order)" — lists the three two-4-cycle patterns first and the two 8-cycles
last.  Recomputed from `cycles8.SLOTS` / `cycles8.build` with an independent
component walk (`record/r5/pattern_order.py`, pure Python):

    index  pattern                 npres  labeltuples(POOL6)  cycle_type
        0  (0, 1, 1, 1, 1, 1, 1)      6               46656  [4, 4]
        1  (1, 0, 0, 1, 1, 1, 1)      5                7776  [4, 4]
        2  (1, 0, 1, 1, 1, 0, 0)      4                1296  [8]
        3  (1, 1, 0, 0, 0, 1, 1)      4                1296  [8]
        4  (1, 1, 1, 0, 0, 0, 0)      3                 216  [4, 4]
    total label tuples: 57240

`PROGRESS.md` item 3 ("indices 0, 1, 4 = two 4-cycles; 2, 3 = single 8-cycles"),
the binary's own table (`logs/rust-cycles8_8cycle.log`) and `check`'s
`cycles8_patterns` fixture (`npres [6, 5, 4, 4, 3]`) all agree with the measurement.
PREDICTIONS does not.  Consequences:

* `PREDICTIONS.md:191` writes the label-tuple split as "216 + 7,776 + 46,656 +
  1,296 + 1,296", in the same wrong order, in the same table cell as a pairs list
  that *is* correctly "per pattern in product order" (1,557,900 / 259,650 / 40,830
  / 40,830 / 6,210, verified against `count_pairs.out`).  The two lists in that cell
  disagree with each other about which pattern is which.
* Anyone using §2.2 to drive `cycles8 --patterns i,j,...` would select the wrong
  indices.

The aggregate numbers in §2.2 are right: 54,648 = 46,656+7,776+216 and
1,823,760 = 1,557,900+259,650+6,210 are indices 0,1,4, i.e. the [4,4] patterns.
The error is confined to the stated ordering.

## R10 — MINOR.  PROGRESS misattributes which argument settles the two-4-cycle patterns

`PROGRESS.md:179-181`: "The Lemma-C-settled two-4-cycle patterns hold 1,823,760 of
POOL6's 1,905,420 pairs".  PREDICTIONS settles those by the direct-sum / mediant
argument on the complete `n4_p6_t1` scan (§2.2); Lemma C (§2.1) is the prune used
on the *8-cycle* side (§2.3, `cycle8_check.py`).  The two arguments have different
dependencies — §2.2 leans on the Python `min_generators` of a completed scan,
§2.3 on Lemma C's proof — so the attribution is not cosmetic.

## R11 — MAJOR.  "the runtime estimate for 2x5 was wrong by more than 10x" is both mis-cited and unsupported; measured, it is at most ~2.5x

`PREDICTIONS.md:273`: "The runtime estimate for 2x5 (implied by section 3) was
wrong by more than 10x."  Section 3 contains no runtime estimates (it is the
pair-count table); §4 has them, at **0.5–2 hours**.  And the 2x5 Rust run was cut
at its 7200 s cap and never completed (`logs/rust-g2_tall_2x5.log`,
`complete: false`), so no artifact on disk can supply any factor — the log predates
the `walked`/`total` keys, so it does not even record how far it got.

Measured (contended, `--threads 2`, current binary):

    $ kakeya-search g2-tall --rows 5 --max-t 1 --tlimit 90 --threads 2
    RESULT {..., "complete": false, "seconds": 100.1, "walked": 37, "total": 65536, "pairs": 386}
    real 1m40s   user 1m24.5s

386 pairs / 84.5 s CPU = **4.57 pairs/s**.  The complete 2x5 is 672,719 pairs
(`count_pairs.out`), so ≈ 147,000 s CPU ≈ **41 CPU-hours** ≈ 5 h wall on 8 threads
if it scales.  Because the probe walks the product-order *prefix*, which §4 itself
identifies as the expensive region ("2x5 1.8–3.1 s (first 4)" vs "0.04–4.7 s"
random), that figure is an UPPER bound on the true total.  Against §4's 2 h upper
end the overrun is therefore **at most ~2.5x**, not "more than 10x".

## R12 — RECORD, STALE.  RESULTS-RUST.json still lists the C6 defect as live

`rust/RESULTS-RUST.json:133` (notes[3]): "Known binary defect (audit C6): `total`
uses an unchecked integer pow, so on a box with >= 65 vertices the binary can print
complete: true without scanning; use checked_pow before quoting any RESULT from a
larger box."  The fix is in the shipped binary (file mtime 15:33; RESULTS-RUST.json
mtime 15:09):

    $ shasum -a 256 rust/target/release/kakeya-search
    add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9
    $ kakeya-search scan --tag c6 --d 65 --pool 3 --max-t 0 --target 2 --threads 1
    thread 'main' panicked at crates/kakeya-search/src/common.rs:93:40:
    label index space 4^64 exceeds u64; refusing to run (audit C6)

`PROGRESS.md:185` has this right ("FIXED and REBUILT"); RESULTS-RUST.json does not.

## R13 — RECORD, INCOMPLETE.  The 8-cycle cross-check finished during this pass and is in no record file

pid 12158 exited on its own at 2026-09-06T20:46:00Z (I signalled nothing; it was
already gone at my 20:50 `ps`).  `logs/rust-cycles8_8cycle.log`:

    pattern table (product order; --patterns selects by index):
      0 (0,1,1,1,1,1,1) cycles=[4,4] labels=46656
      1 (1,0,0,1,1,1,1) cycles=[4,4] labels=7776
      2 (1,0,1,1,1,0,0) cycles=[8]   labels=1296  SELECTED
      3 (1,1,0,0,0,1,1) cycles=[8]   labels=1296  SELECTED
      4 (1,1,1,0,0,0,0) cycles=[4,4] labels=216
    RESULT {"tag": "cycles8", "pool": 6, "best": null, "hits": 0, "tested": 81660, "patterns": [2, 3]}

Complete (81,660 = 1,905,420 − 1,823,760, the full 8-cycle pair count; no TIME
LIMIT line; `rust-targets.log` records `exit=0`).  This independently confirms
Fable's `cycle8_cheap` + `cycle8_r5` side computation (0 hits) by a different route
— no Lemma C prune, the Python prune order reproduced.  It is not yet reflected in
`PROGRESS.md`, `PREDICTIONS.md` §6 (which still says "was started … as an
independent cross-check") or `RESULTS-RUST.json` (5 runs, this is not one of them).

Timing: 19:02:26 → 20:46:00 = 6,214 s at `--threads 10` = **13.1 pairs/s**.
`PROGRESS.md:181-182` estimated "about 5 h at the 4.6 pairs/s the 2026-09-05 POOL6
run sustained on 8 threads" — actual 1.73 h, so that estimate was ~3x high.

## R14 — MINOR, STALE.  COMMANDS.md §9 still records the pre-growth test count

`COMMANDS.md:75`: "`cargo test --release --workspace` -> 62 (kakeya-core) + 13
(kakeya-search) = 75 passed".  Static count of `#[test]` in the workspace today
(no cargo run — ground rule):

    kakeya-core: 62   kakeya-search: 16   fastcore-rs: 0   => 78

`PROGRESS.md` says 78 and 16/16.  COMMANDS.md's own "Status 2026-09-06" section
does not correct §9.

---

## Claims re-measured and CONFIRMED (no finding)

| record claim | where | measured |
|---|---|---|
| binary sha256 `add55418…fcf9` | task brief, r4 | matches; `.so` = `03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b` |
| `check`: 14 PASS / 2 SKIP / 0 FAIL over 16 fixtures | PROGRESS:8 | 14 / 2 / 0, exit 0, at `--threads 1`; `--threads 2` byte-identical modulo the `[Ns]` brackets (55.6 s wall, contended) |
| workspace 78 tests (62 + 16 + 0) | PROGRESS:143 | 78 `#[test]` fns, static count |
| difftest.py 54,406 checks, 0 mismatches | PROGRESS:77, r3 | `total checks: 54406 / mismatches: 0 / expected divergences: 1`, 127.3 s contended (r3 saw 102.5 s) |
| edge-case corpus 57 | difftest output | `edge_cases.json` has 57 entries |
| traps.json 119 entries | PORT-TRAPS:3, r3 | 119, all reproduce against the current pure-Python fastcore, 0 mismatches |
| VERIFIED.md's 16 rows | VERIFIED.md | all 16 (17 call forms) reproduce, 0 mismatches |
| n4_p6_t1 = 241 lines (120 HIT + RESULT + 120 HITOBJ) | COMMANDS §1 | 241; `check` fixture scans 343/343, best 7/4, hits 120 |
| newA `2x2 3 2 2`: 300 hits, 24 with `"gens": []`, 276 with non-empty T0 | COMMANDS §3 | 300 / 24 / 276 exactly |
| sampled path `--limit 500 --seed 11` d=2x2 POOL6: 329/329 identical | PROGRESS:42 | re-run from scratch, pure-Python `scan1.py` (216 s CPU) vs Rust `--threads 2`: **329/329, byte-identical after `norm.py`**; 164 hits |
| `rzero` 5 recorded sweeps + a 6th | PROGRESS:43, r3 §6 | `logs/rzero.log` has 6 RESULT lines; `check` gates 5 |
| count_pairs: 8789 / 28357 / 31718 / 672719 / 13183980 / 1905420 | PREDICTIONS §3,§6; PROGRESS item 2 | all six match `count_pairs.out` verbatim |
| per-pattern pairs 1557900/259650/40830/40830/6210 | PREDICTIONS §3 | matches `count_pairs.out`, and is in true product order |
| g2_tall 2x3 pairs 1587, t=0 buckets 237 | PROGRESS item 2 | `check` prints `pairs 1587` and `pairs 237` |
| `cycles8_patterns` npres [6,5,4,4,3], POOL6 57240, POOL8 303616 | check fixture | reproduced; 57240 independently recomputed |
| POOL3 `8cycle` 3948 + `4+4` 25056 = 29004 | PROGRESS item 3, r3 | arithmetic holds; full POOL3 `tested` = 29004 in `py_cycles8_p3_rskernel.txt` |
| cycle8_cheap 10,062,000 calls / 0 hits / 2973 s | PREDICTIONS §6 | matches `cycle8_cheap.out` `DONE` line |
| cycle8_r5 91,993,680 calls / 0 hits / 13,369 s | PREDICTIONS §6 | matches `cycle8_r5.out` `DONE` line |
| Python cycles8 tested 526; g2_tall 2x5 818 s, 2x6 867 s; stacked 8268.5 / 16959.8 s | PREDICTIONS §0, RESULTS-RUST | all match `logs/cycles8.log`, `logs/g2_tall.log`, `logs/stacked.log` |
| RESULTS-RUST.json's 5 result blocks | RESULTS-RUST | each matches `logs/rust-<tag>.log` verbatim; all `python_*` fields match the Aug-24 logs |
| g2_tall cap arithmetic q=12→21, 11→20, 10→18, 9→16 | PREDICTIONS §2.1 | correct |
| cycles8 budgets r≤5 (t=0), ≤3 (t=1), ≤2 (t=2) | PREDICTIONS §2.2 | correct from `int(67/40*den)-8` |
| rate_c8 5.22 pairs/s → ~93 min for 29,004 | PROGRESS:85-88, r4 | arithmetic correct |
| pid 13369 is the pure-Python POOL3 oracle | r4 | confirmed: `KAKEYA_PURE_PY=1` in its environment, fd 1 → `refute/search/r3/out/C8.py.txt`; still running at 17:35 (1:40 elapsed, ~44% of a core), file still 45 bytes.  Left alive. |

## Not checked

* `cargo test` / `cargo clippy` were not run (ground rule: no cargo on the main
  workspace).  Test counts above are static `#[test]` counts.
* `--threads 12` was not run (contention rule); thread-independence was checked at
  1 vs 2 only.
* Bench numbers in `PROGRESS.md` ("idle machine") cannot be checked on a contended
  machine and are not disputed.
* `lemma_c_test.py`'s "40,000 instances, 8,196 force" was not re-run.
