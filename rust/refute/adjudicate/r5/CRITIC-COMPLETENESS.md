# Completeness critic — closing the arithmetic-kakeya port (2026-09-06, late)

Artifacts under test, re-hashed by me:
`rust/target/release/kakeya-search` sha256 `add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9` (matches the pin);
`src/fastcore_rs.abi3.so` sha256 `03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b`.
Machine CONTENDED throughout (load average 33 at 23:09, several python3.12 jobs from
another session at 50-100% each, 6 physical cores). Every wall/CPU second below is an
upper bound; only back-to-back ratios are meaningful. Nothing written outside this
directory. No process signalled.

---

## 0. Ground-rule check (question 3)

* `git -C "…/arithmetic-kakeya/.." status --short arithmetic-kakeya/rust/crates arithmetic-kakeya/src`
  → **empty output, exit 0.** Clean.
* Whole-tree `git status --short arithmetic-kakeya` → 137 lines, **all `??` under
  `rust/refute/adjudicate/r5/`** (this critic's and the nine adjudicators' scratch).
  Nothing modified, nothing staged.
* `find rust/crates src tests logs results.json rust/RESULTS-RUST.json KAKEYA-WORKBENCH.md
  REPORT.md -newermt '2026-09-06 16:00'` returns five paths, all accounted for:
  `rust/RESULTS-RUST.json` and `rust/crates/kakeya-search/PROGRESS.md` (the orchestrator's
  own manual triage, declared in SWEEP-2026-09-06.md), `logs/rust-cycles8_8cycle.log` and
  `logs/rust-targets.log` (written by the 8-cycle job itself), and
  `src/__pycache__/fastcore.cpython-312.pyc` — a stray `.pyc` under `src/` from something
  importing `fastcore` under Homebrew python3.12. Harmless, but it is a write inside `src/`;
  `src/__pycache__` should be gitignored so this cannot recur ambiguously.
* `grep -rlE '\b(pkill|killall|kill -|os\.kill|\.kill\(|SIGKILL|SIGTERM)\b' rust/refute rust/improve`
  → 9 files, **every one a `.md`** quoting the rule in prose. No script contains a kill.
* Both long jobs ended normally: 8-cycle `exit=0` 2026-09-06T20:46:00Z, `tested: 81660`;
  `refute/search/r3/out/C8.py.txt` written, 131 B, byte-identical to `C8.rs1.txt`/`C8.rs12.txt`.

**No ground-rule violation found.** Caveat: this is a filesystem + one-git-status judgement.
A write that was made and reverted to identical bytes is undetectable from here.

---

## 1. THE MATERIAL GAP NOBODY RAN: g2_tall searches only t ∈ {0,1}

This is the exact analogue of the science lens's cycles8 `t = 3` find, in the driver that
produced three of the campaign's headline negatives, and it is still open.

`src/g2_tall.py:61` — `run(rows_, max_t=1, tlimit=700)`.
`rust/run_targets.sh:8,10` — `g2-tall --rows 5 --max-t 1`, `--rows 6 --max-t 1`.
Every recorded g2_tall run (2x4 complete, 2x5 7207 s, 2x6 14558 s) is `max_t = 1`.

Feasibility, computed from the driver's own cap rule
(`cap = int(11/6·q); if cap/q >= 11/6: cap -= 1; budget = cap - G.m`, q = n - t),
with `m` ranged over all POOL3 label tuples (`ConstructibleGraph(X,[2,rows],[{(1,):(1,0)},f2])`):

| rows | n | m range | t=2 (q, cap, max budget) | t=3 | t=4 |
|---|---|---|---|---|---|
| 4 | 8  | 4–10 | q=6, cap=10, **budget ≤ 6** | q=5, cap=9, ≤5 | q=4, cap=7, ≤3 |
| 5 | 10 | 5–13 | q=8, cap=14, **budget ≤ 9** | q=7, cap=12, ≤7 | q=6, cap=10, ≤5 |
| 6 | 12 | 6–16 | q=10, cap=18, **budget ≤ 12** | q=9, cap=16, ≤10 | q=8, cap=14, ≤8 |

