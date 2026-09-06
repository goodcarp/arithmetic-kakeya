# r3 — independent refutation attempt: does `kakeya-search` reproduce the Python drivers?

Run 2026-09-06 by a fresh refuter, without reusing `refute/search/*.norm` or
`refute/search/norm.py`.  Own normaliser (`mynorm.py`), own field-by-field
RESULT differ (`jsondiff.py`), own compare driver (`compare.sh`).

Python side is always `/usr/bin/python3` (3.9.6), `KAKEYA_PURE_PY=1`, cwd
`arithmetic-kakeya/src`.  Rust side is `rust/target/release/kakeya-search`
(rustc 1.98.0).  Only two things are ever masked: the RESULT `"seconds"` field
and the `[<x>s]` bracket.  Everything else (every HIT, HITOBJ, witness, score,
tie-break, count, `complete` flag, exit code) is compared verbatim.

NOTE: the machine was shared with other agents' long runs throughout, so all
wall-clock numbers here are contended and not benchmarks.

## 0. Kernel gate (prerequisite, run first)

- `adversary-fable/traps.json` (119 traps) through `run_traps.py`, `_INV`
  cleared before every Python call:  **PASS 91 / FAIL 18 / SKIP 10**.
  The 10 skips are `_inv(...)` traps (`fastcore_rs` exports only `P`, `force`,
  `rank`).  Of the 18 "FAIL":
  - 1 (`c02_cache_poison_force`) is the recorded `_INV` poison value; with the
    cache cleared, Python and Rust agree — a trap-file artefact, not a port bug.
  - 17 are out-of-contract inputs already itemised in
    `adversary-fable/PORT-TRAPS.md` §"Not applicable": `p < 0`, `p >= 2^32`,
    entries >= 2^63, float `p`/entries, `rows=None`, a generator as `rows`,
    `True` inside `T0`, `rank(iter([]))`.  No driver in `src/` passes a
    non-default `p` or any of those shapes (checked by grep of the call sites:
    `g2_tall.py:32`, `cycles8.py:61`, `rzero.py:41`, `search.py:157,217`,
    `stacked.py:27`).
- `adversary-external/VERIFIED.md` traps v01–v16: **15 PASS, 1 SKIP (`_inv`),
  0 FAIL**.
- `rust/difftest.py`: **54406 checks, 0 mismatches, 1 expected divergence**
  (i64 boundary), 102.5 s.

Files: `traps_fable.txt`, `difftest_out.txt`.

## 1. The two completed long stacked runs vs the recorded Python log

`cat logs/rust-stacked_pool4.log logs/rust-stacked_pool6.log` vs
`logs/stacked.log`, `[<x>s]` masked:

    md5 py = md5 rs = b4659f69da0b5307c9a81ac0b0283d71     6/6 lines identical

Both POOL4 and POOL6 reproduce `best = 7/4 (1.75)`, the witness
`((0, 0), (0, 0), (0, 0), (0, 0)) m=8 r=6 t=0 T0=[]` and `hits: 0`.
Caveat worth stating: with 0 hits, `stacked.py`'s `for x in h[:5]` print block
is never exercised on either side, so 3 of the driver's 4 output shapes are
compared, not 4.  (`stacked.rs::hit_line` is pinned only by a unit test.)
File: `stacked_logdiff.txt`, `py_stacked.norm`, `rs_stacked.norm`.

## 2. Cheap fixtures re-run from scratch, both thread counts

| id | command | py lines | verdict |
|---|---|---|---|
| F1 | `scan1.py n4_p6_t1 2x2 6 1 7/4 -` vs `scan --d 2x2 --pool 6 --max-t 1 --target 7/4` | 241 | py == rs1 == rs12, RESULT 10/10 fields equal |
| F2 | `scan1.py g2_23_t1 2x3 3 1 9/5 -` | 1 | identical |
| F3 | `scan1.py g2_32_t1 3x2 3 1 9/5 -` | 1 | identical |

`rs1` vs `rs12` differ only in `"seconds"` (raw bytes otherwise identical).

## 3. New configurations, not in PROGRESS.md's coverage map

