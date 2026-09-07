# perf lens — where kakeya-search's time goes, and the cheapest real speedup

Scout report, 2026-09-06.  **Nothing outside `rust/improve/perf/` was written.**
The audited binary (`rust/target/release/kakeya-search`,
sha256 `add554183aaa…`) and every crate under `rust/crates/` are untouched;
all prototyping happened in a COPY at
`rust/improve/perf/kperf/` (its own workspace, its own `target/`).

**Machine disclosure.**  Every wall/CPU number below was taken on a contended
6-physical-core box: pid 12158 (`ks8run`, the POOL6 8-cycle cross-check) held
~2 cores throughout and pid 13369 (the pure-Python POOL3 oracle) ~0.2.  Load
average ranged 16–56 during the session.  **User CPU seconds** are quoted
because they are the least contention-sensitive number available here; they are
still inflated by cache/SMT contention, so treat absolute seconds as soft and
*ratios measured back-to-back in the same command* as the real result.

**Kernel disclosure.**  The differential in section 5 compares the prototype
against the **pure-Python** `fastcore._force_py` (corpus generated under
`KAKEYA_PURE_PY=1`, with `assert fastcore.force is fastcore._force_py`).  It is
not a Rust-vs-Rust check.  The audited Rust `force`, copied verbatim into the
prototype workspace, was replayed against the same corpus in the same run and
also matched 27,951/27,951 — so the corpus is a live check on both.

---

## 1. Headline

| run (`--threads` as noted) | audited binary | prototype `fastcache` | factor |
|---|---|---|---|
| `scan n4_p6_t1`, threads 1 | 2.71 s user (3 reps: 2.69/2.72/2.71) | 0.58 s user (0.57/0.58/0.58) | **4.67x** |
| `cycles8 --pool 3 --patterns 8cycle`, threads 1 | 46.10 s user | 9.69 s user | **4.76x** |
| `cycles8 --pool 4 --patterns 8cycle`, threads 2 | 668.30 s user | 140.22 s user | **4.77x** |

All three produce **byte-identical stdout** to the audited binary (the POOL3 and
POOL4 cycles8 streams are `diff`-clean with no masking at all; `scan` streams
are identical after masking only `"seconds"`).  The factor does not drift with
pool size (4.76 at POOL3, 4.77 at POOL4), which is the evidence for the
extrapolation in section 7.

The speedup is entirely inside `kakeya_core::force`.  It is **not** the
"incremental elimination across the warm-start T0 growth" lever named in the
record — that lever is still unspent (section 6, lever C).

## 2. Profile: where the time goes

`/usr/bin/sample` on the audited binary, `cycles8 --pool 3 --patterns 8cycle
--threads 1`, 20 s, 15,476 samples on the working thread
(`improve/perf/prof/sample_c8.txt`):

| self time | symbol |
|---|---|
| 14,736 (95.2%) | `kakeya_core::force` |
| 196 (1.3%) | `_platform_bzero` |
| 157 (1.0%) | `_platform_memmove` |
| 104 + 71 + … (~1.5%) | malloc family |
| 66 (0.4%) | `kakeya_search::search::extend` |
| 64 (0.4%) | `kakeya_core::collect` |

This reproduces the record's earlier 20 s sample.  DFS bookkeeping and
allocation are noise; the whole question is what `force` does per call.

Counters (prototype built with `KAKEYA_STATS=1`, which instruments the same
control flow):

| workload | force calls | rounds | rounds/call | mean `nb` | mean `w` | mean `rk` | round histogram |
|---|---|---|---|---|---|---|---|
| `scan n4_p6_t1` | 247,068 | 357,514 | 1.45 | 5.66 | 6.65 | 5.36 | r1 159,109 · r2 65,617 · r3 22,197 · r4 145 |
| `cycles8 p3 pattern 2` | 896,712 | 1,477,320 | 1.65 | 10.23 | 12.69 | 9.26 | r1 464,088 · r2 303,888 · r3 111,192 · r4 15,840 · r5 1,704 |

and element-op totals for `cycles8 p3 pattern 2`:

| step | count | cost each in the audited kernel |
|---|---|---|
| step 2, build B | 223,328,064 reduces | 1 signed 64-bit `rem_euclid` |
| step 3, RREF elimination | 214,405,570 updates | 1 `(fac*b) % p` + 1 `(a+p-t) % p` = **2 divisions** |
| step 3, pivot inversion | 13,674,408 inversions | `pow(a, p-2, p)`: 31 squarings + ~30 mults, each `% p` = **~61 divisions** |
| step 4, membership | 103,820,880 column-visits | see below |

That is ≈ 3.0 billion 64-bit hardware divisions for one POOL3 pattern.
**Inversion alone is ~834 M of the ~1.05 G modular multiplications** — the
single largest item, and it was invisible in the sample because `fermat_inv` is
inlined into `force`.

One estimate in the task brief needs correcting: step 4 is **not**
O(|U|·rk·w).  The reference skips a pivot row whenever `v[c] == 0`, and the
test vector `e_{c1} - e_{c2}` has only two nonzeros whose values survive
untouched in a reduced echelon form — so at most 2 pivot rows are ever
subtracted per candidate.  Step 4 is O(|U|·2·w) already.  That is why lever B
below is worth only ~8%, not the ~1.6x a naive count suggests.

## 3. What `force` repeats that is redundant

`force(rows, n, T0, p)` (`crates/kakeya-core/src/lib.rs:88-232`) and its Python
original (`src/fastcore.py:20-84`) run a fixpoint loop.  Per round it
(1) recomputes `U` = the unforced coordinates, (2) rebuilds the whole matrix
`B` from `rows` by reducing every entry mod p again, (3) does a **full** RREF
from scratch, (4) tests every `j in U`.  Across rounds and across the
warm-started calls in `search::extend`, three things are recomputed:

* **within a call**, round k+1 rebuilds and re-reduces `B` from the same
  `rows` — the entries never change, only the column subset shrinks by 2;
* **within a call**, round k+1 redoes a full RREF of `nb` rows when the row
  space it needs is the projection of round k's already-computed row space,
  i.e. `rk` rows would do (`rk` ≤ w, and `rk` < `nb` whenever there is any
  dependency);
* **across calls**, `extend` calls `force(rows + [new_row], n, T2)` where `T2`
  is exactly the `T` the parent's *last* round ended on.  So the child's
  round-1 `U` equals the parent's final `U`, and the child re-eliminates from
  scratch a matrix of which `nb-1` rows were already reduced one call earlier.
  52% of `cycles8` calls (464,088 / 896,712) never get past round 1, so for
  those the *entire* cost of the call is this redone work.

That third item is lever C.  It is exact for prime p because the RREF of a
matrix over a field is **canonical**: it depends only on the row space, so
rebuilding it incrementally cannot change `piv`, cannot change the membership
predicate, and cannot change which `j` is found.

## 4. What the prototype actually changes (and the measured contribution of each)

Four levers, all inside `force`, none touching the DFS or the drivers.  The
prototype keeps the audited `force` byte-for-byte and adds `perf::force_fast`
beside it, selected by `KAKEYA_KERNEL`:

| `KAKEYA_KERNEL` | levers | `scan` user s | `cycles8 p3 pat2` user s |
|---|---|---|---|
| unset (audited path) | — | 2.68–2.71 | 23.13 |
| `memb` | B + D only (generic `%` arithmetic) | 2.49 | 19.73 |
| `mersenne` | A + D only | 1.05 | 8.95 |
| `fast` | A + B + D | 0.98–1.00 | 7.95 |
| `fastcache` | A + B + C' + D | **0.57–0.58** | **5.19–5.47** |

(The audited *binary* runs `scan` in 2.71 and `cycles8 p3 pat2` in 21.09; the
prototype's own unset-`KAKEYA_KERNEL` path is ~0–10% slower because of the
dispatch and a newer `rayon-core`, so it is the honest baseline for the
per-lever column.)

**A — Mersenne reduction for p = 2^31-1 (the only p any driver uses).**
`x mod (2^31-1)` by shift-and-add instead of a hardware division.  Worth
**2.55x on `scan`, 2.58x on `cycles8`** on its own.  Exact: it computes the same
residue.  Any other p keeps the division path.