t = 2, 3 and 4 are all budget-feasible for every row count, with large budgets — unlike the
cycles8 t=3 case, which was razor-thin (budget exactly 0, r = 0 forced). Nothing in the
record scopes the g2_tall negatives to t ≤ 1, and `PROGRESS.md:147` uses the unqualified
"g2_tall: nothing beats the 11/6 cap" as the justification that the g2_tall improvement
print line is never fired — silently inherited from the driver's hardcoded `max_t=1`,
exactly the failure mode the t=3 find was supposed to teach.

**It is cheap to close.** Measured tonight on the audited binary, contended:

    ./target/release/kakeya-search g2-tall --rows 4 --max-t 1 --threads 4
    RESULT {"tag": "g2_tall_2x4", …, "max_t": 1, "best": null, "hits": 0,
            "complete": true, "seconds": 395.7, "walked": 4096, "total": 4096, "pairs": 31718}
    395.77 real  728.11 user  14.63 sys        (critic_g2t_r4_mt1.txt)

    ./target/release/kakeya-search g2-tall --rows 4 --max-t 2 --tlimit 150 --threads 4
      [2x4] TIME LIMIT
    RESULT {…, "max_t": 1, "best": null, "hits": 0, "complete": false,
            "seconds": 151.0, "walked": 623, "total": 4096, "pairs": 12152}
    150.98 real  334.65 user   7.23 sys        (critic_g2t_r4_mt2_probe.txt)

623/4096 tuples ⇒ a complete `--max-t 2` 2x4 is ≈ 79,900 pairs (2.5× the max_t=1 run) at
27.5 ms/pair ⇒ **≈ 2,200 CPU-s ≈ 37 CPU-min contended.** The cheapest unexplored modality
in the tree, and the one that would most change how the negatives read.

### 1b. The run that closes it mislabels itself
`drivers/g2_tall.rs:184` prints the literal `\"max_t\": 1` in the RESULT format string;
`src/g2_tall.py:63` does the same. The port is faithful — this is not a divergence — but
my `--max-t 2` probe above printed `"max_t": 1`, so any t=2 log is self-mislabelling.
Fix the emitter (both sides, or Rust only with a disclosed divergence) BEFORE running.

---

## 2. Everything else still missing (question 1)

**A comparison still on the wrong kernel.** The `g2-tall 2x4` coverage row's only complete
Python side is `refute/search/py_g2tall_2x4_rskernel.txt` (148 B, PyO3 kernel, 1968.2 s).
The pure-Python-era attempt `logs/g2_tall.log` reads `complete: false, seconds: 703.3`.
Disclosed row-by-row now; still a driver-level check. Cost of closing ≈ 5.5 CPU-h
(FINDING-07 measured a 10.0x kernel ratio by CPU at rows=3).

**Coverage rows with no artifact.** `scan --d 6` (sweep `c12` Python side 0 bytes) and
`scan --d 2x2x2` (`s17b`/`s18`/`s19` never run). Both marked **UNSUPPORTED ON DISK** in the
map — correct — but neither has been filled. FINDING-09: `--d 6` is cheap at small
`--limit`; the exhaustive 46,656-label version needs ≈ 4.6 h pure Python.

**A row whose prose still contradicts its own map entry.** `PROGRESS.md:56-62` still reads
"stacked POOL4 max_t=1 vs `oracle_drivers.py stacked 4 1`: identical except the `[Ns]`
elapsed … the 12-thread Rust run reproduces exactly that" — no kernel disclosure, no note
that BOTH Python artifacts (`py_stacked_p4_t0.txt`, `py_stacked_p4_t1_rskernel.txt`) are
0 bytes. The coverage-map row four dozen lines below says the opposite. The cycles8 bullet
immediately underneath got a full disclosure paragraph; this one got none.