| id | configuration | py lines | verdict |
|---|---|---|---|
| F4 | `scan 2x3 pool4 max_t1 target 67/40 --limit 40` (sampled, new d/pool/target/limit combo) | 1 | identical |
| F5 | `scan 2x2 pool6 max_t1 **target 2**` — 1338 hits, best 7/4 | 2677 | identical, all 1338 HIT + 1338 HITOBJ verbatim |
| F6 | `g2-tall --rows 2 --max-t 1` (rows=2 is not in the map) | 1 | identical **except the 3 Rust-only RESULT keys** (finding A) |
| F7 | `g2-tall --rows 3 --max-t 2` (max_t=2 is not in the map) | 1 | same: identical except the 3 extra keys |
| P2 | target given unnormalised (`14/8`) | 241 | identical |
| P3 | `--limit 100` on a 64-element space (sampling with replacement) | 551 | identical |
| P4 | `--limit 1` | 3 | byte-identical |
| P5 | `--d 1` (n = 1) | 1 | byte-identical |
| P6 | `--max-t 3` with n = 4 | 625 | identical |
| P7b | `--limit 37 --seed 11` pool4 target 2 | 223 | identical |
| S123 | `--limit 37 --seed 123` vs `scan_dims(..., seed=123)` | 257 | identical |
| S0 | `--limit 37 --seed 0` vs `scan_dims(..., seed=0)` | 255 | identical |

`scan1.py` pins `seed=11`, so S123/S0 go through `scan_seed.py`, a 20-line
shim that calls the unmodified `search.scan_dims` with the seed exposed.  Three
distinct seeds now agree end to end, which is a stronger statement about the
MT19937 port than the single seed-11 case in the coverage map.

F5 is the strongest new comparison: 343 label tuples, 1338 hits with non-empty
`gens`/`T0`, ties everywhere, best `7/4` — 2677/2677 lines identical.

## 4. Rust-only `walked`/`pairs` keys checked against an independent oracle

`pairs_g2.py` re-implements `g2_tall.py`'s outer loops (no `min_generators`)
and counts label tuples and (graph, T0) pairs:

    g2_tall 2x2 max_t=1: walked=16  pairs=59      == rust  walked 16/16   pairs 59
    g2_tall 2x3 max_t=1: walked=256 pairs=1587    == rust  walked 256/256 pairs 1587
    g2_tall 2x3 max_t=2: walked=256 pairs=3426    == rust  walked 256/256 pairs 3426

So the extra keys are correct; they are still an output difference (finding A).

## 5. Gates re-verified

    cargo test --release --workspace   -> kakeya-core 62, kakeya-search 16, fastcore-rs 0 => 78 passed, 0 failed
    kakeya-search check --threads 1    -> 14 PASS, 2 SKIP, 0 FAIL, exit 0
    kakeya-search check --threads 12   -> same, differs only in the [Ns] brackets

## FINDINGS

### A. `g2-tall` RESULT is NOT byte-identical to the Python driver's (real, documented)
Rust appends `"walked"`, `"total"`, `"pairs"` after `"seconds"`:

    py: ...,"complete": true, "seconds": SEC}
    rs: ...,"complete": true, "seconds": SEC, "walked": 16, "total": 16, "pairs": 59}

A plain `diff` against a Python g2-tall log fails; the tail has to be stripped
first.  Documented in PROGRESS.md 2026-09-06 item 2, and the values are correct
(§4), but "reproduces the Python drivers" is false as stated for this driver.
Reproduced on two configurations (F6 rows=2, F7 rows=3 max_t=2).

### B. PROGRESS.md's "Known limits" bullet on `g2_tall` `complete` is wrong about WHEN they disagree
It says they "agree except for a run given `--tlimit > 700` that finishes
between 700 s and the limit".  In fact they disagree for **every** tripped run
whose elapsed is under 700 s, which is the common case:

    py  g2tall_tl.py 4 1 3   -> "complete": true,  "seconds": 6.5   (el < 700)
    rs  g2-tall --rows 4 --max-t 1 --tlimit 3 --threads 1
                             -> "complete": false, "seconds": 3.1

(Prior refuter had the same pair in `refute/search/py_g2tall_tl1.txt` /
`rs_g2tall_tl1.txt`; the PROGRESS.md wording does not match it.)
Files: `out/TL.py.txt`, `out/TL.rs1.txt`.

