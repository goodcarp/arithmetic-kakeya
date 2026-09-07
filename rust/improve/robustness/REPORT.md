# improve/robustness — streaming chunk enumeration for `--tlimit`

Scout task, 2026-09-06.  Nothing under `crates/`, `src/`, `results.json`,
`logs/`, `tests/`, `RESULTS-RUST.json`, `PROGRESS.md`, `REPORT.md` or
`KAKEYA-WORKBENCH.md` was touched.  All work is a COPY of the workspace under
`rust/improve/robustness/`, built there.

  audited binary (A)  rust/target/release/kakeya-search
                      sha256 add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9
  new binary     (B)  rust/improve/robustness/target/release/kakeya-search
                      sha256 0a152c933d0f2c1cf4aabf6fffe4817c78929577f2d03e47abef05bbb8aec79b

**Contention disclosure.**  Every wall-clock number below was measured on a
machine running, concurrently: pid 12158 `ks8run` (~5 of 6 physical cores), pid
13369 the pure-Python cycles8 POOL3 oracle, and a second improvement agent's
benchmark sweep.  `uptime` load average during the measurements ranged 13.9 to
23.3.  Wall numbers are upper bounds, not benchmarks; the *ratios* between A and
B measured back-to-back are the meaningful part.

---

## 1. The change

One file, `crates/kakeya-search/src/engine.rs`, `+58 -14` lines
(`engine.diff` in this directory; `engine.rs.orig` is the unmodified original).
`Cargo.toml` in the copy drops `fastcore-rs` from the workspace members so the
copy builds without pyo3; `kakeya-core` and `kakeya-search` are byte-identical
copies of the audited sources (`diff -r` clean at copy time).

### What it replaces

```rust
// audited engine.rs:212-227 (the --tlimit branch)
let outs: Vec<ChunkOut> = pool.install(|| {
    (0..nchunks).into_par_iter().map(|ci| { ... chunk_fn(start, end, &stop) }).collect()
});
let stop_at = stop.first_skipped();
let mut m = Merged::default();
for c in &outs { m.absorb(c, stop_at, ...); }
```

`nchunks = total.div_ceil(4096)`.  Two consequences, both in PROGRESS.md's
"Known limits" as OPEN:

* the `Vec<ChunkOut>` is allocated proportional to the whole index space, so a
  config whose `total` fits u64 but whose `total/4096` is astronomic aborts
  (`memory allocation of 81064793292668928 bytes failed`, SIGABRT, exit 134);
* every chunk is visited even after the deadline trips, so `--tlimit` is not a
  wall-clock bound (chunk-walk cost proportional to the index space).

### With

Wave-based streaming dispatch.  Chunks go out in strictly increasing order,
`wave` chunks at a time; each wave is absorbed as soon as it joins; dispatch
stops at the first wave in which the deadline trips.  `wave` starts at
`threads*4` and doubles to a `threads*256` cap, so a long run pays O(log)
dispatches and a short one keeps the barrier small.

```rust
let mut m = Merged::default();
let mut ci: u64 = 0;
let mut cut: u64 = u64::MAX;
let threads = opts.threads.max(1) as u64;
let mut wave: u64 = threads * 4;
let max_wave: u64 = threads * 256;
while ci < nchunks {
    let hi = ci.saturating_add(wave).min(nchunks);
    let outs: Vec<ChunkOut> = pool.install(|| {
        (ci..hi).into_par_iter()
            .map(|c| chunk_fn(c * cs, ((c + 1) * cs).min(opts.total), &stop))
            .collect()
    });
    ci = hi;
    if stop.tripped() {
        let frontier = ci.saturating_mul(cs).min(opts.total);
        cut = stop.first_skipped().min(frontier);
        for c in &outs { m.absorb(c, cut, opts.print_improvements, opts.print_hits); }
        break;
    }
    for c in &outs { m.absorb(c, u64::MAX, opts.print_improvements, opts.print_hits); }
    wave = wave.saturating_mul(2).min(max_wave);
}
```

and `scanned` is computed from `cut.min(stop.first_skipped()) + 1` instead of
`stop.first_skipped() + 1`.

### Why ordering and tie-breaks are unchanged

The audited engine buffers every progress line under `--tlimit` because a line
can only be published once the global cut-off index is known.  The cut-off is
defined as **the smallest enumeration index that was never processed** —
`Stop::should_stop` `fetch_min`s the index of every item it refuses, and
`Merged::absorb` drops everything at or above it.  Two facts make the streaming
version produce the same number and therefore the same bytes:

1. **A wave that joins with `stop.tripped()` still false skipped nothing.**
   `should_stop` sets `stopped` before it records any index, monotonically, and
   we read the flag after the join.  So every index in that wave was processed,
   every one of them is strictly below any future cut-off, and absorbing (and
   printing) it immediately cannot be retracted.  This is what removes the
   buffering for the pre-trip part of the run without changing what is printed
   or in what order.
2. **The trip wave's cut-off is `min(first_skipped, frontier)`.**  Rayon runs
   every chunk of a dispatched wave, so a chunk that starts after the trip is
   still *entered*, refuses its first item, and records its own start index —
   exactly as in the eager version.  The only indices the eager version saw that
   we do not are those in chunks we never dispatch, and they all start at or
   after `frontier`, of which `frontier` itself is the least.  So
   `min(first_skipped, frontier)` is the same value the eager `first_skipped`
   was.

Nothing else moved: chunk size, chunk boundaries, `Merged::absorb`, the
`sc < best` improvement rule, the "ties go to the lowest enumeration index"
merge, and the no-deadline branch are untouched.

---

## 2. Verification

### 2.1 `check` — required to be identical to the audited binary

    $A check --threads 1   ;  $B check --threads 1
    $A check --threads 12  ;  $B check --threads 12

14 PASS / 2 SKIP / 0 FAIL, exit 0, in all four runs.  A vs B at the same thread
count differ **only** in the per-fixture `[Ns]` bracket; after masking `[Ns]`,
A@1, A@12, B@1 and B@12 are all the same 17 output lines.
Files: `out/check_{A,B}_{1,12}.txt`.

### 2.2 The r3 fixtures, `--threads 1` and `--threads 12`

`fixtures.sh` replays F1–F7, P2–P7b, S0, S123 (commands reconstructed from
`refute/search/r3/out/*.py.txt` RESULT lines and `probe.sh`), normalised with
r3's own `mynorm.py` (masks only `"seconds"` and `[Ns]`):

| compared against | result |
|---|---|
| the recorded audited-binary streams `r3/out/*.rs1.txt` (B at `--threads 1`) | **15/15 IDENTICAL** |
| the recorded audited-binary streams `r3/out/*.rs12.txt` (B at `--threads 12`) | **15/15 IDENTICAL** |
| the recorded PURE-PYTHON streams `r3/out/*.py.txt` (B at `--threads 1`) | 13/15 IDENTICAL; F6 and F7 differ by exactly the three disclosed Rust-only `g2-tall` keys `walked`/`total`/`pairs` and nothing else |

F1 = 242 lines (120 HIT + RESULT + 120 HITOBJ + EXIT), F5 = 2678 lines,
P6 = 626, P3 = 552.  Files: `out/fx_B_t1/`, `out/fx_B_t12/`.

### 2.3 Other drivers, no `--tlimit` (A vs B, `--threads 2`, `"seconds"`/`[Ns]` masked)

    cycles8 --pool 3 --target 67/40 --deg 2 --patterns 8cycle   IDENTICAL
    stacked --pool 4 --max-t 1                                  IDENTICAL
    rzero --d 2x4 --pool 4 --seed 0                             IDENTICAL

### 2.4 Gates in the copy

    cargo test --workspace                                    62 + 16 + 0 + 0 + 0 = 78 passed, 0 failed
    cargo clippy --release --all-targets --workspace -- -D warnings    exit 0, clean

### 2.5 The abort — REQUIRED REPRO, now returns

    scan --tag OV --d 2x2x2x2x2 --pool 3 --max-t 0 --target 7/4 --tlimit 2

| | output | exit | wall |
|---|---|---|---|
| A `--threads 1` | `memory allocation of 81064793292668928 bytes failed` | 134 | 0.013 s |
| B `--threads 1` | `RESULT {... "scanned": 99742, "total": 4611686018427387904, ... "complete": false, "seconds": 2.0}` | 0 | **2.027 s** |
| B `--threads 2` | same shape, `scanned` 161756 | 0 | 2.014 s |
| B `--threads 12` | same shape, `scanned` 236610 | 0 | 2.013 s |
| pure-Python `scan1.py OV 2x2x2x2x2 3 0 7/4 - 2` | `RESULT {... "scanned": 4200, "total": 4611686018427387904, ... "complete": false, "seconds": 2.0}` | 0 | 2.544 s |

Every RESULT field except `scanned` and `seconds` agrees with Python's,
including the `total` 4611686018427387904 and `complete: false`.  `scanned`
is a wall-clock race by construction (documented); B scans 24–56x more label
tuples than pure Python in the same 2 s, which is the expected direction.

Peak RSS (`/usr/bin/time -l`, `--threads 2`): A aborts having reached 872 KB;
B returns with **1.26 MB**, and 1.14 MB on the 5^15 space while scanning 25.2 M
items.  Memory is now independent of the index space.