**A README gate that cannot pass as written.** README "Gates (all must be green…)" line 5:

    cd ../rust/refute/record/r5 && /usr/bin/python3 verify_traps.py   # 119/119 traps + 16/16 VERIFIED

    → EXIT 1: AssertionError: NOT pure python! set KAKEYA_PURE_PY=1   (verify_traps.py:8)

    KAKEYA_PURE_PY=1 /usr/bin/python3 verify_traps.py
    → EXIT 0.  VERIFIED.md rows checked: 17 call-forms (16 numbered rows), mismatches=0
               traps.json entries: 119, mismatches vs current pure-Python fastcore: 0
      (critic_verify_traps_pure.txt)

The one gate in the list that polices kernel substitution is the one written without the
kernel switch. The gate itself is sound; the README line is not.

**PyO3 timings labelled pure Python inside the correction.** `PROGRESS.md:236-240` and
`SWEEP-2026-09-06.md:30` present "13.6 s / 33.2 s" as pure-Python reproductions of
`t3_check.py`. FINDING-01 measured 31.7 s of pure-Python CPU on those same 87,600 pairs
(2,760 pairs/s), so 13.6 s wall is below the pure-Python floor; both reproductions ran the
PyO3 kernel. Counts are unaffected (F1 ran both kernels; identical). The 567 s pattern-0
figure IS genuinely pure Python and is correctly labelled. Same line carries a duplicated
fragment: "Pattern 0: pattern 0 (46,656 graphs):".

**Stale figures still in `COMMANDS.md`.** §4 heading (line 37) "Differential sweep over
**37** scan configurations" — corrected only by a note four lines below whose own text says
"Do not quote … 37"; line 43 still enumerates `d in {2,3,4,5,6,…,2x2x2,3x3,2x2x2x2}`, and
`6` and `2x2x2` are precisely the two shapes with no artifact; §9 lines 77-78 still print
"62 + 13 = **75** passed" twice, annotated at line 79 rather than corrected. `12/12`,
`11 PASS`, `135 traps`, `30/30` and `"only unsettled region"` are all clean in the canonical
docs (each survives only inside its own explicit correction sentence).

**Unfixed known limit.** `scan --tlimit 0`: Rust = 0 s limit, Python `if tlimit and …`
(`search.py:209`) = no limit. Listed OPEN; a one-line fix waiting on a rebuild.

**Modalities never run at all.**
* `stacked --pool 8` — the ONLY pool where FINDING-03's monotonicity argument does not close
  the hit block. POOL3–6 are provably empty at every `max_t` and every `--target`; POOL8 is
  open at t ≤ 2. Nothing in the tree runs it.
* `cycles8 --pool 8` — 303,616 label tuples vs POOL6's 57,240. Never run.
* No run varies the slope modulus at n > 4 ("complete" sweeps are complete in the labellings
  at a single point in the modulus space).
* The **permissive** (non-matching-suffix) reading of Operation 1: `grep -rn permissive
  rust/crates` = 0. The Rust binary cannot express it, and negatives do not transfer between
  the readings (FINDING-04 exhibited 456 configurations valid under permissive and invalid
  under matching-suffix at identical score). FINDING-04 also supplies the closing argument —
  a permissive-valid 4-vertex object scores 5/3 = 1.6667 < 1.675 < γ, so the permissive
  reading would make the Epoch problem trivial and Katz–Tao not a record, hence it is
  untenable — but that argument lives only in an untracked adjudicate file; SWEEP §E still
  files the ambiguity as open.

**Two arguments that exist only in untracked adjudicate files.** FINDING-03's proof that
`stacked` has no hits at t ≥ 3 for any pool and any target (m ≥ 8 ⟹ t ≥ 4 infeasible;
t = 3 forces m = 8 and r = 0, and 0 of 56 3-subsets force on the edge rows), and FINDING-04's
permissive-reading disposal above. `PROGRESS.md:147`'s "stacked: empty for POOL3-6 by pool
monotonicity on the complete POOL4/6 runs" is true but its `max_t ≤ 2` qualifier was omitted
without an argument being on the page — correct by luck until FINDING-03 supplied one.