### C. `--target` rejects decimal strings that `scan1.py` accepts (independent reproduction)
    py  scan1.py P1 2x2 6 1 1.75 -    -> 241 lines, target "7/4"
    rs  scan --target 1.75            -> kakeya-search: bad fraction "1.75": invalid digit found in string ; exit 1
Same as the prior refuter's `probes.txt` §P1.  Input-domain narrowing, not a
wrong answer; no recorded run uses a decimal target.
Files: `out/P1.py.txt`, `out/P1.rs1.txt`.

### D. The claim's "check subcommand passes 12/12" is a miscount
`check` runs 16 fixtures: **14 PASS, 2 SKIP (ladder, schemes), 0 FAIL**.
12 is the old `cargo test -p kakeya-search` figure, now 16 (workspace 78).
Files: `out/check_t1.txt`, `out/check_t12.txt`.

### E. NOT a finding — retracted
`--seed 123` looked like a 223-vs-257-line divergence.  Cause: `scan1.py`
hard-codes `seed=11` in its `scan_dims` call and has no seed argument, so the
Python was sampling at seed 11 while the Rust sampled at 123.  Re-run at
matching seeds (P7b, S123, S0): identical.  Harness error, not a port bug.

## 6. Late additions

### rzero, 6th recorded job (not in the coverage map's "5 sweeps")
`logs/rzero.log`'s last line is `[2,2,2,2]/POOL4 limit 60000`, which tripped the
Python's 600 s cap at `scanned 59201`.  Re-run to completion on both sides
(`rzero_one.py 2x2x2x2 4 60000 0 1e9` vs `rzero --d 2x2x2x2 --pool 4
--limit 60000 --seed 0`):

    py : {"tag":"rzero","d":[2,2,2,2],"pool":4,"scanned":60000,"total":60000,"forcing_objects":0,"best_score":null,"complete":false,"seconds":284.4}
    rs1/rs12: identical except "seconds"   (all 8 fields equal)

### cycles8 POOL3 re-verified against a PURE-PYTHON oracle
The coverage map's cycles8 row was produced with the PyO3 kernel on the Python
side.  Re-run with `KAKEYA_PURE_PY=1`.  Rust `--threads 1` and `--threads 12`
are BYTE-identical to each other and both print

    5 presence patterns are 2-regular with m = 8
    RESULT {"tag": "cycles8", "pool": 3, "best": null, "hits": 0, "tested": 29004}

Files: `out/C8.rs1.txt`, `out/C8.rs12.txt`, `out/C8.py.txt`.

### FINDING F (new): the binary ABORTS on index spaces the Python enumerates fine
`scan` with `--tlimit` builds the whole chunk vector eagerly:
`engine.rs:213-220` does `(0..nchunks).into_par_iter().map(...).collect::<Vec<ChunkOut>>()`,
and `nchunks = total / 4096`.  For a 5-level box the allocation is astronomic:

    d=2x2x2x2x2 pool 4, max_t 0, target 7/4, tlimit 2, threads 1
      python : RESULT {... "scanned": 2904, "total": 4656612873077392578125, "complete": false, "seconds": 2.0}   exit 0
      rust   : memory allocation of 141211520553262032 bytes failed        SIGABRT, exit 134
    d=2x2x2x2x2 pool 3  (4^31 = 4611686018427387904, fits u64)
      rust   : memory allocation of 81064793292668928 bytes failed         SIGABRT, exit 134

Python's `total` is a bigint and its enumeration is lazy, so it always returns.
Note this is NOT the `checked_pow` issue: `common.rs` was edited at 15:10 today
by another session to add an "audit C6" panic for `alphabet^nslots > u64`, but
the shipped binary (`target/release/kakeya-search`, 09:22) predates it and does
not contain that string.  `engine.rs` (Sep 5 17:32) is untouched, so the eager
`collect` is still there.  Files: `out/OV.py.txt`, `out/OV.rs1.txt`,
`out/OV_bracket.txt`.

