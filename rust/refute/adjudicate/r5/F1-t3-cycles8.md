# Adjudication F1 (lens: science) — "cycles8 never searches t = 3"

VERDICT: **real = true**. Substantively correct, reproduced end-to-end.
Reclassify `kind`: divergence -> coverage-gap / claim-scope. There is **no**
Python-vs-Rust divergence here: both implementations hardcode the same t range,
and I confirmed they agree. Severity major is defensible as of when the lens ran
(an in-target phase, 1,692,000 (graph,T0) pairs, was never searched by either
driver and was not disclosed anywhere); the outcome is null (0 hits), so nothing
mathematical changed.

Artifacts tested (sha256):
  rust/target/release/kakeya-search  add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9  (matches the audited sha)
  src/fastcore_rs.abi3.so            03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b
All wall-clock numbers below are CONTENDED (shared machine); CPU (user) times given where they matter.

## (a) Both drivers hardcode t in {0,1,2} — CONFIRMED
  src/cycles8.py:62                        `for t in (0, 1, 2):`
  drivers/cycles8.rs:195                   `let combos: ... = (0..=2).map(|t| combinations(n, t)).collect();`
  drivers/cycles8.rs:196                   `let t_values = [0usize, 1, 2];`
Neither exposes a `--max-t`: `grep -n "max_t|max-t" drivers/cycles8.rs` -> no
hits; main.rs usage line 24 lists only `cycles8 [--pool] [--target] [--deg]
[--patterns]`. Python `main(pool, target, deg, tlimit)` has no t parameter.
So t is unreachable above 2 by any supported input. In contract.

## (b)(c) Budget arithmetic — CONFIRMED, from the driver's own formula
`adjudicate/r5/equiv_check.py` prints the table using `int(target*den) - G.m`, m=8:
    t=0 den=8 int(67/40*8)=13 budget=5  score@r0=1     <=target True
    t=1 den=7 int(67/40*7)=11 budget=3  score@r0=8/7   <=target True
    t=2 den=6 int(67/40*6)=10 budget=2  score@r0=4/3   <=target True
    t=3 den=5 int(67/40*5)= 8 budget=0  score@r0=8/5   <=target True   <-- UNSEARCHED
    t=4 den=4 int(67/40*4)= 6 budget=-2 score@r0=2     <=target False
    t=5 den=3 int(67/40*3)= 5 budget=-3 score@r0=8/3   <=target False
    t=6 den=2 int(67/40*2)= 3 budget=-5 score@r0=4     <=target False
t=3 is the one and only uncovered feasible phase at target 67/40. Confirmed.
ADDED (not in the lens report): the residual is TARGET-DEPENDENT and the Rust
binary exposes `--target`. At target 2 the same formula makes t=4 feasible
(den=4, int(8)-8 = 0, score 8/4 = 2 <= 2), so the hardcoded loop is a scope bug
for any target the user may pass, not only for 67/40.

## (d) Is t3_check.py's hit criterion exactly the driver's at t=3? — YES
Reading the driver at t=3 (budget=0): `mt > budget` skips unless mt==0;
`min_generators(base_rows, n, T0, pool, 0, mand)` with mand empty has slots=[],
so `product()` yields one empty combo, gens=[], rows=base_rows, and
extend() returns [] iff `force(base_rows,n,T0)` succeeds and None otherwise
(budget_left==0 kills the DFS). Score is then Fraction(8+0,5) = 8/5 <= target.
So "driver hit at t=3" == (mt==0) and force(base_rows,n,T0). t3_check.py does
`if not bad <= T0: continue` then `ok,_ = force(base_rows,n,T0)`.

I tested the two lemmas this rests on, on inputs where force ACTUALLY SUCCEEDS
(a pairwise driver-vs-check comparison at t=3 alone is vacuous: both sides are
0 there, 500/500 agreement with 0 hits each — `equiv_check.py` reports that).
`adjudicate/r5/lemma_check.py 600` (KAKEYA_PURE_PY=1, T0 sizes 0..8):
  RESULT {"sampled": 600, "L1_ok": 600, "L1_violations": 0, "L2_ok": 600,
  "L2_violations": 0, "L3_ok": 600, "L3_violations": 0, "force_true": 157,
  "force_false": 443, "min_gen_returned_empty": 157,
  "min_gen_returned_None": 443, "mt_eq_0": 405}
  L1 min_generators(...,budget=0,mand=[]) == [] iff force ok, None otherwise — both
     branches exercised (157 / 443), 0 violations.
  L2 local_requirement(...)[0]==0 iff bad<=T0 (405 positives) — the P4 prune is
     EXACT for r=0, not a heuristic. It is a theorem, not an approximation:
     with budget 0 any mandatory generator makes min_generators return None
     before any force call.
  L3 |bad|>3 => no 3-subset contains bad — skipping the whole graph is sound.
Also: `equiv_check.py` reports pairs_driver_rk_prune_would_skip = 0, i.e. the
driver's extra `den - rk > budget` prune never fires on these graphs, so
t3_check is not merely a superset of the driver's t=3 set — it is the same set.

## (e) Re-ran `t3_check.py 8cycle` — EXACT MATCH
  cd src && KAKEYA_PURE_PY=1 /usr/bin/python3 ../rust/refute/science/r5/t3_check.py 8cycle
  selected: [(2, '8cycle'), (3, '8cycle')]
  RESULT {"tag":"cycles8_t3_r0","pool":6,"which":"8cycle","t":3,"r":0,
  "score_if_hit":"8/5","graphs":2592,"skipped_by_P4":492,"pairs":87600,
  "hits":0,"seconds":140.5}     real 2m22s / user 31.7s  (CONTENDED)