**C' — memoise the pivot inverse.**  `pow(a, p-2, p)` is a pure function of `a`;
a per-worker 8192-entry direct-mapped table (in `ForceScratch`, never global, so
no cross-`p` contamination of the kind the Python `_INV` has) removes most of
the 13.7 M inversions.  Worth a further **1.7–1.9x on top of A+B+D** — the
largest single lever after A, and it is ten lines.

**B — O(w) membership test.**  In a genuine RREF the reduction coefficient of
pivot row q is the untouched original `v[piv[q]]`, and `e_{c1}-e_{c2}` has two
nonzeros, so membership reduces to "rows `q1` and `q2` agree off {c1,c2}"
(or, with one pivot, "that row *is* `e_{c1}-e_{c2}`").  Worth ~8% (2.55x → 2.73x
combined with A).  Much less than expected — see the correction in section 2.

**D — division-free add/sub.**  `(a + p - t) % p` with `a,t < p` is one
conditional subtract.  Free, applies to every p.

### The bug the differential caught (kept in the report on purpose)

Lever B is **invalid for composite p**.  `fermat_inv` is `pow(a, p-2, p)`
verbatim, which for composite p is deterministic garbage, so the pivot need not
scale to 1 and the pivot columns are not cleared — the array is not an RREF and
B's algebra does not apply.  The first prototype got 16/27,951 cases wrong, all
p=91.  The *second* attempt guarded on the FINAL pivot entries being 1 and was
still wrong on the same 16: a later elimination can restore a 1 in a pivot slot
that was never 1 when it mattered (smallest case: `p=91, n=1,
rows=[[-5,2147483649],[-2147483648,0],[0,0],[8589934592,2147483647],[2147483649,5]]`
— the echelon array ends as `[[1,0],[49,1],…]`, pivot column 0 uncleared).
The shipped guard records, at each pivot's own step, whether the scaled pivot
became exactly 1; if any did not, `force_fast` falls back to the reference
membership scan.  For prime p the guard always passes, so the drivers always
take the fast path.

## 5. Differential evidence

Corpus: `improve/perf/diff/gen_cases.py` reproduces `rust/difftest.py`'s three
generators (`run_random` incl. the warm-start chain, `run_ragged`,
`run_drivers` over `ConstructibleGraph`/`build_rows`) and records the
**pure-Python** answer for each case.  27,951 force cases, 10.7 MB, moduli
{2147483647 ×12,985; 1000000007 ×3,655; 91 ×3,885; 97 ×3,703; 7 ×3,723};
outcomes 7,844 forced / 17,749 not-forced / 2,358 exceptions.  T0 includes
empty, full, duplicated and out-of-range members; rows include ragged/short
rows, entries near ±2^40 and near ±p.

```
cd rust/improve/perf/diff
/usr/bin/python3 gen_cases.py cases_big.txt 12000 4000 5000 20260906     # 27951 cases, 138 s
cd .. && ./kperf/target/release/xdiff diff/cases_big.txt
  -> xdiff: 27951 cases | base!=py 0 | fast!=py 0 | base!=fast 0
KAKEYA_KERNEL=mersenne  ./kperf/target/release/xdiff diff/cases_big.txt   -> 0 | 0 | 0
KAKEYA_KERNEL=memb      ./kperf/target/release/xdiff diff/cases_big.txt   -> 0 | 0 | 0
KAKEYA_KERNEL=fastcache ./kperf/target/release/xdiff diff/cases_big.txt   -> 0 | 0 | 0
```

`base!=py 0` is the copied audited kernel against the same pure-Python corpus,
so the harness is not self-fulfilling.

Driver level, prototype `fastcache` vs the audited binary — `diff` clean
(only `"seconds"`/`[Ns]` masked; every HIT, HITOBJ, witness, score, tie-break
and count compared verbatim):

```
scan n4_p6_t1 (241 lines) · scan newA (2x2 pool3 max-t 2 target 2, threads 2)
scan sampled --limit 500 --seed 11 · rzero 2x2 pool6 · rzero 2x2x2 pool4
g2-tall --rows 3 --max-t 1 · stacked --pool 4 --max-t 1
cycles8 --pool 3 --patterns 4+4 · cycles8 --pool 3 --patterns 8cycle (no mask at all)
cycles8 --pool 4 --patterns 8cycle threads 2 (no mask at all, tested: 14376)
```