### FINDING G (independently reproduced): --tlimit is not a wall-clock bound
Same root cause.  `d=2x2x2x2 pool 4 max_t 0 target 7/4 --tlimit 2`:
Python returns in 2.8 s wall; the Rust at `--threads 1` was still running when
killed at 45 s (`out/ov_2x2x2x2_4.txt` is empty, no EXIT line).  Matches the
prior refuter's `finding_tlimit_not_a_bound.txt` (5 s limit -> 120 s wall).

### Coverage gap worth stating
Every end-to-end comparison that exists for `g2_tall`, `cycles8`, `stacked` and
`rzero` -- including the new ones here -- has `best: null` / `hits: 0` /
`forcing_objects: 0`.  So four of the five drivers' "found something" print
paths (g2_tall's `[2xr] score ...` improvement line, cycles8's HITOBJ block,
stacked's `for x in h[:5]` line, rzero's `generator-free forcing object!` line)
are never exercised by any differential run; they are pinned only by Rust unit
tests whose expected strings the porter produced.  `scan`'s HIT/HITOBJ paths
ARE covered end to end (F1 120 hits, F5 1338 hits, P3, P6, S0, S123).
These paths are not reachable by any cheap configuration: stacked's hit test is
the hardcoded `sc < 7/4` and its best over all interfaces IS 7/4; g2_tall's cap
is the hardcoded 11/6 and nothing beats it; rzero's line needs a
generator-free forcing object, whose non-existence is the point of the probe.

### cycles8 `--patterns` partition claim verified (PROGRESS.md 2026-09-06 item 3)
    cycles8 --pool 3 --patterns 8cycle : tested 3948   patterns [2, 3]
    cycles8 --pool 3 --patterns 4+4    : tested 25056  patterns [0, 1, 4]
    3948 + 25056 = 29004 = the full POOL3 run's `tested`.
The printed pattern table's cycle types (indices 0,1,4 = [4,4]; 2,3 = [8]) are
consistent with the label counts 729/243/81/81/27 summing to 1161 label tuples.
Files: `out/C8pat_8cycle.txt`, `out/C8pat_44.txt`.

### FINDING G, measured
`scan --d 2x2x2x2 --pool 4 --max-t 0 --target 7/4 --tlimit 2`:
  python `scan1.py TLB 2x2x2x2 4 0 7/4 - 2` -> 2.8 s wall, RESULT `"seconds": 2.0`,
  `"scanned": 2781`, `"total": 30517578125`, exit 0.
  rust `--threads 12` -> still running at 456 s (7 min 36 s) wall; killed.
  `out/TLB.py.txt`, `out/TLB.rs12.note`.

## 7. Concurrency note — the tree moved under this run

Another session was editing this tree while r3 ran (machine load average peaked
at 390).  `crates/kakeya-search/src/common.rs` changed at 15:10 and
`PROGRESS.md` grew a new section, "Known limits — additions from the closing
audit (C6, 2026-09-06)", which now lists Finding F (allocation abort under
`--tlimit` on a large index space) and Finding G (`--tlimit` is not a wall-clock
bound) as OPEN.  Both were reached here independently, from the CLI, at ~15:22
against the 09:22 binary; they are not novel as of the file's current state.

Still-stale text in the same file, not corrected by that section:
- header: "`cargo test --release -p kakeya-search`: 12/12 pass" and
  "`check --threads 12`: 11 PASS, 2 SKIP" — measured today: 16 tests, and
  14 PASS / 2 SKIP / 0 FAIL.
- the older "Known limits" bullet still says the `g2_tall` `complete`
  divergence only bites for `--tlimit > 700` (Finding B).

---

# Corrections — added 2026-09-06 ~16:00 EDT by the session that read this report

Appended, not edited: everything above is r3's text as it stood at 15:32.
Each item below was re-measured from the CLI before being written.

## C1. Finding B is RETRACTED — it is a harness artefact
r3's own `g2tall_tl.py` makes `tlimit` settable while copying the literal
`"complete": (el < 700)` verbatim out of the shipped driver.  Lowering the
limit without lowering the constant manufactures the divergence it reports.
The shipped `g2_tall.py` `__main__` hardcodes 700 in BOTH places
(`run(rows_, max_t=1, tlimit=700)` and `(el < 700)`), so for every run that
driver can actually perform, `el < 700` is a correct completeness test and
PROGRESS.md's original wording — they disagree only for `--tlimit > 700`
finishing between 700 s and the limit — stands.
This is the same class of error as r3's own Finding E, retracted three
sections earlier for the same reason (a shim that pinned `seed=11` while the
Rust sampled at 123).  Parameterise a value, parameterise every constant that
refers to it.  Recorded in PROGRESS.md next to the g2_tall bullet.