graphs 2592 / pairs 87600 / hits 0 == the finding's 2592 / 87600 / 0; the
finding's skipped_by_P4 492 also matches.

Same script, Rust kernel (no KAKEYA_PURE_PY): identical counts,
  RESULT {... "graphs":2592,"skipped_by_P4":492,"pairs":87600,"hits":0,"seconds":11.7}
  real 0m13.5s / user 4.1s.  Kernels agree bit-for-bit on this workload.

I also verified the counts for the patterns I did not re-force, cheaply
(`adjudicate/r5/count_only.py`, force-free, 51.6 s):
  pattern 0 (0,1,1,1,1,1,1) 4+4    graphs 46656 skipped_P4 6156 pairs 1368000
  pattern 1 (1,0,0,1,1,1,1) 4+4    graphs  7776 skipped_P4 1026 pairs  228000
  pattern 2 (1,0,1,1,1,0,0) 8cycle graphs  1296 skipped_P4  246 pairs   43800
  pattern 3 (1,1,0,0,0,1,1) 8cycle graphs  1296 skipped_P4  246 pairs   43800
  pattern 4 (1,1,1,0,0,0,0) 4+4    graphs   216 skipped_P4   66 pairs    8400
  => 8cycle(2,3) 2592/87600; idx1,4 7992/236400; idx0 46656/1368000;
     all five 57240 graphs / 1,692,000 pairs.
Every count in the finding AND in the on-disk correction reproduces.

## (f) Is "cycles8 POOL6 closed at every t" now a true sentence?
Yes, but the evidence is MIXED and PROGRESS.md states the mixture honestly:
  t = 3, all five patterns: exhaustive computation, 1,692,000 pairs, 0 hits
    (patterns 2,3 re-run by me; pattern 0 evidenced by science/r5/t3_idx0_purepy.txt,
     1,368,000 pairs / 567 s, whose 2,414 pairs/s IS a pure-Python rate — consistent
     with my measured 87,600/31.7s = 2,760 pairs/s).
  t <= 2, 8-cycle patterns (2,3): exhaustive Rust run, Lemma-C-free,
    logs/rust-targets.log:26-27, exit=0 2026-09-06T20:46:00Z,
    RESULT {"tag":"cycles8","pool":6,"best":null,"hits":0,"tested":81660,"patterns":[2,3]}
  t <= 2, two-4-cycle patterns (0,1,4): NOT exhausted by computation. Closed by
    the ANALYTIC mediant argument of PREDICTIONS.md 2.2. The only Rust run over
    that region (cycles8_pool6, 6 h) covered an exact prefix of pattern 0 —
    98,973 pairs, ending at label tuple #3008 of 46,656 (RESULTS-RUST.json:160).
What it does NOT cover, and PROGRESS.md says so: cycles8 is only the
m = n = 8, every-degree-exactly-2 slice of the 2x2x2 POOL6 label space
(6.95% per PROGRESS.md); `--deg` is vacuous for any value but 2; POOL8 is not run;
and the t <= 2 closure for three of five patterns is an argument, not an exhaustion.
"cycles8 POOL6 closed at every t" is therefore true; "n = 8 closed" is not.

## Defects in the on-disk correction (found while checking it)

1. KERNEL MISLABEL (minor, real). SWEEP-2026-09-06.md:30 says
   "Reproduced `t3_check.py` (pure Python): patterns 2,3 -> ... 0 hits (13.6 s);
   patterns 1,4 -> ... (33.2 s)", and PROGRESS.md:239 puts the same
   "(13.6 s / 33.2 s)" inside a sentence whose parenthetical is
   "(pure Python, `KAKEYA_PURE_PY=1` ...)". 13.6 s is NOT a pure-Python time on
   this machine: my pure-Python run needed 31.7 s of CPU for those same 87,600
   pairs (2,760 pairs/s), so 13.6 s wall is below the pure-Python CPU floor.
   13.6 s is my Rust-kernel wall time (13.5 s; 4.1 s CPU). Those two reproduction
   timings were produced with the PyO3 kernel loaded. The RESULTS are unaffected
   (I ran both kernels; counts identical), but the disclosure is wrong in exactly
   the class the ground rules single out. Pattern 0's 567 s figure is genuinely
   pure Python (rate check above) and is correctly labelled.
2. Cosmetic: PROGRESS.md:239 contains a duplicated fragment,
   "Pattern 0: pattern 0 (46,656 graphs): ...".
3. The finding's own title overstates slightly. "the 'cycles8 POOL6 is closed'
   claim was false as written" is true of RESULTS-RUST.json:160 ("Fable's side
   computation ... had already exhausted the 8-cycle patterns", unqualified),
   but PREDICTIONS.md:14 (table row "cycles8 POOL6 (<=67/40, t<=2)") and
   PREDICTIONS.md:271 ("no object scores <= 67/40 with t <= 2") DO carry an
   explicit t <= 2 qualifier. The accurate criticism — which the finding's
   evidence paragraph makes correctly — is that the scope was inherited from the
   driver's hardcoded loop and nobody had established that t <= 2 was the whole
   feasible range; the residual was undisclosed, not always misstated.

Files written by this adjudication (all under refute/adjudicate/r5/):
  equiv_check.py, lemma_check.py, count_only.py, F1-t3-cycles8.md