and `check --threads 1` is `14 PASS / 2 SKIP / 0 FAIL` under every kernel mode,
byte-identical to the audited binary's `check` output modulo `[Ns]`.

## 6. Levers not spent, with estimates

| lever | estimated further factor | cost / risk |
|---|---|---|
| **C — carry the canonical RREF across `extend` calls.**  Keep an RREF stack in `extend`; a child call's round 1 starts from the parent's final RREF (`rk` rows) plus the one new row, so step 3 costs O(w²) instead of O(nb·rk·w), and steps 2's re-reduction of `rows` disappears. | **2–3x** on top of `fastcache` (step 3 + step 2 are ~all of what is left; 52% of calls are single-round, and those are pure redone work) | Medium.  New API in `kakeya-core` (force-with-context), an RREF stack in `search::extend`, and a fallback whenever the pivot-1 guard fails (composite p).  Exactness rests on the RREF being canonical over a field — true for p = 2^31-1.  Needs its own differential gate. |
| **C-lite — carry the RREF between rounds *inside* one call** (project the previous `rk` rows onto the shrunken column set, re-RREF those instead of all `nb`). | 1.2–1.4x | Small, local to `force`, same canonicity argument.  Only helps the 39% of rounds that are not round 1. |
| **Pre-reduce `rows` once per call** (round 1's column set is a superset of every later round's, so the error ordering is preserved). | ~1.05x after A | Small; folded into C-lite. |
| **Thread scaling.**  Not a kernel issue: the record's `scan n4_p6_t1` bench is 1.18 s at 1 thread → 0.16 s at 12 (7.4x on 6 physical cores), i.e. already near-linear.  Nothing to win. | 1.0x | — |
| **Chunk size (`engine.rs:213-220`, `total/4096`).**  Not a throughput lever, but it is the cause of the OPEN `--tlimit` allocation abort; streaming chunk enumeration would fix that and remove an O(index-space) up-front cost that also makes `--tlimit` not a wall-clock bound. | 1.0x throughput, fixes a known bug | Small–medium. |
| **Allocation.**  `collect()` allocates a fresh `Vec<i64>` per force call (52 of 15,476 samples in malloc under it) and `sc.bmat.resize(rows.len()*w, 0)` bzeros the whole scratch every round (196 samples).  Returning `T` into a caller-owned buffer, and zeroing only the `nb*w` prefix actually written, is worth maybe 2–3%. | 1.02–1.03x | Small, but it changes `force`'s signature. |
| **The `deg` filter / pruning.**  Untouched here: this lens measured the kernel, and the kernel is 95% of the time, so a pruning change is a *different* kind of win (fewer pairs, not cheaper pairs) and needs the mathematician's sign-off, not a profiler's. | n/a | n/a |

## 7. What this buys the campaign (estimate, not a measurement)

The record's target run is `cycles8 --pool 6 --patterns 8cycle` — 81,660 pairs.
It ran to completion **during this session** on the audited binary (pid 12158,
`./target/release/ks8run cycles8 --pool 6 --target 67/40 --deg 2 --patterns
8cycle --threads 10 --tlimit 36000`): started ~15:02, finished 16:46, so
**~6,240 s wall on 10 threads**, i.e. ~13.1 pairs/s, not the ~5 h the 4.6
pairs/s figure predicted.  Its log
(`arithmetic-kakeya/logs/rust-cycles8_8cycle.log`, 8 lines) ends
`RESULT {"tag": "cycles8", "pool": 6, "best": null, "hits": 0, "tested": 81660,
"patterns": [2, 3]}` — a clean exit, not a kill.  (Recorded here only because
the orchestrator flagged that job as top priority; this lens did not touch it,
and issued no kill/pkill/signal of any kind.)