**An erratum that is itself wrong.** `PREDICTIONS.md` §7 bullet 2 withdraws §6's
">10x" on the 2x5 estimate. FINDING-10 (the only refuted lens finding) shows the withdrawal
is unsound: the "~2.5x" compares wall-on-8-threads against §4's *sequential* 0.5–2 h; the
"upper bound" premise is backwards (cost per pair rises 2.7x across the first 14% of a
complete 2x4, so a prefix probe is a LOWER bound); and `run_targets.sh:5` `T=8` × the recorded
7,207 s = **16.0 thread-hours already burned without completing**, which excludes the low
estimate outright. Honest number: ≈ 25–40 CPU-h, i.e. 12–73x over §4 in §4's own currency.
The claim should be restored with a number, not withdrawn. `SWEEP §A.11`'s "12–41 CPU-hours"
inherits the same error and its low end is excluded by the recorded run.

**A false provenance sentence in the perf prototype.** `improve/perf/REPORT.md` §8:
"lines 1-368 byte-identical to the audited crate (verified by diff)" — two lines are inserted
into `ForceScratch` (kperf 78-79) and `#[cfg(test)] mod tests;` is dropped. The finding card's
"no change to search.rs or any driver" is wrong of the prototype as built (`search.rs:9`
reroutes to `kakeya_core::perf::force_sel`), and `rzero` appears in the "diff-clean driver
streams" list although `drivers/rzero.rs` was never rerouted, so its diff-clean is vacuous
and rzero gets 0x from this prototype.

---

## 3. Is "cycles8 POOL6 is closed at every t" true, and honestly scoped? (question 2)

**True, as a statement about the cycles8 slice, on deliberately mixed evidence:**
* t = 3, all five patterns, **exhaustively**: 1,692,000 (graph, T0) pairs, 0 hits.
* t ≤ 2, the two 8-cycle patterns: the completed Lemma-C-free Rust run, `tested: 81660`,
  exit 0 (`logs/rust-targets.log:26-27`), plus Fable's Lemma-C side computation.
* t ≤ 2, the three two-4-cycle patterns: **by the analytic mediant argument** of
  PREDICTIONS §2.2 — NOT exhausted. The only Rust run there covered an exact prefix of
  pattern 0 (98,973 of 1,557,900 pairs).
* t ≥ 4: budget-infeasible.

Two scope facts nothing on disk says: the closure is **target-specific** (at `--target 2`
the same arithmetic makes t = 4 feasible: den = 4, int(8) − 8 = 0, 8/4 = 2 ≤ 2 — and
`--target` is a user-settable flag on the Rust side, so the hardcoded `(0,1,2)` loop is a
scope defect for any target a user passes, not only 67/40); and POOL8 cycles8 is not run.

Honesty by location:
* **README.md** — best statement in the tree. Names both routes, names the mediant argument
  as the two-4-cycle route, gives 6.95%, says "not n = 8 closed". Nothing to fix.
* **PROGRESS.md:242-246** — honest, same content, plus "`--deg` is vacuous for every value
  but 2". Marred only by the mislabelled 13.6 s / 33.2 s above and the duplicated fragment.
* **PREDICTIONS.md §7** — honest; the pre-registered §0 row carries its own `t<=2` in the
  header and the erratum is appended rather than edited in. Correct practice.
* **HANDOFF-RUST-GO-PORTS-2026-09-05.md:123** — honest (closed at every t, 6.95%, not n=8).
  Its §C block at line 29 still describes the 8-cycle run as "started"/"if it finishes";
  cosmetically stale but the addendum at 123 supersedes it.