## C2. The section 7 claim about the shipped binary is STALE
r3 wrote: "the shipped binary (`target/release/kakeya-search`, 09:22)
predates it and does not contain that string."  True at 15:32; the rebuild
landed at 15:33, one minute later.  The current binary
(sha256 `add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9`)
does contain `exceeds u64; refusing to run (audit C6)` and does fire it.
Not r3's fault — the tree moved under it, exactly as its section 7 warns.

## C3. Finding F is CONFIRMED and still live, in a narrower form
Re-run against the 15:33 binary,
`scan --tag OVn --d 2x2x2x2x2 --max-t 0 --target 7/4 --tlimit 2 --threads 1`:

    --pool 4  (5^31 > u64)   panicked "label index space 5^31 exceeds u64;
                             refusing to run (audit C6)"           exit 101
    --pool 3  (4^31 = 4611686018427387904, fits u64)
                             memory allocation of 81064793292668928
                             bytes failed                          exit 134

So the `checked_pow` fix moved the boundary but did not close the finding:
configs whose `total` overflows u64 now refuse loudly, while configs whose
`total` fits u64 and whose chunk count is still astronomic abort as before.
The smallest live repro is `--pool 3`, not `--pool 8` or `--pool 4`.
PROGRESS.md's OPEN bullet has been re-scoped accordingly.

## C4. Section 6's heading overclaims — the pure-Python oracle never returned
"cycles8 POOL3 re-verified against a PURE-PYTHON oracle" is not supported by
the files it cites.  `out/C8.py.txt` is 45 bytes — the header line only, no
RESULT, no `EXIT=`.  The body of that section only ever compares Rust
`--threads 1` against Rust `--threads 12`.  Read strictly it never asserts a
Python result, but the heading does, and a reader taking the section at its
title would bank a comparison that was not run.

The underlying observation that opens the section is nonetheless the most
useful thing in this report: the coverage map's cycles8 POOL3 row was indeed
produced with the PyO3 kernel on the Python side
(`../py_cycles8_p3_rskernel.txt` is the completed oracle; `../py_cycles8_p3.txt`
is the pure-Python attempt, also 45 bytes, also killed).  That row therefore
checks the DRIVER port with the kernel held fixed, and the map did not say so.
Now disclosed in PROGRESS.md.

Cost to actually close it, measured rather than guessed: pure-Python cycles8
POOL3 runs at 5.22 pairs/s on this (contended) machine — 779 pairs in 149 s,
`../r4/rate_c8.py` — so 29,004 pairs is about 93 minutes of CPU.  The ~36 h
figure a POOL6 extrapolation gives (0.22 pairs/s) is wrong; POOL6 pairs are
far more expensive than POOL3 pairs.

**In flight:** r3's own `py_drv.sh C8 cycles8 3` (pid 13369) was orphaned by
the session switch and is STILL RUNNING pure-Python, unattended.  At 16:00 EDT
it had 25 min of the ~93 min of CPU it needs, taking only ~21% of a core
against the 8-cycle job.  Its RESULT will land in `out/C8.py.txt` when it
finishes — expect it 2–5 h after 16:00.  It was left alive deliberately.
Whoever picks this up: `cat out/C8.py.txt`; a complete run prints
`RESULT {"tag": "cycles8", "pool": 3, "best": null, "hits": 0, "tested": 29004}`
followed by `EXIT=0`, which would close C4 outright.

## C5. Finding D is CONFIRMED by independent re-measurement
    cargo test --release -p kakeya-search   -> 16 passed; 0 failed
    kakeya-search check --threads 1         -> 14 PASS, 2 SKIP, 0 FAIL, exit 0
PROGRESS.md lines 7, 8 and 36 (`12/12`, `11 PASS`) were stale and are fixed.
Findings A and C stand as written; both were already documented as known
limits rather than defects.