Against that real baseline: the kernel factor measured here is flat across pool
size (4.76 at POOL3, 4.77 at POOL4) and `force` is 95% of the run, so Amdahl
puts the whole-run factor at ~4.3x — **≈ 24 minutes instead of ≈ 104**, same
output byte-for-byte.  With lever C on top the same run would plausibly land
near 10 minutes.  This is still an extrapolation: the 4.77x was not measured at
POOL6, and POOL6 pairs have a different `nb`/`w` mix (POOL6 8-cycle patterns
carry 1,296 labels each vs 81 at POOL3).

## 8. Files (all under `rust/improve/perf/`)

```
REPORT.md                      this file
kperf/                         copy of the workspace (kakeya-core + kakeya-search only)
  crates/kakeya-core/src/lib.rs         the audited crate verbatim PLUS one unused ForceScratch field (`invc: Vec<u64>`, with its doc comment, lines 78-79) and WITH `#[cfg(test)] mod tests;` removed -- NOT "lines 1-368 byte-identical" as this line first said (adjudication FINDING-05 diffed it: 78,79d77 and 368a367,368)
                                        (verified by diff); the `perf` module is appended
  crates/kakeya-core/src/bin/xdiff.rs   corpus replay: audited force + prototype vs pure Python
  crates/kakeya-search/src/search.rs    one line changed: force -> kakeya_core::perf::force_sel
  crates/kakeya-search/src/main.rs      prints STATS on exit when KAKEYA_STATS=1
diff/gen_cases.py              pure-Python corpus generator (KAKEYA_PURE_PY=1 enforced)
diff/cases_big.txt             27,951 cases + pure-Python expected answers (10.7 MB)
diff/cases_smoke.txt           522-case smoke corpus
prof/sample_c8.txt             the 20 s `sample` of the audited binary
prof/lever.txt prof/lever8.txt prof/lever_cache.txt prof/final_scan.txt   timing logs
prof/c8_ship.txt prof/c8_fc.txt prof/c8p4_ship.txt prof/c8p4_fc.txt       byte-compared stdout
```

Reproduce end to end:

```
cd rust/improve/perf/kperf && cargo build --release            # ~80 s
cd ../diff && /usr/bin/python3 gen_cases.py cases_big.txt 12000 4000 5000 20260906
cd .. && KAKEYA_KERNEL=fastcache ./kperf/target/release/xdiff diff/cases_big.txt
cd ../..                                                        # rust/
( /usr/bin/time -p ./target/release/kakeya-search cycles8 --pool 3 --target 67/40 \
    --deg 2 --patterns 8cycle --threads 1 > /tmp/a.txt ) 2>&1
( KAKEYA_KERNEL=fastcache /usr/bin/time -p \
  ./improve/perf/kperf/target/release/kakeya-search cycles8 --pool 3 --target 67/40 \
    --deg 2 --patterns 8cycle --threads 1 > /tmp/b.txt ) 2>&1
diff /tmp/a.txt /tmp/b.txt
```

## 9. Recommendation

Port levers A, C' and D (Mersenne reduction, the pivot-inverse memo, the
division-free add/sub) into `kakeya-core::force` behind the existing test
gates.  They are ~120 lines, need no API change, no change to `search.rs` or any
driver, are exact for every p, and are worth **4.3–4.8x** measured on three
different workloads with byte-identical output.  Lever B (the O(w) membership
test) is only ~8% and carries the composite-p subtlety that already produced one
wrong prototype — take it only with the pivot-time guard, or leave it out.
Lever C is the one worth a separate, properly gated task.


---
**Corrections appended 2026-09-06 late evening (adjudication FINDING-05, which upheld the 4.7x result and the differential -- and regenerated an independent 7,990-case corpus at seed 771131 incl. 1,068 cases at composite p = 91: 0 mismatches in all five kernel modes).** (1) Section 8's provenance line is corrected in place above. (2) The claim "no API change, no change to search.rs or any driver" holds only for the RECOMMENDED port (levers A + C' + D); the prototype as built reroutes `search.rs:9` to `kakeya_core::perf::force_sel` and touches `main.rs`. (3) `rzero` is struck from the diff-clean evidence list: `drivers/rzero.rs` was never rerouted, so its diff-clean is vacuous and rzero gets 0x from this prototype; only the DFS `extend` path (`search.rs:142`) goes through `force_sel`. Severity of the improvement card: major, not critical.