* **RESULTS-RUST.json — the weak one.** `notes[3]` states "cycles8 POOL6 is closed at every t"
  with no 6.95% caveat and no mention that the two-4-cycle t ≤ 2 half is analytic. Worse,
  `notes[0]` still carries, unamended, "Fable's side computation … **had already exhausted
  the 8-cycle patterns** with 0 hits" — the unqualified sentence FINDING-01 named as the one
  place the pre-t3 claim was stated without scope. Run 6's `covers` field ("all 81,660 pairs
  at t <= 2") and `residual_note` ARE accurate, so a careful reader recovers the scope; a
  skimmer reading `notes` does not.

---

## 4. Adoption order and regate recipe (question 4)

**`improve/robustness/` first. `improve/perf/` second, as its own task.**

Why robustness first: one file (`engine.rs`); `engine.rs.orig` is byte-identical to the
audited file; FINDING-06 rebuilt the workspace from a different absolute path with a private
`CARGO_TARGET_DIR` and got `add55418…` from the orig and `0a152c93…` from the shipped
engine.rs, so the diff is provably necessary AND sufficient for the behaviour change; it
touches no math, no kernel and no `.so`, so `difftest.py` and the 119 traps are untouched by
construction; it closes two OPEN limits; and the ordering hunt failed to move a printed byte
(16 never-trip identity runs; 16 tripping-deadline runs where `RESULT.hits` == HIT-line count
== HITOBJ count and the HITOBJ sequence is an exact prefix of the complete 120-line stream,
with A and B interleaving monotonically on (scanned → hits)).

Why perf second: it changes `kakeya_core::force`, on which every result in the tree rests;
it needs a new `.so` (new sha, new disclosure, `difftest.py` and the traps must be re-run);
and its own REPORT carries a false provenance sentence. Take levers A + C' + D only; leave
lever B (the composite-p one that already produced a wrong prototype) out.

### Regate recipe — robustness
1. Record the pre-change state: `shasum -a 256 rust/target/release/kakeya-search` =
   `add55418…`; save `check --threads 1` and `--threads 12` streams as the reference.
2. Apply `improve/robustness/engine.diff` to `crates/kakeya-search/src/engine.rs` ONLY.
   **Rewrite the comment at `engine.rs:219`** — "`--tlimit` is a real wall-clock bound" is
   false, and the prototype's own REPORT §2.7 says so: the per-item `min_generators` DFS
   granularity floor remains and is shared with Python. Replace with: "no chunk past the
   deadline is visited and nothing proportional to the index space is allocated; the residual
   overshoot is one item's DFS, as in Python."
3. `cd rust && cargo build --release -p kakeya-search`; record the new sha. Expect
   `0a152c933d0f2c1cf4aabf6fffe4817c78929577f2d03e47abef05bbb8aec79b` when the build path and
   flags match FINDING-06's; a different sha is a build-environment difference, not a failure
   — re-derive and re-pin it.
4. Equality gates: `check --threads 1` and `--threads 12` → 14 PASS / 2 SKIP / 0 FAIL and
   byte-identical to step 1 after masking `[Ns]`; `cargo test --release --workspace` → 78;
   `cargo clippy --release --all-targets --workspace -- -D warnings` → exit 0.
5. Replay gates (the binding ones): the 15 r3 fixtures through `r3/mynorm.py` byte-identical
   (FINDING-06 got 15/15 — F1 242 lines, F5 2678, P6 626); the complete `scan n4_p6_t1`
   241-line stream; `cycles8 --pool 3 --target 67/40 --deg 2` byte-identical with NO masking;
   `stacked --pool 4 --max-t 2` and `--pool 6` against `logs/stacked.log` (concatenate
   `logs/rust-stacked_pool4.log` + `logs/rust-stacked_pool6.log`, mask only `[Xs]` — they are
   md5-equal only as a concatenation, not file-by-file; the coverage-map row should say so).
6. Never-trip identity: ≥ 4 configs × {1, 12} threads, new `--tlimit 3600` == old
   `--tlimit 3600` == old with no `--tlimit`.
