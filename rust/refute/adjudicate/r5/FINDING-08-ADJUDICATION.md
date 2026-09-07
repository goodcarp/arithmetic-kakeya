# Adjudication, finding 8/10 (lens: record) — VERDICT: real = true (upheld)

Finding: "Coverage-map row 'stacked POOL4 max_t=1' has a 0-byte Python side; no
Python max_t=1 stacked output exists anywhere."

Artifacts tested (sha256):
  rust/target/release/kakeya-search  add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9  (matches the pinned hash)
  src/fastcore_rs.abi3.so            03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b
All wall-clock numbers below are CONTENDED (shared machine); runs used --threads 2.

## 1. File facts — CONFIRMED
$ ls -l rust/refute/search/py_stacked_p4_t*
-rw-r--r--@ 1 spaceman staff 0 Sep  5 18:07 rust/refute/search/py_stacked_p4_t0.txt
-rw-r--r--@ 1 spaceman staff 0 Sep  5 18:07 rust/refute/search/py_stacked_p4_t1_rskernel.txt
Both named Python sides are 0 bytes. The Rust sides are non-empty (178 B each):
rs_stacked_p4_t0.txt, rs_stacked_p46_t1.txt, both carrying
"POOL4: best ... = 7/4 (1.75)" / witness ((0,0),(0,0),(0,0),(0,0)) m=8 r=6 t=0 T0=[] / hits 0.

## 2. Whole-tree hunt for a Python stacked max_t=1 RESULT — NONE EXISTS
grep -rl 'best score over all interfaces' over the whole tree returns 26 paths.
Excluding source files (.py/.rs), Rust-side outputs, and my own adjudicate/ files,
every Python-side stacked artifact on disk is one of:
  logs/stacked.log                     Aug 24 19:41, 359 B — POOL4 + POOL6, max_t = 2
                                       (src/stacked.py __main__ calls run(pool) and
                                       run's signature is `def run(pool, max_t=2, ...)`)
  rust/refute/search/r3/py_stacked.norm  a masked copy of that same log
  rust/refute/search/py_stacked_lowtarget.txt  175 B, a TypeError traceback (best=None)
  rust/refute/search/r5-hitpaths/out/st_p3_mt0.py_rskernel.txt  POOL3, max_t=0, PyO3 kernel
No POOL4 max_t=1 Python output anywhere. The lens is right.

## 3. Is the on-disk correction (PROGRESS.md:144) accurate? — SUBSTANTIALLY YES
Row 144 now reads: "as a SEPARATE max_t=1 comparison, UNSUPPORTED on disk. The
substance (best 7/4, all-ZERO witness, 0 strict hits, tie-break) IS supported by
the max_t=2 comparison: logs/rust-stacked_pool4.log vs the pure-Python
logs/stacked.log, md5-equal (r3 sec 1)."

Checks:
(a) "pure-Python logs/stacked.log" is correct: that log is dated Aug 24 19:41,
    which predates src/fastcore_rs.abi3.so (Sep 4 16:10) — no Rust kernel existed.
(b) "max_t=2 covers max_t=1" is sound. src/stacked.py:28 is `for t in range(max_t+1)`,
    so max_t=1's space is a strict subset of max_t=2's; `best` updates only on strict
    `sc < best`, and the recorded witness has t=0, so the same first-index witness and
    the same 0 hits must come out at max_t=1. Verified empirically on the pinned binary
    at POOL3 (cheap enough to run to completion), --threads 2, contended:
      max_t=0  73.5 s   max_t=1  80.8 s   max_t=2  77.5 s
    all three outputs identical after masking [Ns]:
      md5 = 93118f2739afc1a2e56e69724117ab53 for t = 0, 1, 2
    (outputs at f8_rs_p3_t{0,1,2}.txt). The max_t knob is degenerate for this driver.
(c) MINOR IMPRECISION in the correction: the individual files named are not md5-equal
    (logs/rust-stacked_pool4.log = 177 B ebdb49a881e4bb536ab41fbaafddd6dd;
     logs/stacked.log = 359 B a7fdfff3b77c816b0d659d0ad71a39e2). The md5 equality
    r3 sec 1 established is over `cat rust-stacked_pool4.log rust-stacked_pool6.log`
    vs logs/stacked.log with [Xs] masked (both b4659f69da0b5307c9a81ac0b0283d71,
    see r3/py_stacked.norm and r3/rs_stacked.norm). The row should name both Rust logs.

## 4. RESIDUAL DEFECT the correction did NOT fix
PROGRESS.md:56-62 (the "Landed after the in-flight oracles came back" bullet) is
UNAMENDED and still reads verbatim:
   "- stacked POOL4 max_t=1 vs `oracle_drivers.py stacked 4 1`: identical except
      the `[Ns]` elapsed. ... the 12-thread Rust run reproduces exactly that."
No kernel disclosure, no "Python side is 0 bytes" note — while the cycles8 bullet
immediately below it (63-110) got a long disclosure paragraph, and the map row at
144 now says the opposite. The prose the lens actually cited still asserts a
comparison that was never completed. The record is now self-contradictory at two
places about the same run; fix the bullet, not just the table.

## 5. Retraction hunting (found nothing to retract)
- No shim was written for this finding, so the shim rule has no purchase.
- Nothing in the finding rests on a Python side that "never returned" and was
  reported as if it had — the finding's whole point is the opposite.
- The one place the lens could have overreached is its own concession sentence,
  and that concession is correct: the substance IS backed by the max_t=2 pair.
