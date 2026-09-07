# Adjudication — finding 6/10 (lens: robustness)

"`--tlimit` on a large index space now returns a RESULT instead of aborting
(streaming chunk enumeration, engine.rs only)" — kind improvement, severity major.

**VERDICT: real = true.  Confirmed by independent reproduction on the current
artifacts.  No overstatement found in the finding text; one overstatement found
in a code comment inside the diff (§7).**

Adjudicator run 2026-09-06 ~22:39–23:05 EDT.  All writes under this directory.
No process signalled.

## 0. Artifacts actually tested (sha256 recorded here)

    A (audited)  rust/target/release/kakeya-search
                 add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9   [matches the contract]
    B (new)      rust/improve/robustness/target/release/kakeya-search
                 0a152c933d0f2c1cf4aabf6fffe4817c78929577f2d03e47abef05bbb8aec79b   [matches the finding]
    .so          src/fastcore_rs.abi3.so
                 03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b   (not exercised; engine.rs is Rust-only)

**Contention disclosure.**  `uptime` load average during this adjudication was
258–280 (the report's own runs were at 13.9–23.3).  Every wall number below is
an upper bound.  Only A-vs-B ratios measured back to back are meaningful.

## 1. Scope check — is the change confined to engine.rs?

Per-file sha256 over every `*.rs` and `Cargo.toml` in `crates/` vs
`improve/robustness/crates/`: the ONLY differing file is
`kakeya-search/src/engine.rs`.  (`fastcore-rs` is absent from the copy;
`Cargo.toml` drops it from `members`, which is the documented reason.)
`diff improve/robustness/engine.rs.orig crates/kakeya-search/src/engine.rs`
is empty — the claimed baseline IS the audited file.  No shim, no second
edit smuggled in, no parameterised constant.

## 2. PROVENANCE — a controlled two-way rebuild (the strongest result here)

This is the check the week's retractions call for ("a fix reported missing from
a binary rebuilt one minute earlier").  I copied `improve/robustness/{crates,
Cargo.toml,Cargo.lock}` into `refute/adjudicate/r5/rebuild/` (a DIFFERENT
absolute path) and built it twice with a private `CARGO_TARGET_DIR`, changing
nothing but `crates/kakeya-search/src/engine.rs`:

    with engine.rs as shipped in the copy   -> ks.NEW
      0a152c933d0f2c1cf4aabf6fffe4817c78929577f2d03e47abef05bbb8aec79b
      == the reported new binary B, byte for byte
      abort repro: RESULT, exit 0

    with engine.rs replaced by engine.rs.orig -> ks.ORIG
      add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9
      == the AUDITED binary A, byte for byte
      abort repro: "memory allocation of 81064793292668928 bytes failed", exit 134

So the build is bit-reproducible across directories, and the **only** difference
between the audited binary and the new binary is the engine.rs diff — nothing
else in the copy contributes, and no hand-placed or stale artifact is involved.
The `+58 -14` in engine.rs is provably both necessary and sufficient for the
behaviour change.  (I restored `rebuild/crates/.../engine.rs` to the new
version after the control build.)

## 3. Required repro — the abort (CONFIRMED)

    $ ./target/release/kakeya-search scan --tag OV --d 2x2x2x2x2 --pool 3 \
        --max-t 0 --target 7/4 --tlimit 2 --threads 1
    memory allocation of 81064793292668928 bytes failed
    Abort trap: 6        EXIT_A=134     real 0m0.029s

    $ ./improve/robustness/target/release/kakeya-search scan --tag OV \
        --d 2x2x2x2x2 --pool 3 --max-t 0 --target 7/4 --tlimit 2 --threads 1
    RESULT {"tag": "OV", "d": [2, 2, 2, 2, 2], "pool": 3, "max_t": 0,
            "target": "7/4", "scanned": 24925, "total": 4611686018427387904,
            "best": null, "hits": 0, "complete": false, "seconds": 2.0}
    EXIT_B=0             real 0m2.061s

Pure-Python oracle, same config (`KAKEYA_PURE_PY=1 /usr/bin/python3 scan1.py
OV 2x2x2x2x2 3 0 7/4 - 2`, cwd `src`, i.e. the PURE-PYTHON kernel, not PyO3):

    RESULT {"tag": "OV", "d": [2, 2, 2, 2, 2], "pool": 3, "max_t": 0,
            "target": "7/4", "scanned": 721, "total": 4611686018427387904,
            "best": null, "hits": 0, "complete": false, "seconds": 2.1}

Every RESULT field except `scanned`/`seconds` agrees with B's, including
`total: 4611686018427387904` and `complete: false`.  (`scanned` is a
wall-clock race by construction.)  My `scanned` numbers differ from the
report's (24925 vs 99742) purely because my box is 12x more loaded.

## 4. Required repro — the wall-clock bound (CONFIRMED, both configs)

`--tlimit 5 --max-t 0 --target 1/8 --d 2x2x2x2 --pool 4 --threads 2`
(the requested "~6 s" gate), back to back:

    B  real 0m5.070s   scanned 4343926    peak RSS 1,134,592 B
    A  real 0m11.836s  scanned 2351808    peak RSS 537,473,024 B

B meets the gate.  A overruns to 2.4x the limit and holds **537 MB** where B
holds **1.13 MB** — 474x.  The report only published B's RSS here; the A-side
number I measured makes "memory is now independent of the index space"
concrete.

I also ran the EXACT config the record's own finding is written against
(`refute/search/finding_tlimit_not_a_bound.txt`: `--d 2x2x2x2 --pool 4
--max-t 1 --target 7/4 --tlimit 5`), which the report did NOT test — it tested
`--max-t 0` variants:

    B --threads 2  real 0m5.070s  scanned 30341
    A --threads 2  real 0m9.298s  scanned 24581

B fixes the recorded config too.  **Caveat on the record, not on the finding:**
PROGRESS.md's OPEN limit says "5 s limit -> 120 s wall on 2x2x2x2 POOL4".  I
could not reproduce 120 s: A gives 9.3 s at `--threads 2` today.  The recorded
120 s was measured at `--threads 8`.  The direction of the finding is
unaffected; the magnitude on record is thread-count-specific and should be
read that way.

## 5. Equality gates (CONFIRMED)

`check --threads 1`, A and B, full 17-line streams captured
(`check.A1.txt`, `check.B1.txt`):

    A: 14 PASS / 2 SKIP / 0 FAIL, exit 0
    B: 14 PASS / 2 SKIP / 0 FAIL, exit 0
    diff after masking the [Ns] bracket -> IDENTICAL

r3 fixtures, `fixtures.sh` with `T=1` against B, normalised with r3's own
`mynorm.py`, diffed against the RECORDED audited streams `r3/out/<id>.rs1.txt`:

    F1 IDENTICAL (242 lines)   F5 IDENTICAL (2678)   P6 IDENTICAL (626)
    F2 F3 F4 F6 F7 P2 P4 P5 IDENTICAL   P3 (552)  P7b (224)  S0 (256)  S123 (258)
    SUMMARY: 15 identical, 0 differ

(The specific check asked for "at least 5 of the r3 fixtures"; 15/15 hold.)

I did NOT re-run `cargo test --workspace` or clippy in the copy — the check
gate plus 15 byte-identical fixture streams is stronger evidence over the one
changed file, and CPU budget was contended.  Those two claims are unverified
by me.

## 6. ORDERING / TIE-BREAK HUNT — the part I was asked to break.  I could not.

### 6a. Never-trip identity (16/16)
For P3, P5, P7b, S0 at `--threads` 1 and 12, with `"seconds"`/`[Ns]` masked:

    B(--tlimit 3600) == A(no --tlimit)   OK   (551 / 1 / 223 / 255 lines)
    B(--tlimit 3600) == A(--tlimit 3600) OK

so the multi-wave dispatch (F1-class configs run 69 chunks over waves of
4,8,16,32 at `--threads 1`) reproduces the ordered no-deadline branch exactly.

### 6b. Prefix invariant under a tripping deadline (16/16)
F1 config, A and B x `--threads` 1,4 x `--tlimit` 0.5,1,2,3.  The complete F1
stream has 120 distinct HITOBJ lines.  In every one of the 16 runs:
`RESULT.hits` == HIT-line count == HITOBJ count, and the HITOBJ sequence is an
exact PREFIX of the complete 120-line sequence.  Table:
`f06_prefix_table.txt`.  Cross-binary the (scanned -> hits) pairs interleave
monotonically — 83->12, 93->16, 114->24, 142->39, 154->44, 165->51, 260->93,
343->120 — i.e. A and B compute the same function of `scanned`, which is what a
buffering change would have broken.

### 6c. Edge cases, A vs B identical
    --threads 0 (rayon auto) + --tlimit 3600 on F1: identical
    --tlimit 0 on --d 1 --pool 3:  both scanned 1, complete true
    --pool 4 (total exceeds u64):  both hit the C6 checked_pow refusal
    --d 2x2x2x2x2 --pool 3 --tlimit 3 --threads 4 (B): RESULT, exit 0

### 6d. The proof I tried to break, and why it holds
The cut-off is "smallest enumeration index never processed".  Two claims:
(i) a wave joining with `stop.tripped()` false skipped nothing, so absorbing it
at `u64::MAX` equals absorbing it at any later cut — `Stop::should_stop` stores
`stopped` BEFORE `min_skipped.fetch_min`, and the rayon join gives the
happens-before edge that makes the Relaxed load non-stale, so tripped==false
after a join really does mean no index was recorded during it;
(ii) `min(first_skipped, frontier)` equals the eager `first_skipped`.  I checked
(ii) is in fact *stronger* than needed: in the trip branch `tripped()` implies
at least one index was recorded, and every dispatched chunk's items lie in
`[0, hi*cs) = [0, frontier)`, so `first_skipped < frontier` always and the
`frontier` term is dead defensive code.  It cannot make the cut wrong.
`Merged::absorb` accumulates NOTHING unconditionally — improvements, hits and
`tested` are all index-filtered with the same `break` — so never dispatching the
tail chunks (whose indices are all >= frontier >= cut) cannot change `best`,
`hits`, `bestobj` or `tested`.  `scanned` uses `cut_out.min(first_skipped)`,
read after all rayon work has joined, so it cannot drift.  I found no
construction that changes a printed byte.

## 7. Where the change is OVERSTATED (against the diff, not the finding)

The new comment block in `engine.rs` asserts, unconditionally:

    "so `--tlimit` is a real wall-clock bound and a huge index space returns
     a RESULT instead of aborting on the chunk vector."

The first half is false in general and the report's own §2.7 says so: at
`--d 2x2x2x2 --pool 4 --max-t 0 --target 7/4 --tlimit 5` B still runs for tens
of minutes, because `Stop::should_stop` is polled once per outer label tuple
and a single `min_generators` DFS can exceed the budget.  The overshoot floor is
per-item, shared with Python, and unrelated to chunking.  **The FINDING text
does not make this error** — its wall-clock table is explicitly scoped
"`--max-t 0 --target 1/8` (cheap items, isolates enumeration overhead)" — so it
does not change the verdict.  But if this diff is ever applied to the audited
tree, that comment should be rewritten to "removes the enumeration-proportional
overshoot; the per-item DFS granularity floor remains" or the next reader will
take the code at its word.

## 8. Reclassification

None.  `improvement` / `major` are right: it closes two limits that PROGRESS.md
carries as OPEN (§204-207) against the shipped binary, it is confined to one
file, and it passes the full equality surface.  It is NOT applied to the
audited tree, and this adjudication does not apply it.