### 2.6 `--tlimit` as a wall-clock bound

`--tlimit 5`, all `--max-t 0 --target 1/8` (items rejected by the `m > m_cap`
filter, so per-item cost is negligible and the measurement isolates enumeration
overhead — this is the exact shape of `refute/search/finding_tlimit_abort.txt`):

| config | `total` | B wall | B `scanned` |
|---|---|---|---|
| `--d 2x2x2x2 --pool 4 --threads 1` | 30 517 578 125 | **5.019 s** | 11 759 508 |
| `--d 2x2x2x2 --pool 4 --threads 2` | 30 517 578 125 | **5.012 s** | 21 924 852 |
| `--d 2x2x2x2 --pool 6 --threads 2` | 4 747 561 509 943 | **5.014 s** | 21 769 797 |
| `--d 2x2x2x2x2 --pool 3 --threads 2` | 4 611 686 018 427 387 904 | **5.018 s** | 11 487 729 |

Pure Python on the middle two, same limit: 5.476 s / 5.434 s wall, `scanned`
286 280 and 115 242, all other RESULT fields equal.  So B is now *tighter* to
the deadline than the Python it reproduces, on any index space.

The requested target — "honour a 5 s tlimit within ~6 s wall on
`--d 2x2x2x2 --pool 4`" — is met: 5.012–5.019 s.

### 2.7 What the fix does NOT fix (measured, and it is not new)

`--d 2x2x2x2 --pool 4 --max-t 0 --target 7/4 --tlimit 5 --threads 2` still
overruns badly, in **both** binaries:

* A: returned after **3012.7 s** (50 min 13 s wall) with `scanned` 97 658.
* B: still running when this report was written (21 min wall, 21 min CPU at the time of writing).

The cause is not the chunk enumeration.  It is the deadline's *granularity*:
`Stop::should_stop` is checked once per outer label tuple, so the floor on
overshoot is the cost of one `min_generators` DFS, and at `target 7/4` on this
box the budget is `int(7/4*16) = 28` and single tuples run for many minutes.
Direct evidence, no `--tlimit` at all: `scan --d 2x2x2x2 --pool 4 --max-t 0
--target 7/4 --limit 20 --seed 11 --threads 1` — **20 label tuples** — had
consumed 13 min 07 s of CPU and had not finished.  On the same box at
`--pool 3` (4^15 space), A and B agree exactly (`scanned` 21847 both) and both
overshoot 5 s by 1.8 s / 2.8 s, again per-item, not per-chunk.

This granularity is shared with Python (`g2_tall.py` / `search.scan_dims` also
test the clock once per outer tuple and `min_generators` has no internal
deadline).  Python does not *show* it on this config only because in 5 s it
reaches index 1585 and never meets an expensive tuple.  So: not a divergence,
and not something the streaming change could address.  Closing it needs a
deadline *inside* `min_generators`, which changes results (a partially searched
tuple is not the same as an unsearched one) — see §4.

### 2.8 Ordering invariants under `--tlimit` (the part most at risk)

`scan --d 2x2 --pool 6 --max-t 1 --target 7/4` (the F1 fixture: 343 tuples,
120 HIT lines when complete), run with a deadline:

* `--tlimit 3600` (never trips), `--threads 1` and `--threads 12`: output is
  **identical to the audited no-tlimit F1 stream**, all 241 lines.
* deadline tripping mid-run, 12 runs (`--threads` 1 and 12 x `--tlimit`
  0.05/0.15/1/2/3, A and B):  in every run the printed HIT lines are an exact
  **prefix** of the complete 120-line HIT stream, `RESULT.hits` equals the HIT
  line count equals the HITOBJ count, and `scanned` is monotone in the limit.
  A and B agree on `(scanned, hits)` in 11 of the 12 pairs; the one that differs
  (`--threads 1 --tlimit 1`: A 147/43, B 153/44) is the documented wall-clock
  race, and B's stream is still a prefix of the same complete stream.
* `g2-tall --rows 4 --max-t 1 --tlimit 3 --threads 2`, A vs B:
  byte-identical except `seconds` — same `  [2x4] TIME LIMIT` line, same
  `walked: 40`, `total: 4096`, `pairs: 308`, same `complete: false`.

---

## 3. Item (2): `g2_tall` `complete` semantics and the three Rust-only keys

**Proposal only — not applied.**  Facts first.