7. Closure gates: `--d 2x2x2x2x2 --pool 3 --max-t 0 --target 7/4 --tlimit 2` returns a RESULT
   (was exit 134, "memory allocation of 81064793292668928 bytes failed");
   `--d 2x2x2x2 --pool 4 --max-t 1 --target 7/4 --tlimit 5` honours the limit.
8. `difftest.py` and `verify_traps.py` (WITH `KAKEYA_PURE_PY=1`) need no re-run — kernel and
   `.so` unchanged. Say so explicitly rather than silently skipping them.
9. Re-pin the sha in all four places it is quoted: `README.md` (the "Record the sha256" block
   AND the clean-clone sentence), `PROGRESS.md:205`, `RESULTS-RUST.json` notes[3], and the
   handoff. Move both `--tlimit` entries from OPEN to FIXED, dated. State that all six
   recorded runs came from the pre-change binary; runs 1, 2 and 6 carried no `--tlimit` and
   reproduce unchanged, while runs 3, 4, 5 are time-limited prefixes whose `scanned`/`walked`
   will differ under the new binary — do not re-quote those three as byte-reproducible.
10. Only then start perf as a separate gated task: rebuild the `.so`, re-run `difftest.py`
    and the 119 traps against it, re-pin the `.so` sha in README and PROGRESS.md, and fix
    REPORT §8's provenance sentence and the rzero/search.rs claims before banking it.

Note on the README clean-clone sentence: `83fd36c` is real (it is the tip-minus-2 of the
standalone repo `goodcarp/arithmetic-kakeya`, remote `kakeya`, reachable as
`remotes/kakeya/main~2`; the monorepo HEAD is a different history, which is why
`git merge-base --is-ancestor 83fd36c HEAD` says no). The binary sha is unaffected by the two
later doc commits, so the claim holds — but a reader cloning at `83fd36c` gets `PROGRESS.md`
BEFORE the `30/30` and `136`-trap fixes. Re-cite to the current tip (`0b78b4d`).

---

## 5. Ranked by what a reader would most be misled by if left

1. **g2_tall t = 2/3/4 never searched**, and `PROGRESS.md:147` says "g2_tall: nothing beats
   the 11/6 cap" unqualified. Three headline negatives read as covering the driver's feasible
   phase range; they cover t ≤ 1. Same class as the find that justified this whole sweep, and
   the record has not generalised the lesson. ~37 CPU-min to close 2x4.
2. **`PROGRESS.md:56-62` contradicts its own coverage map** about the 0-byte stacked
   POOL4 max_t=1 row. A reader hitting the prose first banks a comparison that has no
   Python side.
3. **`RESULTS-RUST.json` notes**: the unqualified "had already exhausted the 8-cycle
   patterns" and a closure sentence with no 6.95% / no analytic-half caveat. It is the file
   an automated consumer reads.
4. **README gate 5 fails as written** (missing `KAKEYA_PURE_PY=1`) — a gate list where one
   gate cannot be green destroys the value of the list.
5. **13.6 s / 33.2 s labelled pure Python** in PROGRESS.md and SWEEP — the disclosed defect
   class recurring inside the correction that closed it.
6. **PREDICTIONS §7's 2x5 withdrawal is unsound** and withdraws a claim that measurement
   supports (16.0 recorded thread-hours already exceed the estimate 8-fold).
7. **The permissive reading**: every negative is conditional on it, the Rust binary cannot
   test it, and the argument that settles it is only in an untracked file.
8. `--d 6` / `--d 2x2x2` rows and the g2-tall 2x4 wrong-kernel row — correctly disclosed, so
   under-served rather than misleading.
9. COMMANDS.md's stale §4 heading / d-list / "75 passed"; perf REPORT §8's provenance.
10. `--tlimit 0`, `stacked --pool 8`, `cycles8 --pool 8`, modulus variation at n > 4 —
    correctly carried as open.