* Python `g2_tall.py.__main__` calls `run(rows_, max_t=1, tlimit=700)` and
  prints `"complete": (el < 700)` with the 700 hardcoded in both places, so for
  every run that driver can perform, `el < 700` is a correct completeness test.
  `oracle_drivers.py g2-tall` calls `run(..., tlimit=1e9)` and still prints
  `el < 700`, so **the oracle harness prints `complete: true` for any run under
  700 s even when it tripped its 1e9 limit** — vacuous in practice.  Rust
  prints `complete: !time_limit_tripped`.  They differ only for a run given
  `--tlimit > 700` that finishes between 700 s and that limit; PROGRESS.md's
  scope note is right and r3's finding B came from a shim that made `tlimit`
  settable while copying `(el < 700)` verbatim.
* Rust appends `"walked"`, `"total"`, `"pairs"` after `"seconds"`.  Values are
  independently confirmed (r3 §4 `pairs_g2.py`: 2x2 walked 16 pairs 59,
  2x3 max_t1 pairs 1587, 2x3 max_t2 pairs 3426).  A plain `diff` against a
  Python log fails on the tail.

**Minimal way to make the default output byte-identical to Python**, if that is
what the record wants — two edits, both in `drivers/g2_tall.rs::emit` plus one
CLI flag in `main.rs`:

1. Add `--extra-keys` (default off) to the `g2-tall` arm; thread it into
   `TallCfg` as `extra_keys: bool`.
2. In `emit`, print the Python line up to `"seconds"` and close the brace;
   append `, "walked": …, "total": …, "pairs": …` only when
   `cfg.extra_keys`.
3. Leave `complete` alone (`!time_limit_tripped`) but document that with
   `--tlimit > 700` the Rust is the honest one; if byte-identity is wanted even
   there, gate it as `complete: if cfg.python_complete { elapsed < 700.0 } else { !stopped }`
   behind the same flag — that is 3 lines and it makes the binary print a value
   it knows to be false, which is why I would not do it.

**Trade-off.**  Against: `walked`/`total`/`pairs` are the only progress signal a
TIME LIMIT run emits (`hits` and `best` are `null` on every g2_tall run on
record), and PROGRESS.md's 2026-09-06 item 2 uses them as the gate against
Fable's independent `count_pairs.py` — hiding them by default means the
long-run monitoring path and the check fixture both have to pass the flag, and
a future operator diffing two Rust logs loses the counters silently.  For:
"reproduces the Python drivers" becomes literally true for `g2-tall`, and
`diff` against a Python log stops needing a `sed` to strip the tail.

My recommendation: **do not flip the default.**  Instead make the difference
un-missable and cheap to strip — keep the keys, and add `--python-compat` (one
flag, one `if`) for anyone who wants a byte-diff.  The current state is a
documented superset, not a wrong answer; the recorded coverage-map row already
says "identical except the three keys", and the cost of the flip lands on the
one output path (TIME LIMIT runs) where the extra keys are the only information
there is.  This is a judgement call for the record owner, not mine to apply.

---

## 4. Follow-on worth registering (not done here)

The remaining `--tlimit` overshoot is entirely per-item DFS cost (§2.7).  Two
options, both semantic changes needing their own differential gate:

* **Deadline inside `min_generators`.**  Would make `--tlimit` a true bound but
  a tuple could be *partially* searched, so `best`/`hits` would no longer be
  "the answer over `scanned` tuples".  It would need a distinct flag
  (`--deadline hard`) and a new RESULT field saying a tuple was truncated;
  Python has no such mode, so it would be a Rust-only extension, not a port.
* **A cheap upper bound on DFS cost before entering it**, used to skip tuples
  whose budget makes the search hopeless.  Changes results unless provably
  sound; belongs with the kernel work, not here.

---

## 5. Files in this directory

    Cargo.toml Cargo.lock crates/            the workspace copy (only engine.rs differs)
    engine.rs.orig                            the unmodified engine.rs
    engine.diff                               the +58 -14 unified diff
    fixtures.sh                               replays r3 F1-F7, P2-P7b, S0, S123 against a given binary
    out/check_{A,B}_{1,12}.txt                the check gate, both binaries, both thread counts
    out/fx_B_t1/, out/fx_B_t12/               the 15 fixture streams from the new binary
    out/T1_{A,B}.txt, out/T3_new.txt          the abort repro and the wall-clock ladder
    target/release/kakeya-search              the new binary (sha256 0a152c93…)

## 6. Leftover processes I started (I did not signal anything)

Two of my own runs on the `--pool 4 --target 7/4` configuration of §2.7 were
still running when this was written: `--tag W` (19 min) and `--tag Z2`
(13 min, `--limit 20`, no `--tlimit`).  Both are single/two-thread and are the
per-item-cost demonstration, not a hang in the new code — `--tag Z2` has no
`--tlimit` at all.  Per the ground rules I signalled nothing.
